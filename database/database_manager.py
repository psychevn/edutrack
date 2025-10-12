import sqlite3
import hashlib
from datetime import datetime
import os
import sys
from typing import Optional, Dict, List, Tuple
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store database in user's AppData folder for persistence
            if sys.platform == 'win32':
                app_data = os.getenv('APPDATA')
                db_dir = os.path.join(app_data, 'EDUTRACK')
            else:
                db_dir = os.path.expanduser('~/.edutrack')
            
            # Create directory if it doesn't exist
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, 'assessment_system.db')
        else:
            self.db_path = db_path
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def initialize_database(self):
        """Initialize the database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if we need to migrate the database schema
        self.migrate_database(cursor)
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
                full_name TEXT NOT NULL,
                email TEXT UNIQUE,
                admin_id_number TEXT UNIQUE,
                student_number TEXT UNIQUE,
                section TEXT,
                security_question TEXT NOT NULL,
                security_answer_hash TEXT NOT NULL,
                profile_photo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                post_type TEXT NOT NULL CHECK(post_type IN ('assessment', 'file')),
                created_by INTEGER NOT NULL,
                assessment_id INTEGER,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id),
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        ''')

        # Post sections (assignment) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_sections (
                post_id INTEGER NOT NULL,
                section TEXT NOT NULL,
                PRIMARY KEY (post_id, section),
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')

        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                post_type TEXT DEFAULT 'post',
                parent_comment_id INTEGER DEFAULT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (parent_comment_id) REFERENCES comments (id)
            )
        ''')
        
        # Add missing columns to existing comments table if they don't exist
        try:
            cursor.execute('ALTER TABLE comments ADD COLUMN post_type TEXT DEFAULT "post"')
        except:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE comments ADD COLUMN parent_comment_id INTEGER DEFAULT NULL')
        except:
            pass  # Column already exists

        # File submissions table (for student turn-ins on file posts)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (student_id) REFERENCES users (id)
            )
        ''')

        # Assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes INTEGER NOT NULL,
                status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'active', 'closed')),
                enforce_per_question_time BOOLEAN DEFAULT 0,
                per_question_duration_seconds INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL CHECK(question_type IN ('mcq', 'short_answer')),
                points INTEGER DEFAULT 1,
                correct_answer TEXT,
                options TEXT, -- JSON string for MCQ options
                order_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id)
            )
        ''')
        
        # Submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_graded BOOLEAN DEFAULT 0,
                total_score REAL DEFAULT 0,
                max_score REAL DEFAULT 0,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id),
                FOREIGN KEY (student_id) REFERENCES users (id),
                UNIQUE(assessment_id, student_id)
            )
        ''')
        
        # Answers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                is_correct BOOLEAN,
                points_earned REAL DEFAULT 0,
                feedback TEXT,
                FOREIGN KEY (submission_id) REFERENCES submissions (id),
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        ''')
        
        # Security questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Answer responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answer_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                selected_option TEXT,
                is_correct BOOLEAN,
                points_earned REAL DEFAULT 0,
                feedback TEXT,
                FOREIGN KEY (submission_id) REFERENCES submissions (id),
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        ''')
        
        # Announcements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                target_sections TEXT,  -- JSON array of sections, NULL for all students
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize security questions
        self.initialize_security_questions()
        
        # Create default admin user if not exists
        self.create_default_admin()
    
    def migrate_database(self, cursor):
        """Migrate existing database to new schema"""
        try:
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add new columns if they don't exist
            if 'admin_id_number' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN admin_id_number TEXT UNIQUE')
            
            if 'student_number' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN student_number TEXT UNIQUE')
            
            if 'section' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN section TEXT')
            
            if 'security_question' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN security_question TEXT NOT NULL DEFAULT "What is your favorite teacher\'s name?"')
            
            if 'security_answer_hash' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN security_answer_hash TEXT NOT NULL DEFAULT "default_hash"')
            
            if 'profile_photo' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN profile_photo TEXT')
            
            # Update existing users with default security question and answer
            cursor.execute('''
                UPDATE users 
                SET security_question = "What is your favorite teacher's name?",
                    security_answer_hash = ?
                WHERE security_answer_hash = "default_hash"
            ''', (self.hash_password("default"),))
            
            # Check if assessments table needs status column
            cursor.execute("PRAGMA table_info(assessments)")
            assessment_columns = [column[1] for column in cursor.fetchall()]
            
            if 'status' not in assessment_columns:
                cursor.execute('ALTER TABLE assessments ADD COLUMN status TEXT DEFAULT "draft" CHECK(status IN ("draft", "published", "active", "closed"))')
                # Update existing assessments to have published status if they're active
                cursor.execute('UPDATE assessments SET status = "published" WHERE is_active = 1')
            else:
                # Ensure existing assessments have proper status values
                cursor.execute('UPDATE assessments SET status = "published" WHERE status IS NULL AND is_active = 1')
                cursor.execute('UPDATE assessments SET status = "draft" WHERE status IS NULL AND is_active = 0')
                cursor.execute('UPDATE assessments SET status = "draft" WHERE status = ""')

            # Add per-question timing columns if not exist
            if 'enforce_per_question_time' not in assessment_columns:
                cursor.execute('ALTER TABLE assessments ADD COLUMN enforce_per_question_time BOOLEAN DEFAULT 0')
            if 'per_question_duration_seconds' not in assessment_columns:
                cursor.execute('ALTER TABLE assessments ADD COLUMN per_question_duration_seconds INTEGER')
            
            # Check if submissions table needs additional columns
            cursor.execute("PRAGMA table_info(submissions)")
            submission_columns = [column[1] for column in cursor.fetchall()]
            
            if 'score' not in submission_columns:
                cursor.execute('ALTER TABLE submissions ADD COLUMN score REAL DEFAULT 0')
            if 'total_questions' not in submission_columns:
                cursor.execute('ALTER TABLE submissions ADD COLUMN total_questions INTEGER DEFAULT 0')

            # Ensure new tables exist (idempotent)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    post_type TEXT NOT NULL CHECK(post_type IN ('assessment', 'file')),
                    created_by INTEGER NOT NULL,
                    assessment_id INTEGER,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id),
                    FOREIGN KEY (assessment_id) REFERENCES assessments (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_sections (
                    post_id INTEGER NOT NULL,
                    section TEXT NOT NULL,
                    PRIMARY KEY (post_id, section),
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    post_type TEXT DEFAULT 'post',
                    parent_comment_id INTEGER DEFAULT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (parent_comment_id) REFERENCES comments (id)
                )
            ''')
            
            # Add missing columns to existing comments table if they don't exist
            try:
                cursor.execute('ALTER TABLE comments ADD COLUMN post_type TEXT DEFAULT "post"')
            except:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE comments ADD COLUMN parent_comment_id INTEGER DEFAULT NULL')
            except:
                pass  # Column already exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (id),
                    FOREIGN KEY (student_id) REFERENCES users (id)
                )
            ''')
            
        except Exception as e:
            print(f"Migration error: {e}")

    def fix_assessment_status_values(self) -> None:
        """Ensure assessments have a valid non-empty status string. Safe no-op if already valid."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE assessments SET status = 'draft' WHERE status IS NULL OR TRIM(status) = ''")
            conn.commit()
        except Exception as ex:
            print(f"fix_assessment_status_values error: {ex}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def initialize_security_questions(self):
        """Initialize predefined security questions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        security_questions = [
            "What is your favorite teacher's name?",
            "What is your pet's name?",
            "What is the name of your first school?",
            "What is your favorite subject?",
            "What is your mother's maiden name?"
        ]
        
        for question in security_questions:
            cursor.execute('''
                INSERT OR IGNORE INTO security_questions (question_text)
                VALUES (?)
            ''', (question,))
        
        conn.commit()
        conn.close()
    
    def create_default_admin(self):
        """Create a default admin user if none exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Create default admin user
            password_hash = self.hash_password("admin123")
            security_answer_hash = self.hash_password("admin")
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, email, admin_id_number, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ("admin", password_hash, "admin", "System Administrator", "admin@system.com", "ADMIN001", "What is your favorite teacher's name?", security_answer_hash))
            
            # Create a sample student
            student_password = self.hash_password("student123")
            student_security_answer_hash = self.hash_password("student")
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, email, student_number, section, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ("student", student_password, "student", "Test Student", "student@test.com", "STU001", "1A", "What is your favorite teacher's name?", student_security_answer_hash))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def get_security_questions(self) -> List[str]:
        """Get all available security questions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT question_text FROM security_questions ORDER BY id')
        results = cursor.fetchall()
        conn.close()
        
        return [result[0] for result in results]
    
    def create_admin_account(self, admin_id_number: str, name: str, username: str, 
                           password: str, email: str, security_question: str, 
                           security_answer: str, profile_photo: str = None) -> bool:
        """Create a new admin account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if username or email already exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone()[0] > 0:
                return False
            
            # Check if admin ID already exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE admin_id_number = ?', (admin_id_number,))
            if cursor.fetchone()[0] > 0:
                return False
            
            password_hash = self.hash_password(password)
            security_answer_hash = self.hash_password(security_answer.lower().strip())
            
            cursor.execute('''
                INSERT INTO users (admin_id_number, full_name, username, password_hash, email, role, security_question, security_answer_hash, profile_photo)
                VALUES (?, ?, ?, ?, ?, 'admin', ?, ?, ?)
            ''', (admin_id_number, name, username, password_hash, email, security_question, security_answer_hash, profile_photo))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating admin account: {e}")
            return False
        finally:
            conn.close()
    
    def create_student_account(self, student_number: str, name: str, section: str, 
                             username: str, password: str, email: str, 
                             security_question: str, security_answer: str, profile_photo: str = None) -> bool:
        """Create a new student account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if username or email already exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone()[0] > 0:
                return False
            
            # Check if student number already exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE student_number = ?', (student_number,))
            if cursor.fetchone()[0] > 0:
                return False
            
            password_hash = self.hash_password(password)
            security_answer_hash = self.hash_password(security_answer.lower().strip())
            
            cursor.execute('''
                INSERT INTO users (student_number, full_name, section, username, password_hash, email, role, security_question, security_answer_hash, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, 'student', ?, ?, ?)
            ''', (student_number, name, section, username, password_hash, email, security_question, security_answer_hash, profile_photo))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating student account: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_by_username_or_email(self, identifier: str) -> Optional[Dict]:
        """Get user by username or email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, full_name, email, security_question
            FROM users
            WHERE username = ? OR email = ?
        ''', (identifier, identifier))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_data = {
                'id': result[0],
                'username': result[1],
                'role': result[2],
                'full_name': result[3],
                'email': result[4],
                'security_question': result[5]
            }
            return user_data
        return None
    
    def list_all_users(self):
        """Debug method to list all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, full_name
            FROM users
        ''')
        
        results = cursor.fetchall()
        print("All users in database:")
        for result in results:
            print(f"  ID: {result[0]}, Username: '{result[1]}', Email: '{result[2]}', Role: {result[3]}, Name: {result[4]}")
        
        conn.close()
        return results
    
    def verify_security_answer(self, user_id: int, security_answer: str) -> bool:
        """Verify security answer for password recovery"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT security_answer_hash FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_hash = result[0]
            provided_hash = self.hash_password(security_answer.lower().strip())
            return stored_hash == provided_hash
        return False
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(new_password)
            cursor.execute('''
                UPDATE users SET password_hash = ? WHERE id = ?
            ''', (password_hash, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if successful"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username, role, full_name, email, admin_id_number, student_number, section, profile_photo
            FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'role': result[2],
                'full_name': result[3],
                'email': result[4],
                'admin_id_number': result[5],
                'student_number': result[6],
                'section': result[7],
                'profile_photo': result[8]
            }
        return None
    
    def create_assessment(self, title: str, description: str, created_by: int, 
                         start_time: str, end_time: str, duration_minutes: int, status: str = 'draft',
                         enforce_per_question_time: int = 0, per_question_duration_seconds: Optional[int] = None) -> int:
        """Create a new assessment and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assessments (title, description, created_by, start_time, end_time, duration_minutes, status, enforce_per_question_time, per_question_duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, created_by, start_time, end_time, duration_minutes, status, enforce_per_question_time, per_question_duration_seconds))
        
        assessment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return assessment_id
    
    def add_question(self, assessment_id: int, question_text: str, question_type: str,
                    points: int, correct_answer: str, options: str = None, order_index: int = 0) -> int:
        """Add a question to an assessment and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO questions (assessment_id, question_text, question_type, points, correct_answer, options, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (assessment_id, question_text, question_type, points, correct_answer, options, order_index))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return question_id
    
    def get_assessments(self, user_id: int = None, role: str = None) -> List[Dict]:
        """Get assessments based on user role and ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if role == 'admin':
            cursor.execute('''
                SELECT a.id, a.title, a.description, a.created_by, a.start_time, a.end_time, 
                       a.duration_minutes, a.status, a.is_active, a.created_at, u.full_name as creator_name
                FROM assessments a
                JOIN users u ON a.created_by = u.id
                ORDER BY a.created_at DESC
            ''')
        else:  # student
            cursor.execute('''
                SELECT a.id, a.title, a.description, a.created_by, a.start_time, a.end_time, 
                       a.duration_minutes, a.status, a.is_active, a.created_at, u.full_name as creator_name,
                       CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END as is_submitted
                FROM assessments a
                JOIN users u ON a.created_by = u.id
                LEFT JOIN submissions s ON a.id = s.assessment_id AND s.student_id = ?
                WHERE a.is_active = 1
                ORDER BY a.created_at DESC
            ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        assessments = []
        for result in results:
            if role == 'admin':
                assessments.append({
                    'id': result[0],
                    'title': result[1],
                    'description': result[2],
                    'created_by': result[3],
                    'start_time': result[4],
                    'end_time': result[5],
                    'duration_minutes': result[6],
                    'status': result[7],  # Now correctly mapped to status column
                    'is_active': result[8],
                    'created_at': result[9],
                    'creator_name': result[10]
                })
            else:
                assessments.append({
                    'id': result[0],
                    'title': result[1],
                    'description': result[2],
                    'created_by': result[3],
                    'start_time': result[4],
                    'end_time': result[5],
                    'duration_minutes': result[6],
                    'status': result[7],
                    'is_active': result[8],
                    'created_at': result[9],
                    'creator_name': result[10],
                    'is_submitted': result[11]
                })
        
        return assessments
    
    def get_questions(self, assessment_id: int) -> List[Dict]:
        """Get all questions for an assessment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question_text, question_type, points, correct_answer, options, order_index
            FROM questions
            WHERE assessment_id = ?
            ORDER BY order_index
        ''', (assessment_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        questions = []
        for result in results:
            questions.append({
                'id': result[0],
                'question_text': result[1],
                'question_type': result[2],
                'points': result[3],
                'correct_answer': result[4],
                'options': result[5],
                'order_index': result[6]
            })
        
        return questions

    def get_assessment_by_id(self, assessment_id: int) -> Optional[Dict]:
        """Get a single assessment by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, a.title, a.description, a.created_by, a.start_time, a.end_time,
                   a.duration_minutes, a.status, a.is_active, a.created_at, u.full_name as creator_name
            FROM assessments a
            JOIN users u ON a.created_by = u.id
            WHERE a.id = ?
        ''', (assessment_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'created_by': row[3],
            'start_time': row[4],
            'end_time': row[5],
            'duration_minutes': row[6],
            'status': row[7],
            'is_active': row[8],
            'created_at': row[9],
            'creator_name': row[10],
        }

    def update_assessment(self, assessment_id: int, *, title: str, description: str,
                          start_time: Optional[str], end_time: Optional[str],
                          duration_minutes: int, status: str) -> None:
        """Update core fields of an assessment."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assessments
            SET title = ?, description = ?, start_time = ?, end_time = ?, duration_minutes = ?, status = ?
            WHERE id = ?
        ''', (title, description, start_time, end_time, duration_minutes, status, assessment_id))
        conn.commit()
        conn.close()
    
    def submit_assessment(self, assessment_id: int, student_id: int, answers: List[Dict]) -> int:
        """Submit an assessment and return submission ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create submission record
        cursor.execute('''
            INSERT OR REPLACE INTO submissions (assessment_id, student_id, submitted_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (assessment_id, student_id))
        
        submission_id = cursor.lastrowid
        
        # Insert answers
        total_score = 0
        max_score = 0
        
        for answer in answers:
            question_id = answer['question_id']
            answer_text = answer['answer_text']
            
            # Get question details
            cursor.execute('''
                SELECT question_type, correct_answer, points
                FROM questions
                WHERE id = ?
            ''', (question_id,))
            
            question_data = cursor.fetchone()
            if question_data:
                question_type, correct_answer, points = question_data
                max_score += points
                
                # Check if answer is correct
                is_correct = False
                points_earned = 0
                
                if question_type == 'mcq' and answer_text == correct_answer:
                    is_correct = True
                    points_earned = points
                elif question_type == 'short_answer':
                    # For short answers, we'll mark as needing manual review
                    points_earned = 0
                
                total_score += points_earned
                
                cursor.execute('''
                    INSERT INTO answers (submission_id, question_id, answer_text, is_correct, points_earned)
                    VALUES (?, ?, ?, ?, ?)
                ''', (submission_id, question_id, answer_text, is_correct, points_earned))
        
        # Update submission with total score
        cursor.execute('''
            UPDATE submissions
            SET total_score = ?, max_score = ?, is_graded = 1
            WHERE id = ?
        ''', (total_score, max_score, submission_id))
        
        conn.commit()
        conn.close()
        
        return submission_id

    # ------------------------- Posts API -------------------------
    def create_post(self, title: str, description: str, post_type: str, created_by: int,
                    assessment_id: Optional[int] = None, file_path: Optional[str] = None) -> int:
        """Create a new post (assessment or file) and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (title, description, post_type, created_by, assessment_id, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, post_type, created_by, assessment_id, file_path))
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return post_id

    def get_available_sections(self) -> List[str]:
        """Get list of available sections from users table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT section FROM users WHERE section IS NOT NULL ORDER BY section')
        results = cursor.fetchall()
        conn.close()
        
        sections = [result[0] for result in results if result[0]]
        # If no sections found, return default sections
        if not sections:
            return ["1A", "2A", "3A", "4A", "1B", "2B", "3B", "4B"]
        return sections

    def assign_post_sections(self, post_id: int, sections: List[str]) -> None:
        """Assign a post to one or more sections"""
        conn = self.get_connection()
        cursor = conn.cursor()
        for section in sections:
            cursor.execute('''
                INSERT OR IGNORE INTO post_sections (post_id, section) VALUES (?, ?)
            ''', (post_id, section))
        conn.commit()
        conn.close()

    def get_posts_for_student_section(self, student_id: int) -> List[Dict]:
        """Return posts assigned to the student's section, newest first"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Get student section
        cursor.execute('SELECT section FROM users WHERE id = ?', (student_id,))
        row = cursor.fetchone()
        student_section = row[0] if row else None
        if not student_section:
            conn.close()
            return []
        cursor.execute('''
            SELECT p.id, p.title, p.description, p.post_type, p.created_by, p.assessment_id, p.file_path, p.created_at,
                   u.full_name as author_name
            FROM posts p
            JOIN post_sections ps ON ps.post_id = p.id AND ps.section = ?
            JOIN users u ON u.id = p.created_by
            ORDER BY p.created_at DESC
        ''', (student_section,))
        results = cursor.fetchall()
        conn.close()
        posts: List[Dict] = []
        for r in results:
            posts.append({
                'id': r[0],
                'title': r[1],
                'description': r[2],
                'post_type': r[3],
                'created_by': r[4],
                'assessment_id': r[5],
                'file_path': r[6],
                'created_at': r[7],
                'author_name': r[8]
            })
        return posts

    # ------------------------- Admin Stats -------------------------
    def get_admin_dashboard_stats(self, admin_user_id: int) -> Dict:
        """Compute admin dashboard KPIs for a specific admin (only their assessments/posts):
        - total_students: students assigned to any of this admin's assessment posts
        - active_assessments: this admin's published/active assessments
        - completion_rate: percent of assigned student-assessment pairs submitted for this admin
        - new_submissions: distinct submissions for this admin in the last 24 hours
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Total assigned students (students who have at least one assessment assigned via this admin's posts)
            cursor.execute(
                '''
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                JOIN post_sections ps ON ps.section = u.section
                JOIN posts p ON p.id = ps.post_id AND p.post_type = 'assessment' AND p.assessment_id IS NOT NULL AND p.created_by = ?
                WHERE u.role = 'student'
                '''
            , (admin_user_id,))
            total_students = cursor.fetchone()[0] or 0

            # Active / published assessments
            cursor.execute("SELECT COUNT(*) FROM assessments WHERE status IN ('published','active') AND is_active = 1 AND created_by = ?", (admin_user_id,))
            active_assessments = cursor.fetchone()[0] or 0

            # New submissions in last 24 hours (distinct student-assessment pairs)
            # Only count if the submission is from a student and the assessment was assigned to that student's section via posts
            cursor.execute(
                '''
                SELECT COUNT(DISTINCT (s.assessment_id || '-' || s.student_id))
                FROM submissions s
                JOIN users u ON u.id = s.student_id AND u.role = 'student'
                JOIN posts p ON p.assessment_id = s.assessment_id AND p.post_type = 'assessment' AND p.created_by = ?
                JOIN post_sections ps ON ps.post_id = p.id
                WHERE u.section = ps.section
                  AND s.submitted_at >= datetime('now','-1 day')
                '''
            , (admin_user_id,))
            new_submissions = cursor.fetchone()[0] or 0

            # Total targets = number of student-assessment pairs assigned via posts/post_sections
            cursor.execute(
                '''
                SELECT COUNT(DISTINCT (p.assessment_id || '-' || u.id))
                FROM posts p
                JOIN post_sections ps ON ps.post_id = p.id
                JOIN users u ON u.section = ps.section AND u.role = 'student'
                WHERE p.post_type = 'assessment' AND p.assessment_id IS NOT NULL AND p.created_by = ?
                '''
            , (admin_user_id,))
            total_targets = cursor.fetchone()[0] or 0

            # Submissions count as distinct student-assessment pairs for this admin only
            cursor.execute(
                '''
                SELECT COUNT(DISTINCT (s.assessment_id || '-' || s.student_id))
                FROM submissions s
                JOIN posts p ON p.assessment_id = s.assessment_id AND p.post_type = 'assessment' AND p.created_by = ?
                JOIN post_sections ps ON ps.post_id = p.id
                JOIN users u ON u.id = s.student_id AND u.section = ps.section
                '''
            , (admin_user_id,))
            submitted_pairs = cursor.fetchone()[0] or 0

            completion_rate = 0
            if total_targets > 0:
                completion_rate = int(round((submitted_pairs / total_targets) * 100))

            return {
                'total_students': total_students,
                'active_assessments': active_assessments,
                'completion_rate': completion_rate,
                'new_submissions': new_submissions,
            }
        finally:
            conn.close()

    # ------------------------- Comments API -------------------------
    def add_comment(self, post_id: int, user_id: int, content: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)
        ''', (post_id, user_id, content))
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return comment_id

    def get_comments(self, post_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.post_id, c.user_id, u.full_name, c.content, c.created_at
            FROM comments c
            JOIN users u ON u.id = c.user_id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        ''', (post_id,))
        results = cursor.fetchall()
        conn.close()
        return [
            {
                'id': r[0],
                'post_id': r[1],
                'user_id': r[2],
                'user_name': r[3],
                'content': r[4],
                'created_at': r[5],
            }
            for r in results
        ]

    def get_announcement_comments(self, announcement_id: int) -> List[Dict]:
        """Get comments for an announcement with user details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First, check if the new columns exist
            cursor.execute("PRAGMA table_info(comments)")
            columns = [column[1] for column in cursor.fetchall()]
            
            has_post_type = 'post_type' in columns
            has_parent_comment = 'parent_comment_id' in columns
            
            # Build query based on available columns
            if has_post_type and has_parent_comment:
                query = '''
                    SELECT c.id, c.content, c.created_at, u.full_name as user_name, u.id as user_id,
                           u.profile_photo, c.parent_comment_id
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.post_id = ? AND c.post_type = 'announcement'
                    ORDER BY c.created_at ASC
                '''
            elif has_parent_comment:
                query = '''
                    SELECT c.id, c.content, c.created_at, u.full_name as user_name, u.id as user_id,
                           u.profile_photo, c.parent_comment_id
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.post_id = ?
                    ORDER BY c.created_at ASC
                '''
            else:
                # Fallback for old schema
                query = '''
                    SELECT c.id, c.content, c.created_at, u.full_name as user_name, u.id as user_id,
                           u.profile_photo, NULL as parent_comment_id
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.post_id = ?
                    ORDER BY c.created_at ASC
                '''
            
            cursor.execute(query, (announcement_id,))
            
            comments = []
            for row in cursor.fetchall():
                comments.append({
                    'id': row[0],
                    'content': row[1],
                    'created_at': row[2],
                    'user_name': row[3],
                    'user_id': row[4],
                    'profile_photo': row[5],
                    'parent_comment_id': row[6] if len(row) > 6 else None
                })
            
            return comments
            
        except Exception as e:
            print(f"Error getting announcement comments: {e}")
            return []
        finally:
            conn.close()
    
    def add_announcement_comment(self, announcement_id: int, user_id: int, content: str, parent_comment_id: int = None) -> int:
        """Add comment for an announcement with optional reply support"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if the new columns exist
            cursor.execute("PRAGMA table_info(comments)")
            columns = [column[1] for column in cursor.fetchall()]
            
            has_post_type = 'post_type' in columns
            has_parent_comment = 'parent_comment_id' in columns
            
            # Build insert query based on available columns
            if has_post_type and has_parent_comment:
                cursor.execute('''
                    INSERT INTO comments (post_id, post_type, user_id, content, parent_comment_id, created_at)
                    VALUES (?, 'announcement', ?, ?, ?, datetime('now'))
                ''', (announcement_id, user_id, content, parent_comment_id))
            elif has_parent_comment:
                cursor.execute('''
                    INSERT INTO comments (post_id, user_id, content, parent_comment_id, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', (announcement_id, user_id, content, parent_comment_id))
            else:
                # Fallback for old schema
                cursor.execute('''
                    INSERT INTO comments (post_id, user_id, content, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (announcement_id, user_id, content))
            
            comment_id = cursor.lastrowid
            conn.commit()
            return comment_id
            
        except Exception as e:
            print(f"Error adding announcement comment: {e}")
            return 0
        finally:
            conn.close()

    # ------------------------- File submissions API -------------------------
    def create_file_submission(self, post_id: int, student_id: int, file_path: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO file_submissions (post_id, student_id, file_path) VALUES (?, ?, ?)
        ''', (post_id, student_id, file_path))
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return submission_id

    def get_file_submissions(self, post_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fs.id, fs.post_id, fs.student_id, u.full_name, fs.file_path, fs.submitted_at
            FROM file_submissions fs
            JOIN users u ON u.id = fs.student_id
            WHERE fs.post_id = ?
            ORDER BY fs.submitted_at DESC
        ''', (post_id,))
        results = cursor.fetchall()
        conn.close()
        return [
            {
                'id': r[0],
                'post_id': r[1],
                'student_id': r[2],
                'student_name': r[3],
                'file_path': r[4],
                'submitted_at': r[5],
            }
            for r in results
        ]

    # ------------------------- Scoring/Grading API -------------------------
    def get_published_assessments_with_stats(self) -> List[Dict]:
        """Get all published assessments with student submission statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.title, a.description, a.created_at, a.start_time, a.end_time,
                   COUNT(DISTINCT q.id) as total_questions,
                   COALESCE(SUM(q.points), 0) as total_points,
                   COUNT(DISTINCT s.student_id) as students_taken
            FROM assessments a
            LEFT JOIN questions q ON a.id = q.assessment_id
            LEFT JOIN submissions s ON a.id = s.assessment_id
            WHERE a.status IN ('published', 'done')
            GROUP BY a.id, a.title, a.description, a.created_at, a.start_time, a.end_time
            ORDER BY a.created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        assessments = []
        for result in results:
            assessments.append({
                'id': result[0],
                'title': result[1],
                'description': result[2],
                'created_at': result[3],
                'start_time': result[4],
                'end_time': result[5],
                'total_questions': result[6],
                'total_points': result[7],
                'students_taken': result[8]
            })
        
        return assessments

    def get_assessment_submissions(self, assessment_id: int) -> List[Dict]:
        """Get all student submissions for a specific assessment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, s.student_id, u.student_number, u.full_name, s.submitted_at,
                   s.is_graded, s.total_score, s.max_score
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            WHERE s.assessment_id = ?
            ORDER BY u.full_name
        ''', (assessment_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        submissions = []
        for result in results:
            submissions.append({
                'submission_id': result[0],
                'student_id': result[1],
                'student_number': result[2],
                'student_name': result[3],
                'submitted_at': result[4],
                'is_graded': bool(result[5]),
                'total_score': result[6] or 0,
                'max_score': result[7] or 0
            })
        
        return submissions

    def get_student_submission(self, student_id: int, assessment_id: int) -> Dict:
        """Get student's submission for a specific assessment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, assessment_id, student_id, submitted_at, total_score, max_score, is_graded
                FROM submissions 
                WHERE student_id = ? AND assessment_id = ?
                ORDER BY submitted_at DESC
                LIMIT 1
            ''', (student_id, assessment_id))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'assessment_id': result[1],
                    'student_id': result[2],
                    'submitted_at': result[3],
                    'total_score': result[4],
                    'max_score': result[5],
                    'is_graded': bool(result[6])
                }
            return None
        finally:
            conn.close()

    def get_submission_details(self, submission_id: int) -> Dict:
        """Get detailed submission information including all answers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get submission info
        cursor.execute('''
            SELECT s.id, s.assessment_id, s.student_id, u.student_number, u.full_name,
                   s.submitted_at, s.is_graded, s.total_score, s.max_score, a.title
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            JOIN assessments a ON s.assessment_id = a.id
            WHERE s.id = ?
        ''', (submission_id,))
        
        submission_result = cursor.fetchone()
        if not submission_result:
            conn.close()
            return None
        
        # Get all answers with question details
        cursor.execute('''
            SELECT a.id, a.question_id, q.question_text, q.question_type, q.points,
                   q.correct_answer, q.options, a.answer_text, a.is_correct,
                   a.points_earned, a.feedback
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.submission_id = ?
            ORDER BY q.order_index
        ''', (submission_id,))
        
        answers_results = cursor.fetchall()
        conn.close()
        
        answers = []
        for answer_result in answers_results:
            answers.append({
                'answer_id': answer_result[0],
                'question_id': answer_result[1],
                'question_text': answer_result[2],
                'question_type': answer_result[3],
                'points': answer_result[4],
                'correct_answer': answer_result[5],
                'options': answer_result[6],
                'student_answer': answer_result[7],
                'is_correct': bool(answer_result[8]) if answer_result[8] is not None else None,
                'points_earned': answer_result[9] or 0,
                'feedback': answer_result[10]
            })
        
        return {
            'submission_id': submission_result[0],
            'assessment_id': submission_result[1],
            'student_id': submission_result[2],
            'student_number': submission_result[3],
            'student_name': submission_result[4],
            'submitted_at': submission_result[5],
            'is_graded': bool(submission_result[6]),
            'total_score': submission_result[7] or 0,
            'max_score': submission_result[8] or 0,
            'assessment_title': submission_result[9],
            'answers': answers
        }

    def update_answer_grade(self, answer_id: int, points_earned: float, feedback: str = None) -> bool:
        """Update the grade and feedback for a specific answer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE answers 
                SET points_earned = ?, feedback = ?, is_correct = ?
                WHERE id = ?
            ''', (points_earned, feedback, points_earned > 0, answer_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating answer grade: {e}")
            return False
        finally:
            conn.close()

    def update_submission_grade(self, submission_id: int, total_earned_score: float, total_possible_score: float, updated_answers: list) -> bool:
        """Update submission grade with individual answer scores"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Update individual answer scores
            for i, answer in enumerate(updated_answers):
                points_earned = answer.get('points_earned', 0)
                feedback = answer.get('feedback', '')
                
                # Get the answer ID or question ID to identify the record
                answer_id = answer.get('answer_id')
                question_id = answer.get('question_id')
                
                if answer_id:
                    # Update by answer ID if available
                    cursor.execute('''
                        UPDATE answers 
                        SET points_earned = ?, feedback = ?
                        WHERE id = ?
                    ''', (points_earned, feedback, answer_id))
                elif question_id:
                    # Update by question ID and submission ID
                    cursor.execute('''
                        UPDATE answers 
                        SET points_earned = ?, feedback = ?
                        WHERE submission_id = ? AND question_id = ?
                    ''', (points_earned, feedback, submission_id, question_id))
                else:
                    # Fallback: update by position (assuming answers are in order)
                    cursor.execute('''
                        UPDATE answers 
                        SET points_earned = ?, feedback = ?
                        WHERE submission_id = ? AND id IN (
                            SELECT id FROM answers 
                            WHERE submission_id = ? 
                            ORDER BY id 
                            LIMIT 1 OFFSET ?
                        )
                    ''', (points_earned, feedback, submission_id, submission_id, i))
            
            # Update submission totals
            cursor.execute('''
                UPDATE submissions 
                SET score = ?, total_score = ?, max_score = ?, is_graded = 1
                WHERE id = ?
            ''', (total_earned_score, total_earned_score, total_possible_score, submission_id))
            
            conn.commit()
            # Get the number of rows affected
            rows_affected = cursor.rowcount
            print(f"DEBUG: Updated submission {submission_id} with score {total_earned_score}/{total_possible_score}")
            print(f"DEBUG: Updated {rows_affected} answer records")
            return True
        except Exception as e:
            print(f"Error updating submission grade: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def finalize_submission_grade(self, submission_id: int) -> bool:
        """Calculate final score and mark submission as graded"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate total score from all answers
            cursor.execute('''
                SELECT COALESCE(SUM(points_earned), 0) as total_score
                FROM answers
                WHERE submission_id = ?
            ''', (submission_id,))
            
            total_score = cursor.fetchone()[0]
            
            # Update submission
            cursor.execute('''
                UPDATE submissions 
                SET total_score = ?, is_graded = 1
                WHERE id = ?
            ''', (total_score, submission_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error finalizing grade: {e}")
            return False
        finally:
            conn.close()
    
    def fix_assessment_status_values(self):
        """Fix any assessments that have NULL or empty status values"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Update assessments with NULL status
            cursor.execute('UPDATE assessments SET status = "published" WHERE status IS NULL AND is_active = 1')
            cursor.execute('UPDATE assessments SET status = "draft" WHERE status IS NULL AND is_active = 0')
            cursor.execute('UPDATE assessments SET status = "draft" WHERE status = ""')
            
            # Check current status distribution
            cursor.execute('SELECT status, COUNT(*) FROM assessments GROUP BY status')
            results = cursor.fetchall()
            print("Assessment status distribution after fix:")
            for status, count in results:
                print(f"  {status}: {count}")
            
            conn.commit()
        except Exception as e:
            print(f"Error fixing assessment status: {e}")
        finally:
            conn.close()
    
    def debug_assessments_table(self):
        """Debug method to check all assessments in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, title, status, is_active, created_at FROM assessments ORDER BY id')
            results = cursor.fetchall()
            print("All assessments in database:")
            for row in results:
                print(f"  ID: {row[0]}, Title: '{row[1]}', Status: '{row[2]}', Active: {row[3]}, Created: {row[4]}")
        except Exception as e:
            print(f"Error debugging assessments: {e}")
        finally:
            conn.close()

    def debug_user_data(self, user_id: int = None):
        """Debug method to check user data in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('''
                    SELECT id, username, full_name, email, admin_id_number, student_number, 
                           section, role, profile_photo, security_question
                    FROM users WHERE id = ?
                ''', (user_id,))
                print(f"🔍 User data for ID {user_id}:")
            else:
                cursor.execute('''
                    SELECT id, username, full_name, email, admin_id_number, student_number, 
                           section, role, profile_photo, security_question
                    FROM users
                ''')
                print("🔍 All users in database:")
            
            results = cursor.fetchall()
            for row in results:
                print(f"  ID: {row[0]}")
                print(f"  Username: '{row[1]}'")
                print(f"  Full Name: '{row[2]}'")
                print(f"  Email: '{row[3]}'")
                print(f"  Admin ID: '{row[4]}'")
                print(f"  Student Number: '{row[5]}'")
                print(f"  Section: '{row[6]}'")
                print(f"  Role: '{row[7]}'")
                print(f"  Profile Photo: '{row[8]}'")
                print(f"  Security Question: '{row[9]}'")
                print("  ---")
                
        except Exception as e:
            print(f"Error debugging user data: {e}")
        finally:
            conn.close()

    def update_user_profile(self, user_id: int, full_name: str = None, email: str = None, 
                           admin_id_number: str = None, student_number: str = None, 
                           section: str = None, security_question: str = None, 
                           security_answer: str = None, profile_photo: str = None) -> bool:
        """Update user profile information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query based on provided parameters
            update_fields = []
            update_values = []
            
            if full_name is not None:
                update_fields.append("full_name = ?")
                update_values.append(full_name)
            
            if email is not None:
                update_fields.append("email = ?")
                update_values.append(email)
            
            if admin_id_number is not None:
                update_fields.append("admin_id_number = ?")
                update_values.append(admin_id_number)
            
            if student_number is not None:
                update_fields.append("student_number = ?")
                update_values.append(student_number)
            
            if section is not None:
                update_fields.append("section = ?")
                update_values.append(section)
            
            if security_question is not None:
                update_fields.append("security_question = ?")
                update_values.append(security_question)
            
            if security_answer is not None:
                security_answer_hash = self.hash_password(security_answer.lower().strip())
                update_fields.append("security_answer_hash = ?")
                update_values.append(security_answer_hash)
            
            if profile_photo is not None:
                update_fields.append("profile_photo = ?")
                update_values.append(profile_photo)
            
            if not update_fields:
                return True  # Nothing to update
            
            # Add user_id to the end of values list
            update_values.append(user_id)
            
            # Execute update query
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
        finally:
            conn.close()
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                         (password_hash, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, full_name, email, admin_id_number, 
                   student_number, section, security_question, profile_photo, created_at
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'role': result[2],
                'full_name': result[3],
                'email': result[4],
                'admin_id_number': result[5],
                'student_number': result[6],
                'section': result[7],
                'security_question': result[8],
                'profile_photo': result[9],
                'created_at': result[10]
            }
        return None

    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student information by ID (alias for get_user_by_id)"""
        return self.get_user_by_id(student_id)
    
    def get_post_sections(self, assessment_id: int) -> List[str]:
        """Get sections assigned to a published assessment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ps.section
            FROM post_sections ps
            JOIN posts p ON ps.post_id = p.id
            WHERE p.assessment_id = ?
        ''', (assessment_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [result[0] for result in results]

    def get_posts_by_section(self, section: str) -> List[Dict]:
        """Get posts filtered by section"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT p.id, p.title, p.description, p.created_at, p.created_by, p.post_type,
                       u.full_name as author_name
                FROM posts p
                JOIN post_sections ps ON ps.post_id = p.id
                JOIN users u ON u.id = p.created_by
                WHERE ps.section = ?
                ORDER BY p.created_at DESC
            """, (section,))
            
            rows = cursor.fetchall()
            posts = []
            for row in rows:
                posts.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2] or '',
                    'created_at': row[3],
                    'author_id': row[4],
                    'post_type': row[5],
                    'author_name': row[6],
                    'section': section
                })
            return posts
        except Exception as e:
            print(f"Error getting posts by section: {e}")
            return []
        finally:
            conn.close()

    def get_announcements_by_section(self, section: str) -> List[Dict]:
        """Get announcements filtered by section"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT a.id, a.title, a.description, a.created_at, a.created_by, a.is_active,
                       u.full_name as creator_name
                FROM announcements a
                LEFT JOIN users u ON a.created_by = u.id
                WHERE a.target_sections IS NULL OR a.target_sections LIKE ?
                ORDER BY a.created_at DESC
            """, (f'%"{section}"%',))
            
            rows = cursor.fetchall()
            announcements = []
            for row in rows:
                announcements.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2] or '',
                    'created_at': row[3],
                    'author_id': row[4],
                    'is_active': row[5],
                    'creator_name': row[6] or 'Unknown',
                    'section': section
                })
            return announcements
        except Exception as e:
            print(f"Error getting announcements by section: {e}")
            return []
        finally:
            conn.close()

    def get_assessments_by_section(self, section: str) -> List[Dict]:
        """Get assessments filtered by section"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT a.id, a.title, a.description, a.duration_minutes, a.status, a.created_at,
                       u.full_name as creator_name
                FROM assessments a
                JOIN posts p ON p.assessment_id = a.id
                JOIN post_sections ps ON ps.post_id = p.id
                JOIN users u ON u.id = a.created_by
                WHERE ps.section = ? AND a.is_active = 1
                ORDER BY a.created_at DESC
            """, (section,))
            
            rows = cursor.fetchall()
            assessments = []
            for row in rows:
                assessments.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'duration_minutes': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'creator_name': row[6],
                    'section': section
                })
            return assessments
        except Exception as e:
            print(f"Error getting assessments by section: {e}")
            return []
        finally:
            conn.close()

    def get_questions_by_assessment_id(self, assessment_id: int):
        """Get all questions for a specific assessment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # For now, use description field since we have it in the table
            cursor.execute('''
                INSERT INTO announcements (title, description, created_by)
                VALUES (?, ?, ?)
            ''', (title, content, created_by))
            
            announcement_id = cursor.lastrowid
            conn.commit()
            print(f"Created announcement with ID: {announcement_id}")
            return announcement_id
            
        except Exception as e:
            print(f"Error creating announcement: {e}")
            return None
        finally:
            conn.close()

    def get_announcements(self, user_id: int = None) -> List[Dict]:
        """Get all announcements"""
        print("Getting announcements from database...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT a.id, a.title, a.description, a.created_by, a.is_active, a.created_at,
                       u.full_name as creator_name
                FROM announcements a
                LEFT JOIN users u ON a.created_by = u.id
                ORDER BY a.created_at DESC
            ''')
            
            results = cursor.fetchall()
            print(f"Found {len(results)} announcements in database")
            
            announcements = []
            for result in results:
                announcements.append({
                    'id': result[0],
                    'title': result[1],
                    'content': result[2] or '',  # description -> content
                    'created_by': result[3],
                    'is_active': result[4],
                    'created_at': result[5],
                    'creator_name': result[6] or 'Unknown',
                    'target_sections': None  # For compatibility
                })
            
            print(f"Returning {len(announcements)} announcements")
            return announcements
            
        except Exception as e:
            print(f"Error getting announcements: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            conn.close()
    
    def get_active_announcements(self, user_id: int = None) -> List[Dict]:
        """Get only active announcements for students"""
        print("Getting active announcements from database...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT a.id, a.title, a.description, a.created_by, a.is_active, a.created_at,
                       u.full_name as creator_name
                FROM announcements a
                LEFT JOIN users u ON a.created_by = u.id
                WHERE a.is_active = 1
                ORDER BY a.created_at DESC
            ''')
            
            results = cursor.fetchall()
            print(f"Found {len(results)} active announcements in database")
            
            announcements = []
            for result in results:
                announcements.append({
                    'id': result[0],
                    'title': result[1],
                    'content': result[2] or '',  # description -> content
                    'created_by': result[3],
                    'is_active': result[4],
                    'created_at': result[5],
                    'creator_name': result[6] or 'Unknown',
                    'target_sections': None  # For compatibility
                })
            
            print(f"Returning {len(announcements)} active announcements")
            return announcements
            
        except Exception as e:
            print(f"Error getting active announcements: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            conn.close()
    
    def toggle_announcement_status(self, announcement_id: int) -> bool:
        """Toggle the active status of an announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First get current status
            cursor.execute('SELECT is_active FROM announcements WHERE id = ?', (announcement_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"Announcement with ID {announcement_id} not found")
                return False
            
            current_status = result[0]
            new_status = 0 if current_status else 1  # Toggle status
            
            # Update the status
            cursor.execute('''
                UPDATE announcements 
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_status, announcement_id))
            
            conn.commit()
            print(f"Toggled announcement {announcement_id} status from {current_status} to {new_status}")
            return True
            
        except Exception as e:
            print(f"Error toggling announcement status: {e}")
            return False
        finally:
            conn.close()
    
    def delete_announcement(self, announcement_id: int) -> bool:
        """Delete an announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"Deleted announcement with ID {announcement_id}")
                return True
            else:
                print(f"No announcement found with ID {announcement_id}")
                return False
                
        except Exception as e:
            print(f"Error deleting announcement: {e}")
            return False
        finally:
            conn.close()
    
    def update_announcement(self, announcement_id: int, title: str, content: str, target_sections: str = None) -> bool:
        """Update an existing announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE announcements 
                SET title = ?, description = ?, target_sections = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (title, content, target_sections, announcement_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"Updated announcement with ID {announcement_id}")
                return True
            else:
                print(f"No announcement found with ID {announcement_id}")
                return False
                
        except Exception as e:
            print(f"Error updating announcement: {e}")
            return False
        finally:
            conn.close()

    def create_announcement(self, title: str, content: str, created_by: int, target_sections: str = None) -> bool:
        """Create a new announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO announcements (title, description, created_by, target_sections, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (title, content, created_by, target_sections))
            
            announcement_id = cursor.lastrowid
            conn.commit()
            print(f"Created announcement with ID: {announcement_id}")
            return True
            
        except Exception as e:
            print(f"Error creating announcement: {e}")
            return False
        finally:
            conn.close()

    def get_assessment_results(self, assessment_id: int, student_id: int) -> Optional[Dict]:
        """Get assessment results for a specific student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get submission details
            cursor.execute('''
                SELECT s.id, s.total_score, s.max_score, s.submitted_at, a.title
                FROM submissions s
                JOIN assessments a ON s.assessment_id = a.id
                WHERE s.assessment_id = ? AND s.student_id = ?
                ORDER BY s.submitted_at DESC
                LIMIT 1
            ''', (assessment_id, student_id))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            submission_id, total_score, max_score, submitted_at, title = result
            
            # Calculate percentage and correct answers
            score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
            
            # Get total questions count
            cursor.execute('SELECT COUNT(*) FROM questions WHERE assessment_id = ?', (assessment_id,))
            total_questions = cursor.fetchone()[0]
            
            # Calculate correct answers (approximate based on score)
            correct_answers = int(total_score / max_score * total_questions) if max_score > 0 else 0
            
            return {
                'submission_id': submission_id,
                'score': total_score,
                'total_points': max_score,
                'score_percentage': score_percentage,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'submitted_at': submitted_at,
                'title': title
            }
            
        except Exception as e:
            print(f"Error getting assessment results: {e}")
            return None
        finally:
            conn.close()

    def get_student_answers(self, assessment_id: int, student_id: int) -> Dict[int, str]:
        """Get student answers for an assessment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get the latest submission for this student and assessment
            cursor.execute('''
                SELECT id FROM submissions 
                WHERE assessment_id = ? AND student_id = ?
                ORDER BY submitted_at DESC
                LIMIT 1
            ''', (assessment_id, student_id))
            
            submission_result = cursor.fetchone()
            if not submission_result:
                return {}
            
            submission_id = submission_result[0]
            
            # Get all answers for this submission
            cursor.execute('''
                SELECT question_id, answer_text
                FROM answers
                WHERE submission_id = ?
            ''', (submission_id,))
            
            answers = {}
            for row in cursor.fetchall():
                answers[row[0]] = row[1]
            
            return answers
            
        except Exception as e:
            print(f"Error getting student answers: {e}")
            return {}
        finally:
            conn.close()

    def get_student_answers_with_grades(self, assessment_id: int, student_id: int) -> Dict[int, Dict]:
        """Get student answers for an assessment with grading information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get the latest submission for this student and assessment
            cursor.execute('''
                SELECT id FROM submissions 
                WHERE assessment_id = ? AND student_id = ?
                ORDER BY submitted_at DESC
                LIMIT 1
            ''', (assessment_id, student_id))
            
            submission_result = cursor.fetchone()
            if not submission_result:
                return {}
            
            submission_id = submission_result[0]
            
            # Get all answers with grading information
            cursor.execute('''
                SELECT question_id, answer_text, points_earned, feedback, is_correct
                FROM answers
                WHERE submission_id = ?
            ''', (submission_id,))
            
            answers = {}
            for row in cursor.fetchall():
                answers[row[0]] = {
                    'answer_text': row[1],
                    'points_earned': row[2],
                    'feedback': row[3],
                    'is_correct': bool(row[4]) if row[4] is not None else None
                }
            
            return answers
            
        except Exception as e:
            print(f"Error getting student answers with grades: {e}")
            return {}
        finally:
            conn.close()
    
    def create_material(self, title: str, description: str, file_path: str, created_by: int, target_sections: str = None) -> bool:
        """Create a new material upload record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create a post record for the material
            cursor.execute('''
                INSERT INTO posts (title, description, post_type, created_by, file_path)
                VALUES (?, ?, 'file', ?, ?)
            ''', (title, description, created_by, file_path))
            
            post_id = cursor.lastrowid
            
            # If specific sections are targeted, add them to post_sections
            if target_sections:
                try:
                    sections = eval(target_sections)  # Convert string back to list
                    for section in sections:
                        cursor.execute('''
                            INSERT INTO post_sections (post_id, section)
                            VALUES (?, ?)
                        ''', (post_id, section))
                except:
                    pass  # If parsing fails, material will be available to all
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error creating material: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_materials(self) -> List[Dict]:
        """Get all uploaded materials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.id, p.title, p.description, p.file_path, p.created_at, u.full_name as creator_name
                FROM posts p
                JOIN users u ON p.created_by = u.id
                WHERE p.post_type = 'file'
                ORDER BY p.created_at DESC
            ''')
            
            materials = []
            for row in cursor.fetchall():
                materials.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'file_path': row[3],
                    'created_at': row[4],
                    'creator_name': row[5]
                })
            
            return materials
            
        except Exception as e:
            print(f"Error getting materials: {e}")
            return []
        finally:
            conn.close()
    
    def delete_material(self, material_id: int) -> bool:
        """Delete a material and its associated file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get file path before deletion
            cursor.execute('SELECT file_path FROM posts WHERE id = ? AND post_type = "file"', (material_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                
                # Delete from post_sections first (foreign key constraint)
                cursor.execute('DELETE FROM post_sections WHERE post_id = ?', (material_id,))
                
                # Delete the post record
                cursor.execute('DELETE FROM posts WHERE id = ? AND post_type = "file"', (material_id,))
                
                # Try to delete the actual file
                try:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")
                except Exception as file_error:
                    print(f"Warning: Could not delete file {file_path}: {file_error}")
                
                conn.commit()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error deleting material: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_material(self, material_id: int, title: str, description: str = None) -> bool:
        """Update material title and description"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE posts 
                SET title = ?, description = ?
                WHERE id = ? AND post_type = 'file'
            ''', (title, description, material_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error updating material: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
