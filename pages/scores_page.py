import flet as ft
import json
from typing import List, Dict, Any, Optional
from database.database_manager import DatabaseManager
from datetime import datetime

class ScoresPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.current_view = "assessments"  # assessments, students, grading
        self.current_assessment_id = None
        self.current_submission_id = None
        self.expanded_assessment_id = None
        self.search_query = ""
        self.sort_order = "newest first"
        self.user_data = page.data
        self.assessment = None
        self.student_scores = []
        self.submission_details = None
        
        # Content container for seamless navigation
        self.main_content = None
        
        # Reference to parent dashboard for embedded navigation
        self.parent_dashboard = None
        
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%m/%d/%Y")
        except:
            return date_str

    def _initialize_main_content(self):
        """Initialize the main content container"""
        self.main_content = ft.Container(
            content=self.get_content_only(),
            padding=ft.padding.all(20),
            expand=True,
            bgcolor="#f4f1ec"
        )
        print(f"Main content container initialized")

    def _on_button_hover(self, e, normal_color: str, hover_color: str):
        """Handle button hover effects"""
        try:
            if e.data == "true":  # Mouse enter
                e.control.bgcolor = hover_color
                e.control.scale = 1.05
            else:  # Mouse leave
                e.control.bgcolor = normal_color
                e.control.scale = 1.0
            e.control.update()
        except:
            # If update fails, just continue
            pass
    
    def _on_button_click(self, e, assessment_id: int):
        """Handle button click without complex animations"""
        print(f"DEBUG: Button clicked for assessment {assessment_id}")
        
        # Skip animations to prevent transitions
        # Call the actual function immediately
        self._view_student_scores_page(assessment_id)

    def _create_search_bar(self) -> ft.Control:
        """Create the search and filter bar matching the UI design"""
        print(f"DEBUG: Creating search bar with sort_order='{self.sort_order}', search_query='{self.search_query}'")
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Dropdown(
                        value=self.sort_order,
                        options=[
                            ft.dropdown.Option("newest first"),
                            ft.dropdown.Option("oldest first"),
                            ft.dropdown.Option("most students"),
                            ft.dropdown.Option("least students"),
                        ],
                        text_size=12,
                        bgcolor="#F5E6E8",
                        border_color="#D4817A",
                        on_change=self._on_sort_change,
                        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    ),
                    width=240,
                ),
                ft.TextField(
                    hint_text="Search assessments...",
                    value=self.search_query,
                    width=300,
                    height=40,
                    text_size=12,
                    bgcolor="#F5E6E8",
                    border_color="#D4817A",
                    on_change=self._on_search_change,
                ),
                ft.IconButton(
                    icon=ft.Icons.SEARCH,
                    icon_color="#D4817A",
                    bgcolor="#F5E6E8",
                    on_click=self._refresh_assessments,
                ),
                ft.IconButton(
                    icon=ft.Icons.SORT,
                    icon_color="#D4817A",
                    bgcolor="#F5E6E8",
                ),
            ], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.all(15),
            bgcolor="#F5E6E8",
            border_radius=10,
            margin=ft.margin.only(bottom=20),
        )

    def _create_assessment_card(self, assessment: Dict[str, Any], is_expanded: bool) -> ft.Control:
        """Create assessment card matching the UI design from Image 1"""
        assessment_id = assessment['id']
        
        # Main assessment info
        main_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(
                            assessment.get('title', f"Assessment #{assessment_id}"),
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            f"{assessment['total_questions']} items    total scores: {assessment['total_points']}",
                            size=12,
                            color=ft.Colors.WHITE70,
                        ),
                        ft.Text(
                            self._format_date(assessment['created_at']),
                            size=10,
                            color=ft.Colors.WHITE60,
                        ),
                    ], expand=True),
                    ft.Column([
                        ft.Container(
                            content=ft.Text(
                                str(assessment['students_taken']),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor="#B85450",
                            border_radius=20,
                            padding=ft.padding.all(10),
                            width=50,
                            height=50,
                        ),
                        ft.Text(
                            "No. of Student's Taken",
                            size=10,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.PEOPLE, size=16, color=ft.Colors.WHITE),
                                ft.Text("View Students", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor="#B85450",
                            border_radius=15,
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            on_click=lambda e, aid=assessment_id: self._on_button_click(e, aid),
                            on_hover=lambda e: self._on_button_hover(e, "#B85450", "#A04440"),
                            # Removed animation to prevent UI issues
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            bgcolor="#D4817A",
            border_radius=15,
            padding=ft.padding.all(20),
            margin=ft.margin.only(bottom=5),
        )
        
        # Students table (shown when expanded)
        students_table = None
        if is_expanded:
            students_table = self._create_students_table(assessment_id)
        
        return ft.Column([
            main_card,
            students_table if students_table else ft.Container(),
        ], spacing=0)

    def _create_students_table(self, assessment_id: int) -> ft.Control:
        """Create students table showing actual student scores, names, and sections"""
        submissions = self.get_student_submissions_with_details(assessment_id)
        
        # Table header
        header_row = ft.Row([
            ft.Text("Rank", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=1),
            ft.Text("Student Name", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=3),
            ft.Text("Section", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=2),
            ft.Text("Score", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=2),
            ft.Text("Percentage", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=2),
            ft.Text("Date", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=2),
            ft.Text("View", size=12, weight=ft.FontWeight.BOLD, color="#D4817A", expand=1),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Table rows
        table_rows = []
        for i, submission in enumerate(submissions, 1):
            # Calculate percentage
            percentage = (submission['score'] / submission['total_questions'] * 100) if submission['total_questions'] > 0 else 0
            
            # Determine score color based on percentage
            if percentage >= 80:
                score_color = ft.Colors.GREEN
            elif percentage >= 60:
                score_color = ft.Colors.ORANGE
            else:
                score_color = ft.Colors.RED
            
            # Rank icon for top 3
            rank_content = ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color="#FFD700", size=14) if i == 1 
                else ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.GREY, size=14) if i == 2
                else ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.ORANGE, size=14) if i == 3
                else ft.Container(width=14),
                ft.Text(str(i), size=11, color="#D4817A", weight=ft.FontWeight.BOLD if i <= 3 else ft.FontWeight.NORMAL)
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
            
            row = ft.Row([
                ft.Container(content=rank_content, expand=1),
                ft.Text(submission['student_name'], size=11, color="#D4817A", expand=3),
                ft.Text(submission['section'] or 'N/A', size=11, color="#D4817A", expand=2),
                ft.Text(f"{submission['score']}/{submission['total_questions']}", size=11, color=score_color, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text(f"{percentage:.1f}%", size=11, color=score_color, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text(self._format_date(submission['submitted_at']), size=11, color="#D4817A", expand=2),
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.VISIBILITY,
                        size=16,
                        color="#D4817A",
                    ),
                    on_click=lambda e, sid=submission['submission_id']: self._view_submission(sid),
                    expand=1,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            table_rows.append(row)
        
        if not table_rows:
            table_rows.append(
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=32, color=ft.Colors.GREY_400),
                            ft.Text("No students have taken this assessment yet", 
                                   size=12, color=ft.Colors.BLACK54, 
                                   text_align=ft.TextAlign.CENTER)
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=ft.padding.all(20)
                    )
                ])
            )
        
        return ft.Container(
            content=ft.Column([
                header_row,
                ft.Divider(height=1, color="#D4817A"),
                *table_rows,
            ], spacing=8),
            padding=ft.padding.all(15),
            bgcolor="#F9F9F9",
            border_radius=10,
            margin=ft.margin.only(top=10)
        )
    
    def get_student_submissions_with_details(self, assessment_id: int):
        """Get student submissions with complete details including scores and sections"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Query to get detailed student submissions
            query = """
            SELECT 
                s.id as submission_id,
                s.student_id,
                u.full_name as student_name,
                u.section,
                COALESCE(s.score, s.total_score, 0) as score,
                COALESCE(s.total_questions, s.max_score, 0) as total_questions,
                s.submitted_at,
                s.is_graded
            FROM submissions s
            JOIN users u ON s.student_id = u.id
            WHERE s.assessment_id = ?
            ORDER BY COALESCE(s.score, s.total_score, 0) DESC, u.full_name ASC
            """
            
            cursor.execute(query, (assessment_id,))
            results = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            submissions = []
            for row in results:
                submissions.append({
                    'submission_id': row[0],
                    'user_id': row[1],
                    'student_name': row[2],
                    'section': row[3],
                    'score': row[4] or 0,
                    'total_questions': row[5] or 0,
                    'submitted_at': row[6],
                    'is_graded': row[7]
                })
            
            return submissions
            
        except Exception as e:
            print(f"Error getting student submissions: {e}")
            return []
    
    def load_assessment_data(self):
        """Load assessment and student scores data"""
        try:
            print(f"Loading data for assessment ID: {self.current_assessment_id}")
            
            # Get assessment details
            self.assessment = self.db_manager.get_assessment_by_id(self.current_assessment_id)
            print(f"Assessment found: {self.assessment.get('title') if self.assessment else 'None'}")
            
            # Get student scores
            self.student_scores = self.get_student_scores()
            print(f"Found {len(self.student_scores)} student submissions")
            print(f"Student scores data: {self.student_scores}")
            
        except Exception as e:
            print(f"Error loading assessment data: {e}")
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
            
            print(f"Executing query for assessment ID: {self.current_assessment_id}")
            cursor.execute(query, (self.current_assessment_id,))
            results = cursor.fetchall()
            conn.close()
            
            print(f"Query results: {len(results)} rows")
            print(f"Raw results: {results}")
            
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
            
            print(f"Processed student scores: {student_scores}")
            return student_scores
            
        except Exception as e:
            print(f"Error getting student scores: {e}")
            return []
    
    def load_submission_data(self):
        """Load submission details for grading"""
        try:
            print(f"Loading submission data for ID: {self.current_submission_id}")
            self.submission_details = self.db_manager.get_submission_details(self.current_submission_id)
            print(f"Submission found: {self.submission_details.get('student_name') if self.submission_details else 'None'}")
        except Exception as e:
            print(f"Error loading submission data: {e}")
            self.submission_details = None

    def _create_grading_interface(self, submission_details: Dict) -> ft.Control:
        """Create grading interface matching the UI design from Image 3"""
        if not submission_details:
            return ft.Text("Submission not found", color=ft.Colors.RED)
        
        # Header with student info and back button
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#D4817A",
                    on_click=self._go_back_to_students,
                ),
                ft.Text("Back", size=14, color="#D4817A"),
                ft.Container(expand=True),
                ft.Text(
                    f"{submission_details['student_number']}    {submission_details['student_name']}",
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
                    on_click=self._finalize_grade,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(15),
        )
        
        # Questions and answers
        questions_column = []
        for i, answer in enumerate(submission_details['answers']):
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
            ),
        ], expand=True)

    def _create_question_card(self, answer: Dict, question_num: int) -> ft.Control:
        """Create individual question card for grading"""
        question_type = answer['question_type']
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
            options = json.loads(answer['options']) if answer['options'] else []
            
            # Show options with student's selection highlighted
            option_controls = []
            for i, option in enumerate(options):
                option_letter = chr(65 + i)  # A, B, C, D
                is_selected = answer['student_answer'] == option_letter
                is_correct = answer['correct_answer'] == option_letter
                
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
                    f"Correct Answer: {answer['correct_answer']}",
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
                        answer['student_answer'] or "No answer provided",
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
                    value=str(answer['points_earned']),
                    width=80,
                    height=35,
                    text_size=12,
                    border_color="#D4817A",
                    data=answer['answer_id'],  # Store answer ID for updates
                ),
                ft.Text(f"/ {answer['points']}", size=12, color="#D4817A"),
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
                    value=answer['feedback'] or "",
                    multiline=True,
                    min_lines=2,
                    max_lines=3,
                    border_color="#D4817A",
                    text_size=12,
                    data=answer['answer_id'],  # Store answer ID for updates
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

    def _view_student_scores_page(self, assessment_id: int):
        """Show student scores embedded within admin dashboard - NO VIEW CLEARING"""
        print(f"DEBUG: Embedding student scores for assessment {assessment_id}")
        
        # Check if we have a parent dashboard reference
        if hasattr(self, 'parent_dashboard') and self.parent_dashboard:
            # Use the embedded approach - update content only
            self.parent_dashboard.show_student_scores_embedded(assessment_id)
        else:
            # Fallback: try to find admin dashboard in page data or create new navigation
            print(f"DEBUG: No parent dashboard found, using fallback navigation")
            # This should not happen in normal flow, but provides safety
            self.page.go(f"/admin/student-scores-list/{assessment_id}")

    def _toggle_students_view(self, assessment_id: int):
        """Toggle the students view for an assessment"""
        if self.expanded_assessment_id == assessment_id:
            self.expanded_assessment_id = None
        else:
            self.expanded_assessment_id = assessment_id
        self._refresh_content()

    def _view_submission(self, submission_id: int):
        """Show submission grading content within the same page"""
        print(f"Showing submission grading for ID {submission_id}")
        
        # Load submission data
        self.current_view = "grading"
        self.current_submission_id = submission_id
        self.load_submission_data()
        
        # Update content by rebuilding the entire view
        self._refresh_content()

    def _go_back_to_students(self, e=None):
        """Go back to students view"""
        if self.current_view == "grading":
            # Go back to students list
            self.current_view = "students"
            self.current_submission_id = None
        else:
            # Go back to main assessments view
            self.current_view = "assessments"
            self.current_assessment_id = None
            self.current_submission_id = None
        
        # Update content by rebuilding the entire view
        self._refresh_content()
    
    def _go_back_to_main_scores(self, e=None):
        """Go back to main scores view within admin dashboard"""
        print(f"DEBUG: Going back to main scores view")
        # Refresh the admin dashboard with scores section active
        self.page.views.clear()
        from pages.admin_dashboard import AdminDashboard
        admin_dashboard = AdminDashboard(self.page, self.db_manager)
        admin_dashboard.show_results()
        self.page.views.append(admin_dashboard.get_view())
        self.page.update()

    def _finalize_grade(self, e=None):
        """Finalize the grade for current submission"""
        if self.current_submission_id:
            success = self.db_manager.finalize_submission_grade(self.current_submission_id)
            if success:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Grade saved successfully!")))
                self._go_back_to_students()
            else:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error saving grade")))

    def _on_search_change(self, e):
        """Handle search query change"""
        print(f"DEBUG: Search changed to: '{e.control.value}'")
        self.search_query = e.control.value
        print(f"DEBUG: self.search_query set to: '{self.search_query}'")
        self._refresh_assessments()

    def _on_sort_change(self, e):
        """Handle sort order change"""
        print(f"DEBUG: Sort changed to: '{e.control.value}'")
        self.sort_order = e.control.value
        print(f"DEBUG: self.sort_order set to: '{self.sort_order}'")
        self._refresh_assessments()

    def _refresh_assessments(self, e=None):
        """Refresh the assessments list"""
        self._refresh_content()

    def _refresh_content(self):
        """Refresh the page content using embedded pattern - NO VIEW CLEARING"""
        try:
            print(f"Refreshing content for view: {self.current_view}")
            
            # Check if we have a parent dashboard reference
            if hasattr(self, 'parent_dashboard') and self.parent_dashboard:
                # Use embedded refresh - update content only
                print(f"Using embedded refresh through parent dashboard")
                self.parent_dashboard.show_results()
            else:
                # Fallback: direct content update without view clearing
                print(f"Using direct content update")
                if hasattr(self, 'main_content') and self.main_content:
                    self.main_content.content = self.get_content_only()
                    self.page.update()
                else:
                    self.page.update()
            
            print(f"Content refreshed successfully - NO TRANSITIONS")
        except Exception as e:
            print(f"Error refreshing content: {e}")
            # Fallback to page update
            self.page.update()

    def get_content_only(self) -> ft.Control:
        """Get the main content based on current view"""
        print(f"Getting content for view: {self.current_view}")
        print(f"Current assessment ID: {self.current_assessment_id}")
        print(f"Current submission ID: {self.current_submission_id}")
        
        if self.current_view == "grading" and self.current_submission_id:
            print(f"Returning grading interface for submission {self.current_submission_id}")
            return self._create_grading_interface(self.submission_details)
        elif self.current_view == "students" and self.current_assessment_id:
            print(f"Returning student scores interface for assessment {self.current_assessment_id}")
            print(f"Student scores data: {len(self.student_scores) if self.student_scores else 0} students")
            return self._create_student_scores_interface()
        
        # Main assessments view
        header = ft.Row([
            ft.Icon(ft.Icons.STAR, size=28, color="#D4817A"),
            ft.Text("Scores", size=24, weight=ft.FontWeight.BOLD, color="#D4817A"),
            ft.Container(expand=True),
            ft.Text(datetime.now().strftime("%B %d, %Y"), size=14, color="#D4817A"),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Get published assessments
        assessments = self.db_manager.get_published_assessments_with_stats()
        
        # Apply search filter
        if self.search_query:
            assessments = [a for a in assessments if self.search_query.lower() in a['title'].lower()]

        # Apply sorting
        if self.sort_order == "newest first":
            assessments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif self.sort_order == "oldest first":
            assessments.sort(key=lambda x: x.get('created_at', ''))
        elif self.sort_order == "most students":
            assessments.sort(key=lambda x: x.get('students_taken', 0), reverse=True)
        elif self.sort_order == "least students":
            assessments.sort(key=lambda x: x.get('students_taken', 0))

        # Create assessment cards
        assessment_cards = []
        for assessment in assessments:
            is_expanded = self.expanded_assessment_id == assessment['id']
            card = self._create_assessment_card(assessment, is_expanded)
            assessment_cards.append(card)

        if not assessment_cards:
            assessment_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ASSIGNMENT, size=64, color=ft.Colors.GREY_400),
                        ft.Text("No published assessments found", size=16, color=ft.Colors.GREY_600),
                        ft.Text("Publish some assessments to see student scores", size=12, color=ft.Colors.GREY_500)
                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.all(40),
                    alignment=ft.alignment.center
                )
            )

        # Create the main content container
        content = ft.Column([
            header,
            ft.Container(height=20),
            self._create_search_bar(),
            ft.Container(height=20),
            ft.Text("List of Assessments", size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
            ft.Container(height=10),
            ft.Column(assessment_cards, spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        ], spacing=0, expand=True)
        
        return content
    
    def _create_student_scores_interface(self) -> ft.Control:
        """Create the student scores interface"""
        # Header with back button
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#D4817A",
                        icon_size=24,
                        on_click=self._go_back_to_students
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
                            ft.Text(f"{self._calculate_average_score():.1f}%", size=20, weight=ft.FontWeight.BOLD, color="#D4817A")
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(15),
                        bgcolor=ft.Colors.GREEN_50,
                        border_radius=10,
                        width=150
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Highest Score", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            ft.Text(f"{self._get_highest_score():.1f}%", size=20, weight=ft.FontWeight.BOLD, color="#D4817A")
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
        
        # Students table
        students_table = self._create_detailed_students_table()
        
        return ft.Column([
            header,
            students_table
        ], spacing=0, expand=True)
    
    def _calculate_average_score(self):
        """Calculate average score percentage"""
        if not self.student_scores:
            return 0
        
        total_percentage = 0
        for student in self.student_scores:
            if student['total_questions'] > 0:
                percentage = (student['score'] / student['total_questions']) * 100
                total_percentage += percentage
        
        return total_percentage / len(self.student_scores) if self.student_scores else 0
    
    def _get_highest_score(self):
        """Get highest score percentage"""
        if not self.student_scores:
            return 0
        
        highest = 0
        for student in self.student_scores:
            if student['total_questions'] > 0:
                percentage = (student['score'] / student['total_questions']) * 100
                highest = max(highest, percentage)
        
        return highest
    
    def _create_detailed_students_table(self):
        """Create the detailed students scores table"""
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
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Student Name", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=280,
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Section", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Score", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Percentage", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=120,
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("Date", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=150,
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                ),
                ft.Container(
                    content=ft.Text("View", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    width=100,
                    alignment=ft.alignment.center,
                    bgcolor="#D4817A",
                    padding=ft.padding.symmetric(vertical=12)
                )
            ], spacing=0),
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
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
            
            row = ft.Container(
                content=ft.Row([
                    ft.Container(content=rank_content, width=80, alignment=ft.alignment.center),
                    ft.Container(
                        content=ft.Text(student['full_name'] or "Unknown Student", size=15, color=ft.Colors.BLACK87, weight=ft.FontWeight.BOLD if i <= 3 else ft.FontWeight.W_500),
                        width=280,
                        alignment=ft.alignment.center_left,
                        padding=ft.padding.only(left=15)
                    ),
                    ft.Container(
                        content=ft.Text(student['section'] or 'N/A', size=14, color=ft.Colors.BLACK87, weight=ft.FontWeight.W_500),
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(f"{student['score']}/{student['total_questions']}", size=14, color=score_color, weight=ft.FontWeight.BOLD),
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(f"{percentage:.1f}%", size=14, color=score_color, weight=ft.FontWeight.BOLD),
                        width=120,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(self._format_date_detailed(student['submitted_at']), size=12, color=ft.Colors.BLACK87),
                        width=150,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.VISIBILITY,
                            icon_color="#D4817A",
                            icon_size=20,
                            tooltip="View Detailed Submission",
                            on_click=lambda e, sid=student['submission_id']: self._view_submission(sid)
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
            height=600
        )
    
    def _format_date_detailed(self, date_str):
        """Format date string for detailed display"""
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%m/%d/%Y %H:%M")
        except:
            return date_str
    
    def get_view(self):
        """Return the scores page view"""
        # Create fresh content every time to ensure proper display
        main_content = ft.Container(
            content=self.get_content_only(),
            padding=ft.padding.all(20),
            expand=True,
            bgcolor="#f4f1ec"
        )
        
        return ft.View(
            "/admin-scores",
            [main_content],
            padding=0,
            bgcolor="#f4f1ec"
        )
