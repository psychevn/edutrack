import flet as ft
from datetime import datetime
from database.database_manager import DatabaseManager

class StudentScoresPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, assessment_id: int):
        self.page = page
        self.db_manager = db_manager
        self.assessment_id = assessment_id
        self.assessment = None
        self.student_scores = []
        self.current_view = "students"  # students, grading
        self.current_submission_id = None
        self.user_data = page.data  # Get user data from page
        
        # Load data
        self.load_assessment_data()
        self.init_ui()
        
    def load_assessment_data(self):
        """Load assessment and student scores data"""
        try:
            print(f"🔍 Loading data for assessment ID: {self.assessment_id}")
            
            # Get assessment details
            self.assessment = self.db_manager.get_assessment_by_id(self.assessment_id)
            print(f"📋 Assessment found: {self.assessment.get('title') if self.assessment else 'None'}")
            
            # Get student scores
            self.student_scores = self.get_student_scores()
            print(f"👥 Found {len(self.student_scores)} student submissions")
            
            if self.student_scores:
                print("📊 Student scores preview:")
                for i, student in enumerate(self.student_scores[:3]):  # Show first 3
                    print(f"  {i+1}. {student['full_name']} - {student['score']}/{student['total_questions']}")
            
        except Exception as e:
            print(f"❌ Error loading assessment data: {e}")
            self.assessment = None
            self.student_scores = []
    
    def get_student_scores(self):
        """Get student scores for the assessment"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Query to get student submissions with user details
            query = """
            SELECT 
                u.id as user_id,
                u.full_name,
                u.section,
                COALESCE(s.score, s.total_score, 0) as score,
                COALESCE(s.total_questions, s.max_score, 0) as total_questions,
                s.submitted_at,
                s.id as submission_id
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            WHERE s.assessment_id = ?
            ORDER BY COALESCE(s.score, s.total_score, 0) DESC, u.full_name ASC
            """
            
            cursor.execute(query, (self.assessment_id,))
            results = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            student_scores = []
            for row in results:
                student_scores.append({
                    'user_id': row[0],
                    'full_name': row[1],
                    'section': row[2] or 'N/A',
                    'score': row[3] or 0,
                    'total_questions': row[4] or 0,
                    'submitted_at': row[5],
                    'submission_id': row[6]
                })
            
            return student_scores
            
        except Exception as e:
            print(f"Error getting student scores: {e}")
            return []
    
    def init_ui(self):
        """Initialize UI components"""
        # Left sidebar navigation
        self.sidebar = ft.Container(
            content=ft.Column([
                # Profile section
                ft.Container(
                    content=ft.Column([
                        self.create_profile_photo(),
                        ft.Text(
                            self.get_user_display_name(),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "admin",
                            size=12,
                            color=ft.Colors.WHITE70,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5),
                    padding=20
                ),
                
                ft.Divider(color="#fafafa", height=20),
                
                # Navigation items
                ft.Container(
                    content=ft.Column([
                        self.create_nav_item(ft.Icons.PERSON, "User", False),
                        self.create_nav_item(ft.Icons.HOME, "Dashboard", False),
                        self.create_nav_item(ft.Icons.ASSIGNMENT, "Assessments", False),
                        self.create_nav_item(ft.Icons.STAR, "Scores", True)  # Active
                    ], spacing=5),
                    padding=ft.padding.symmetric(horizontal=10, vertical=20)
                ),
                
                # Spacer
                ft.Container(expand=True),
                
                # Logout button
                ft.Container(
                    content=ft.TextButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.WHITE70, size=20),
                            ft.Text("Logout", color=ft.Colors.WHITE70, size=14)
                        ], alignment=ft.MainAxisAlignment.START),
                        on_click=self.logout,
                        style=ft.ButtonStyle(
                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            overlay_color=ft.Colors.WHITE10,
                            shape=ft.RoundedRectangleBorder(radius=0)
                        )
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(10)
                )
            ]),
            width=240,
            bgcolor="#efaaaa",  # Soft pink
            padding=ft.padding.all(0),
            margin=ft.margin.only(top=100),
            border_radius=ft.border_radius.only(
                top_left=0,
                top_right=120,
                bottom_left=0,
                bottom_right=0
            )
        )
    
    def create_profile_photo(self):
        """Create profile photo container"""
        profile_photo = self.user_data.get('profile_photo') if self.user_data else None
        if profile_photo:
            return ft.Container(
                content=ft.Image(
                    src=profile_photo,
                    width=60,
                    height=60,
                    fit=ft.ImageFit.COVER,
                    border_radius=30
                ),
                width=60,
                height=60,
                border_radius=30,
                border=ft.border.all(2, ft.Colors.WHITE)
            )
        else:
            return ft.Container(
                content=ft.Image(
                    src="assets/urs_logo.png",
                    width=60,
                    height=60,
                    fit=ft.ImageFit.COVER,
                    border_radius=30
                ),
                width=60,
                height=60,
                border_radius=30,
                border=ft.border.all(2, ft.Colors.WHITE)
            )
    
    def create_nav_item(self, icon, text, is_active):
        """Create a navigation item"""
        return ft.Container(
            content=ft.TextButton(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70, size=20),
                    ft.Text(text, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70, size=14, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL)
                ], alignment=ft.MainAxisAlignment.START),
                on_click=lambda e: self.navigate_to(text.lower()),
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    overlay_color=ft.Colors.WHITE10,
                    shape=ft.RoundedRectangleBorder(radius=0)
                )
            ),
            bgcolor="#bb5862" if is_active else ft.Colors.TRANSPARENT,
            border_radius=5,
            margin=ft.margin.symmetric(vertical=2)
        )
    
    def get_user_display_name(self):
        """Get user display name"""
        if self.user_data:
            return self.user_data.get('full_name', 'Admin')
        return 'Admin'
    
    def navigate_to(self, destination):
        """Navigate to different sections"""
        # Instead of navigating to routes, go back to admin dashboard and let it handle navigation
        if destination == "dashboard":
            self.page.go("/admin")
        elif destination == "assessments":
            self.page.go("/admin")
        elif destination == "scores":
            self.page.go("/admin")
        elif destination == "user":
            self.page.go("/admin")
    
    def logout(self, e):
        """Handle logout"""
        # Clear user data and go to login
        self.page.data = None
        self.page.go("/")
    
    def view_submission_details(self, submission_id: int):
        """View detailed submission for grading"""
        self.current_view = "grading"
        self.current_submission_id = submission_id
        self._refresh_content()
    
    def go_back_to_students(self, e=None):
        """Go back to students view"""
        self.current_view = "students"
        self.current_submission_id = None
        self._refresh_content()
    
    def finalize_grade(self, e=None):
        """Finalize the grade for current submission"""
        if self.current_submission_id:
            success = self.db_manager.finalize_submission_grade(self.current_submission_id)
            if success:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Grade saved successfully!")))
                self.go_back_to_students()
            else:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error saving grade")))
    
    def _refresh_content(self):
        """Refresh the page content by rebuilding it"""
        if hasattr(self, '_content_container') and self._content_container:
            new_content = self.get_content_only()
            self._content_container.content = new_content
            self._content_container.update()
        else:
            self.page.update()
    
    def get_content_only(self) -> ft.Control:
        """Get the main content based on current view"""
        if self.current_view == "grading" and self.current_submission_id:
            submission_details = self.db_manager.get_submission_details(self.current_submission_id)
            return self._create_grading_interface(submission_details)
        
        # Main students view with proper header
        header = ft.Row([
            ft.Icon(ft.Icons.STAR, size=28, color="#D4817A"),
            ft.Text("Student Scores", size=24, weight=ft.FontWeight.BOLD, color="#D4817A"),
            ft.Container(expand=True),
            ft.Text(datetime.now().strftime("%B %d, %Y"), size=14, color="#D4817A"),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        return ft.Column([
            header,
            ft.Container(height=20),
            self.create_students_table()
        ], spacing=0, expand=True)
    
    def _create_grading_interface(self, submission_details: dict) -> ft.Control:
        """Create grading interface for individual submission"""
        if not submission_details:
            return ft.Text("Submission not found", color=ft.Colors.RED)
        
        # Header with student info and back button
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#D4817A",
                    on_click=self.go_back_to_students,
                ),
                ft.Text("← Back", size=14, color="#D4817A"),
                ft.Container(expand=True),
                ft.Text(
                    f"{submission_details.get('student_number', 'N/A')} {submission_details.get('student_name', 'Unknown')}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color="#D4817A",
                ),
                ft.Text(
                    f"Score: ___",
                    size=14,
                    color="#D4817A",
                ),
                ft.Icon(ft.Icons.EDIT, size=16, color="#D4817A"),
                ft.Container(
                    content=ft.Text("GRADE", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor="#8BC34A",
                    border_radius=15,
                    padding=ft.padding.symmetric(horizontal=15, vertical=8),
                    on_click=self.finalize_grade,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(15),
        )
        
        # Questions and answers
        questions_column = []
        for i, answer in enumerate(submission_details.get('answers', [])):
            question_card = self._create_question_card(answer, i + 1)
            questions_column.append(question_card)
        
        return ft.Column([
            header,
            ft.Container(
                content=ft.ListView(
                    controls=questions_column,
                    spacing=15,
                    expand=True,
                ),
                expand=True,
                padding=ft.padding.all(20),
            ),
        ], spacing=0, expand=True)
    
    def _create_question_card(self, answer: dict, question_num: int) -> ft.Control:
        """Create individual question card for grading"""
        question_type = answer.get('question_type', 'mcq')
        is_mcq = question_type == 'mcq'
        
        # Question header
        question_header = ft.Container(
            content=ft.Text(
                "Question",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor="#D4817A",
            border_radius=ft.border_radius.only(top_left=10, top_right=10),
            padding=ft.padding.all(10),
        )
        
        # Question content
        question_content = []
        
        if is_mcq:
            # Multiple choice question
            options = answer.get('options', [])
            if isinstance(options, str):
                import json
                try:
                    options = json.loads(options)
                except:
                    options = []
            
            # Show options with student's selection highlighted
            option_controls = []
            for i, option in enumerate(options):
                option_letter = chr(65 + i)  # A, B, C, D
                is_selected = answer.get('student_answer') == option_letter
                is_correct = answer.get('correct_answer') == option_letter
                
                if is_selected:
                    if is_correct:
                        # Student selected correct answer
                        bgcolor = "#4CAF50"  # Green
                        icon = ft.Icons.CIRCLE
                    else:
                        # Student selected wrong answer
                        bgcolor = "#D4817A"  # Pink/Red
                        icon = ft.Icons.CIRCLE
                else:
                    if is_correct:
                        # Correct answer not selected
                        bgcolor = "#4CAF50"  # Green
                        icon = ft.Icons.CIRCLE_OUTLINED
                    else:
                        # Not selected, not correct
                        bgcolor = ft.Colors.WHITE
                        icon = ft.Icons.CIRCLE_OUTLINED
                
                option_control = ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, size=16, color=ft.Colors.WHITE if bgcolor != ft.Colors.WHITE else ft.Colors.BLACK54),
                        ft.Text(option, size=12, color=ft.Colors.WHITE if bgcolor != ft.Colors.WHITE else ft.Colors.BLACK87),
                    ]),
                    bgcolor=bgcolor,
                    border_radius=10,
                    padding=ft.padding.all(10),
                    margin=ft.margin.only(bottom=5),
                    border=ft.border.all(1, "#D4817A") if bgcolor == ft.Colors.WHITE else None,
                )
                option_controls.append(option_control)
            
            question_content.extend(option_controls)
            
            # Show correct answer and auto-grade info
            question_content.append(
                ft.Text(
                    f"Correct Answer: {answer.get('correct_answer', 'N/A')}",
                    size=12,
                    color="#4CAF50",
                    weight=ft.FontWeight.BOLD,
                )
            )
            question_content.append(
                ft.Text(
                    "Comment:",
                    size=12,
                    color="#D4817A",
                    weight=ft.FontWeight.BOLD,
                )
            )
            
        else:
            # Short answer question
            question_content.append(
                ft.Container(
                    content=ft.Text(
                        answer.get('student_answer') or "No answer provided",
                        size=12,
                        color=ft.Colors.BLACK87,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, "#D4817A"),
                    border_radius=5,
                    padding=ft.padding.all(10),
                    width=float('inf'),
                )
            )
            
            # Score input and comment for manual grading
            score_row = ft.Row([
                ft.Text("Score:", size=12, color="#D4817A", weight=ft.FontWeight.BOLD),
                ft.TextField(
                    value=str(answer.get('points_earned', 0)),
                    width=80,
                    height=35,
                    text_size=12,
                    border_color="#D4817A",
                    data=answer.get('answer_id'),  # Store answer ID for updates
                ),
                ft.Text(f"/ {answer.get('points', 0)}", size=12, color="#D4817A"),
            ])
            question_content.append(score_row)
            
            question_content.append(
                ft.Text(
                    "Comment:",
                    size=12,
                    color="#D4817A",
                    weight=ft.FontWeight.BOLD,
                )
            )
            question_content.append(
                ft.TextField(
                    value=answer.get('feedback') or "",
                    multiline=True,
                    min_lines=2,
                    max_lines=3,
                    border_color="#D4817A",
                    text_size=12,
                    data=answer.get('answer_id'),  # Store answer ID for updates
                )
            )
        
        return ft.Container(
            content=ft.Column([
                question_header,
                ft.Container(
                    content=ft.Column(question_content, spacing=10),
                    padding=ft.padding.all(15),
                    bgcolor=ft.Colors.WHITE,
                ),
            ], spacing=0),
            border=ft.border.all(2, "#D4817A"),
            border_radius=10,
        )
    
    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%m/%d/%Y %H:%M")
        except:
            return date_str
    
    def format_time_taken(self, time_taken):
        """Format time taken for display"""
        if time_taken and time_taken != 'N/A':
            try:
                minutes = int(time_taken) // 60
                seconds = int(time_taken) % 60
                return f"{minutes}m {seconds}s"
            except:
                return str(time_taken)
        return "N/A"
    
    def create_header(self):
        """Create page header"""
        if not self.assessment:
            title = "Student Scores"
            subtitle = "Assessment not found"
        else:
            title = f"Student Scores: {self.assessment.get('title', 'N/A')}"
            subtitle = f"{len(self.student_scores)} students • {self.assessment.get('duration_minutes', 0)} minutes"
        
        return ft.Container(
            content=ft.Column([
                # Back button and title
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#D4817A",
                        icon_size=24,
                        on_click=self.go_back
                    ),
                    ft.Column([
                        ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Text(subtitle, size=14, color=ft.Colors.GREY_600)
                    ], spacing=2, expand=True),
                    ft.Text(datetime.now().strftime("%B %d, %Y"), size=14, color="#D4817A")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Assessment info cards
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Total Students", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            ft.Text(str(len(self.student_scores)), size=20, weight=ft.FontWeight.BOLD, color="#D4817A")
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(15),
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=10,
                        width=150
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Average Score", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            ft.Text(f"{self.calculate_average_score():.1f}%", size=20, weight=ft.FontWeight.BOLD, color="#D4817A")
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(15),
                        bgcolor=ft.Colors.GREEN_50,
                        border_radius=10,
                        width=150
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Highest Score", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            ft.Text(f"{self.get_highest_score():.1f}%", size=20, weight=ft.FontWeight.BOLD, color="#D4817A")
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(15),
                        bgcolor=ft.Colors.ORANGE_50,
                        border_radius=10,
                        width=150
                    )
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=20),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            margin=ft.margin.only(bottom=20)
        )
    
    def calculate_average_score(self):
        """Calculate average score percentage"""
        if not self.student_scores:
            return 0
        
        total_percentage = 0
        for student in self.student_scores:
            if student['total_questions'] > 0:
                percentage = (student['score'] / student['total_questions']) * 100
                total_percentage += percentage
        
        return total_percentage / len(self.student_scores) if self.student_scores else 0
    
    def get_highest_score(self):
        """Get highest score percentage"""
        if not self.student_scores:
            return 0
        
        highest = 0
        for student in self.student_scores:
            if student['total_questions'] > 0:
                percentage = (student['score'] / student['total_questions']) * 100
                highest = max(highest, percentage)
        
        return highest
    
    def create_students_table(self):
        """Create the main students scores table"""
        if not self.student_scores:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No students have taken this assessment yet", size=18, color=ft.Colors.GREY_600),
                    ft.Text("Students will appear here once they submit their answers", size=14, color=ft.Colors.GREY_500)
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                height=400
            )
        
        # Table header
        header_row = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("Rank", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=80,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text("Student Name", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=280,
                    alignment=ft.alignment.center_left,
                    padding=ft.padding.only(left=15)
                ),
                ft.Container(
                    content=ft.Text("Section", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text("Score", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text("Percentage", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text("Time Taken", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text("Submitted", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=150,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text("Actions", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=100,
                    alignment=ft.alignment.center
                )
            ], spacing=0),
            bgcolor="#D4817A",
            padding=ft.padding.symmetric(vertical=15),
            border_radius=ft.border_radius.only(top_left=15, top_right=15)
        )
        
        # Table rows
        table_rows = [header_row]
        
        for i, student in enumerate(self.student_scores, 1):
            # Calculate percentage
            percentage = (student['score'] / student['total_questions'] * 100) if student['total_questions'] > 0 else 0
            
            # Determine colors based on performance
            if percentage >= 90:
                score_color = ft.Colors.GREEN
                row_accent = ft.Colors.GREEN_50
                performance_badge = "🌟 Excellent"
            elif percentage >= 80:
                score_color = ft.Colors.LIGHT_GREEN
                row_accent = ft.Colors.LIGHT_GREEN_50
                performance_badge = "✅ Very Good"
            elif percentage >= 70:
                score_color = ft.Colors.ORANGE
                row_accent = ft.Colors.ORANGE_50
                performance_badge = "👍 Good"
            elif percentage >= 60:
                score_color = ft.Colors.DEEP_ORANGE
                row_accent = ft.Colors.DEEP_ORANGE_50
                performance_badge = "⚠️ Fair"
            else:
                score_color = ft.Colors.RED
                row_accent = ft.Colors.RED_50
                performance_badge = "❌ Needs Improvement"
            
            # Row background - highlight top 3 performers
            if i == 1:
                row_bg = ft.Colors.YELLOW_50  # Gold for 1st place
            elif i == 2:
                row_bg = ft.Colors.GREY_100   # Silver for 2nd place
            elif i == 3:
                row_bg = ft.Colors.ORANGE_50  # Bronze for 3rd place
            else:
                row_bg = ft.Colors.WHITE if i % 2 == 0 else ft.Colors.GREY_50
            
            # Rank with trophy for top 3
            rank_content = ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color="#FFD700", size=20) if i == 1 
                else ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.GREY, size=20) if i == 2
                else ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.ORANGE, size=20) if i == 3
                else ft.Container(width=20),
                ft.Text(str(i), size=16, weight=ft.FontWeight.BOLD if i <= 3 else ft.FontWeight.NORMAL, color="#D4817A")
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
            
            # Student name with enhanced formatting
            student_name_display = ft.Column([
                ft.Text(
                    student['full_name'] or "Unknown Student", 
                    size=15, 
                    color=ft.Colors.BLACK87, 
                    weight=ft.FontWeight.BOLD if i <= 3 else ft.FontWeight.W_500
                ),
                ft.Text(
                    f"ID: {student['user_id']}", 
                    size=11, 
                    color=ft.Colors.GREY_600
                )
            ], spacing=2)
            
            # Section with enhanced display
            section_display = ft.Container(
                content=ft.Text(
                    student['section'] or 'No Section', 
                    size=14, 
                    color=ft.Colors.BLACK87,
                    weight=ft.FontWeight.W_500
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8
            )
            
            # Score with fraction and performance badge
            score_display = ft.Column([
                ft.Text(
                    f"{student['score']}/{student['total_questions']}", 
                    size=16, 
                    color=score_color, 
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    f"({student['score']} correct)", 
                    size=11, 
                    color=ft.Colors.GREY_600
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            # Percentage with performance indicator
            percentage_display = ft.Column([
                ft.Text(
                    f"{percentage:.1f}%", 
                    size=16, 
                    color=score_color, 
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    performance_badge, 
                    size=10, 
                    color=score_color,
                    weight=ft.FontWeight.W_500
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            row = ft.Container(
                content=ft.Row([
                    ft.Container(content=rank_content, width=80, alignment=ft.alignment.center),
                    ft.Container(
                        content=student_name_display,
                        width=280,
                        alignment=ft.alignment.center_left,
                        padding=ft.padding.only(left=15)
                    ),
                    ft.Container(
                        content=section_display,
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=score_display,
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=percentage_display,
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(self.format_time_taken(student.get('time_taken', 'N/A')), size=14, color=ft.Colors.BLACK87),
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(self.format_date(student['submitted_at']), size=12, color=ft.Colors.BLACK87),
                        width=150,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.VISIBILITY,
                            icon_color="#D4817A",
                            icon_size=20,
                            tooltip="View Detailed Submission",
                            on_click=lambda e, sid=student['submission_id']: self.view_submission_details(sid)
                        ),
                        width=100,
                        alignment=ft.alignment.center
                    )
                ], spacing=0),
                bgcolor=row_bg,
                padding=ft.padding.symmetric(vertical=15),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
            )
            table_rows.append(row)
        
        return ft.Container(
            content=ft.Column(
                controls=table_rows,
                spacing=0,
                scroll=ft.ScrollMode.AUTO
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            height=600  # Increased height for better visibility
        )
    
    def view_submission(self, submission_id):
        """View individual student submission"""
        # Navigate to submission details or show dialog
        print(f"Viewing submission {submission_id}")
        # You can implement detailed submission view here
    
    def go_back(self, e=None):
        """Go back to scores page"""
        print("🔙 Going back to scores page")
        
        # Remove the current view from the stack
        if len(self.page.views) > 1:
            self.page.views.pop()
            self.page.update()
        else:
            # Fallback: navigate to admin dashboard scores section
            self.page.go("/admin")
    
    def build(self):
        """Build the complete page"""
        # Main content area with proper scrolling
        main_content = ft.Container(
            content=ft.Column([
                self.get_content_only()
            ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20),
            expand=True,
            bgcolor="#f4f1ec"
        )
        
        # Store reference for content updates
        self._content_container = main_content
        
        return ft.View(
            "/admin/student-scores",
            [
                ft.Row([
                    self.sidebar,
                    main_content
                ], spacing=0, expand=True)
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )
