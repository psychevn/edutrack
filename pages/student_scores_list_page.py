import flet as ft
from datetime import datetime
from database.database_manager import DatabaseManager

class StudentScoresListPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, assessment_id: int):
        self.page = page
        self.db_manager = db_manager
        self.assessment_id = assessment_id
        self.assessment = None
        self.student_scores = []
        self.filtered_student_scores = []
        self.search_query = ""
        self.user_data = page.data
        
        # Reference to parent dashboard for embedded navigation
        self.parent_dashboard = None
        
        # Load data
        self.load_assessment_data()
        self.init_ui()
        
    def load_assessment_data(self):
        """Load assessment and student scores data"""
        try:
            print(f"Loading data for assessment ID: {self.assessment_id}")
            
            # Get assessment details
            self.assessment = self.db_manager.get_assessment_by_id(self.assessment_id)
            print(f" Assessment found: {self.assessment.get('title') if self.assessment else 'None'}")
            
            # Get student scores
            self.student_scores = self.get_student_scores()
            print(f"Found {len(self.student_scores)} student submissions")
            
        except Exception as e:
            print(f"Error loading assessment data: {e}")
            self.assessment = None
            self.student_scores = []
    
    def get_student_scores(self):
        """Get student scores for the assessment with grading status"""
        try:
            print(f"DEBUG: Getting student scores for assessment_id: {self.assessment_id}")
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # First, let's check if the assessment exists
            cursor.execute("SELECT id, title FROM assessments WHERE id = ?", (self.assessment_id,))
            assessment_check = cursor.fetchone()
            print(f"DEBUG: Assessment check result: {assessment_check}")
            
            # Check if there are any submissions for this assessment
            cursor.execute("SELECT COUNT(*) FROM submissions WHERE assessment_id = ?", (self.assessment_id,))
            submission_count = cursor.fetchone()[0]
            print(f"DEBUG: Total submissions for assessment {self.assessment_id}: {submission_count}")
            
            # Query to get student submissions with user details and grading status
            query = """
            SELECT 
                u.id as user_id,
                u.full_name,
                u.student_number,
                u.section,
                COALESCE(s.score, s.total_score, 0) as score,
                COALESCE(s.max_score, 0) as max_score,
                s.submitted_at,
                s.id as submission_id,
                s.is_graded
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            WHERE s.assessment_id = ?
            ORDER BY COALESCE(s.score, s.total_score, 0) DESC, u.full_name ASC
            """
            
            print(f"DEBUG: Executing query with assessment_id: {self.assessment_id}")
            cursor.execute(query, (self.assessment_id,))
            results = cursor.fetchall()
            print(f"DEBUG: Query returned {len(results)} results")
            print(f"DEBUG: Raw results: {results}")
            conn.close()
            
            # Convert to list of dictionaries
            student_scores = []
            for row in results:
                student_scores.append({
                    'user_id': row[0],
                    'full_name': row[1],
                    'student_number': row[2] or 'N/A',
                    'section': row[3] or 'N/A',
                    'score': row[4] or 0,
                    'max_score': row[5] or 0,
                    'submitted_at': row[6],
                    'submission_id': row[7],
                    'is_graded': row[8] or 0
                })
            
            print(f"DEBUG: Processed {len(student_scores)} student scores")
            return student_scores
            
        except Exception as e:
            print(f"Error getting student scores: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
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
        """Create profile photo container with user's actual photo or default"""
        import os
        
        # Get user's profile photo path
        profile_photo_path = None
        if self.user_data and isinstance(self.user_data, dict):
            profile_photo_path = self.user_data.get('profile_photo')
            print(f"Student Scores List - User data: {self.user_data}")
            print(f"Student Scores List - Profile photo path: {profile_photo_path}")
        
        # Check if photo file exists
        if profile_photo_path and os.path.exists(profile_photo_path):
            print(f"Student Scores List - Photo file exists: {profile_photo_path}")
            # Show actual user photo
            return ft.Container(
                content=ft.Image(
                    src=profile_photo_path,
                    width=80,
                    height=80,
                    fit=ft.ImageFit.COVER,
                ),
                width=80,
                height=80,
                border_radius=40,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                border=ft.border.all(3, ft.Colors.WHITE)
            )
        else:
            print(f"Student Scores List - Using default logo")
            # Show default logo
            return ft.Container(
                content=ft.Image(
                    src="assets/urs_logo.png",
                    width=80,
                    height=80,
                    fit=ft.ImageFit.COVER,
                ),
                width=80,
                height=80,
                border_radius=40,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                border=ft.border.all(3, ft.Colors.WHITE)
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
        """Navigate to different sections using direct view manipulation"""
        print(f"Navigating to {destination} from student scores list")
        
        # Use direct view manipulation to prevent transitions
        self.page.views.clear()
        from pages.admin_dashboard import AdminDashboard
        admin_dashboard = AdminDashboard(self.page, self.db_manager)
        self.page.views.append(admin_dashboard.get_view())
        self.page.update()
    
    def logout(self, e):
        """Handle logout"""
        self.page.data = None
        self.page.go("/")
    
    def go_back_to_scores(self, e=None):
        """Go back to admin dashboard with scores section active"""
        print(f"Going back to admin dashboard scores section")
        # Use direct view manipulation to return to admin dashboard with scores active
        self.page.views.clear()
        from pages.admin_dashboard import AdminDashboard
        admin_dashboard = AdminDashboard(self.page, self.db_manager)
        # Navigate to scores section specifically
        admin_dashboard.show_results()
        self.page.views.append(admin_dashboard.get_view())
        self.page.update()
    
    def view_submission_details(self, submission_id: int):
        """Navigate to detailed submission view using embedded approach - NO VIEW CLEARING"""
        print(f"Viewing submission details for ID: {submission_id}")
        
        # Check if we have a parent dashboard reference
        if hasattr(self, 'parent_dashboard') and self.parent_dashboard:
            # Use the embedded approach - update content only
            self.parent_dashboard.show_submission_grading_embedded(self.assessment_id, submission_id)
        else:
            # Fallback: This should not happen in normal flow
            print(f"DEBUG: No parent dashboard found for submission navigation")
            self.page.go(f"/admin/student-scores/{self.assessment_id}/submission/{submission_id}")
    
    def create_search_field(self):
        """Create search field for filtering students"""
        return ft.Container(
            content=ft.TextField(
                hint_text="Search students by name or student number...",
                value=self.search_query,
                width=400,
                height=40,
                text_size=14,
                bgcolor="#F5E6E8",
                border_color="#D4817A",
                on_change=self._on_search_change,
                prefix_icon=ft.Icons.SEARCH
            ),
            padding=ft.padding.only(bottom=15)
        )
    
    def _on_search_change(self, e):
        """Handle search query change"""
        self.search_query = e.control.value.lower()
        self._filter_students()
        self.page.update()
    
    def _filter_students(self):
        """Filter students based on search query"""
        if not self.search_query:
            self.filtered_student_scores = self.student_scores
        else:
            self.filtered_student_scores = [
                student for student in self.student_scores
                if (self.search_query in student['full_name'].lower() or 
                    self.search_query in str(student['student_number']).lower())
            ]
    
    def create_header(self):
        """Create page header with back button"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#D4817A",
                        icon_size=24,
                        on_click=self.go_back_to_scores
                    ),
                    ft.Column([
                        ft.Text("Student Scores", size=24, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Text(f"Assessment: {self.assessment.get('title', 'Unknown') if self.assessment else 'Unknown'}", size=14, color=ft.Colors.GREY_600)
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
            margin=ft.margin.only(bottom=10)
        )
    
    def calculate_average_score(self):
        """Calculate average score percentage"""
        if not self.student_scores:
            return 0
        
        total_percentage = 0
        for student in self.student_scores:
            if student['max_score'] > 0:
                percentage = (student['score'] / student['max_score']) * 100
                total_percentage += percentage
        
        return total_percentage / len(self.student_scores) if self.student_scores else 0
    
    def get_highest_score(self):
        """Get highest score percentage"""
        if not self.student_scores:
            return 0
        
        highest = 0
        for student in self.student_scores:
            if student['max_score'] > 0:
                percentage = (student['score'] / student['max_score']) * 100
                highest = max(highest, percentage)
        
        return highest
    
    def create_students_table(self):
        """Create the main students scores table"""
        # Use flexible column definitions that adapt to container width
        # Define columns as flex values that will scale proportionally
        COLUMN_FLEX = {
            'rank': 1,      # Smallest column
            'name': 3,      # Largest column for names
            'student_no': 2.5,  # Medium column
            'section': 2,    # Small column
            'score': 2,     # Small column
            'percentage': 2,  # Small column
            'date': 2,          # Medium column
            'status': 2,      # Small column
            'view': 2,         # Small column
        }
        
        print(f"DEBUG: Using flexible column layout with flex values: {COLUMN_FLEX}")
        
        # Initialize filtered scores if not done
        if not hasattr(self, 'filtered_student_scores') or not self.filtered_student_scores:
            self._filter_students()
        
        if not self.filtered_student_scores:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No students found" if self.search_query else "No students have taken this assessment yet", size=18, color=ft.Colors.GREY_600),
                    ft.Text("Try adjusting your search" if self.search_query else "Students will appear here once they submit their answers", size=14, color=ft.Colors.GREY_500)
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                height=400
            )
        
        # Table header with flexible column widths using expand property
        header_row = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("#", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['rank'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Student Name", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['name'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Student No.", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['student_no'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Section", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['section'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Score", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['score'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("%", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['percentage'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Date", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['date'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Status", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['status'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("View", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    expand=COLUMN_FLEX['view'],
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                )
            ], spacing=0),
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        
        # Table rows
        table_rows = [header_row]
        for i, student in enumerate(self.filtered_student_scores, 1):
            # Calculate percentage
            percentage = (student['score'] / student['max_score'] * 100) if student['max_score'] > 0 else 0
            
            # Determine colors based on performance
            if percentage >= 90:
                score_color = ft.Colors.GREEN
            elif percentage >= 80:
                score_color = ft.Colors.LIGHT_GREEN
            elif percentage >= 70:
                score_color = ft.Colors.ORANGE
            elif percentage >= 60:
                score_color = ft.Colors.DEEP_ORANGE
            else:
                score_color = ft.Colors.RED
            
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
                ft.Icon(ft.Icons.EMOJI_EVENTS, color="#FFD700", size=16) if i == 1 
                else ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.GREY, size=16) if i == 2
                else ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.ORANGE, size=16) if i == 3
                else ft.Container(width=16),
                ft.Text(str(i), size=14, weight=ft.FontWeight.BOLD if i <= 3 else ft.FontWeight.NORMAL, color="#D4817A")
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
            
            # Grading status
            is_graded = student.get('is_graded', 0)
            status_display = ft.Container(
                content=ft.Text(
                    "Graded" if is_graded else "Ungraded",
                    size=12,
                    color=ft.Colors.GREEN if is_graded else ft.Colors.ORANGE,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=ft.Colors.GREEN_50 if is_graded else ft.Colors.ORANGE_50,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=8, vertical=4)
            )
            
            row = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=rank_content, 
                        expand=COLUMN_FLEX['rank'], 
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(
                            student['full_name'] or "Unknown Student", 
                            size=13, 
                            color=ft.Colors.BLACK87, 
                            weight=ft.FontWeight.BOLD if i <= 3 else ft.FontWeight.W_500
                        ),
                        expand=COLUMN_FLEX['name'],
                        alignment=ft.alignment.center_left,
                        padding=ft.padding.only(left=10)
                    ),
                    ft.Container(
                        content=ft.Text(
                            str(student['student_number']) or 'N/A',
                            size=12,
                            color=ft.Colors.BLACK87
                        ),
                        expand=COLUMN_FLEX['student_no'],
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(
                            student['section'] or 'N/A',
                            size=12,
                            color=ft.Colors.BLACK87
                        ),
                        expand=COLUMN_FLEX['section'],
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"{student['score']}/{student['max_score']}",
                            size=12,
                            color=score_color,
                            weight=ft.FontWeight.BOLD
                        ),
                        expand=COLUMN_FLEX['score'],
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(f"{percentage:.1f}%", size=12, color=score_color, weight=ft.FontWeight.BOLD),
                        expand=COLUMN_FLEX['percentage'],
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(self.format_date(student['submitted_at']), size=11, color=ft.Colors.BLACK87),
                        expand=COLUMN_FLEX['date'],
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=status_display,
                        expand=COLUMN_FLEX['status'],
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.VISIBILITY,
                            icon_color="#D4817A",
                            icon_size=18,
                            tooltip="View Detailed Submission",
                            on_click=lambda e, sid=student['submission_id']: self.view_submission_details(sid)
                        ),
                        expand=COLUMN_FLEX['view'],
                        alignment=ft.alignment.center
                    )
                ], spacing=0),
                bgcolor=row_bg,
                padding=ft.padding.symmetric(vertical=12),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
            )
            table_rows.append(row)
        
        # Create responsive table that adapts to container width
        table_column = ft.Column(
            controls=table_rows,
            spacing=0,
            tight=True
        )
        
        return ft.Container(
            content=table_column,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            height=600,
            expand=True,  # Allow table to expand to fill available space
            padding=ft.padding.all(0)   # No container padding
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
    
    def build(self):
        """Build the complete page"""
        try:
            # Initialize filtered scores
            self._filter_students()
            
            # Main content area
            main_content = ft.Container(
                content=ft.Column([
                    self.create_header(),
                    self.create_search_field(),
                    self.create_students_table()
                ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.all(20),
                expand=True,
                bgcolor="#f4f1ec"
            )
            
            return ft.View(
                "/admin/student-scores-list",
                [
                    ft.Row([
                        self.sidebar,
                        main_content
                    ], spacing=0, expand=True)
                ],
                padding=0,
                bgcolor="#f4f1ec"
            )
        except Exception as e:
            print(f" Error building student scores list page: {e}")
            # Return a simple error view
            return ft.View(
                "/admin/student-scores-list",
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Error loading student scores", size=18, color=ft.Colors.RED),
                            ft.Text(f"Details: {str(e)}", size=12, color=ft.Colors.GREY)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(50),
                        alignment=ft.alignment.center
                    )
                ],
                padding=0,
                bgcolor="#f4f1ec"
            )
