import flet as ft
from typing import Dict, List, Optional

class StudentResultsPage:
    def __init__(self, page: ft.Page, db_manager, user_data: Dict, assessment_id: int):
        self.page = page
        self.db_manager = db_manager
        self.user_data = user_data
        self.assessment_id = assessment_id
        self.assessment = None
        self.results = None
        self.questions = []
        self.student_answers = {}
        
        # Load data
        self.load_assessment_data()
        
    def load_assessment_data(self):
        """Load assessment, results, questions, and student answers"""
        try:
            # Get assessment details
            self.assessment = self.db_manager.get_assessment_by_id(self.assessment_id)
            if not self.assessment:
                self.show_error("Assessment not found")
                return

            # Get detailed results from database
            self.results = self.db_manager.get_assessment_results(
                assessment_id=self.assessment_id,
                student_id=self.user_data['id']
            )

            if not self.results:
                self.show_error("Results not found")
                return

            # Get questions and answers for this assessment
            self.questions = self.db_manager.get_questions(self.assessment_id)
            self.student_answers = self.db_manager.get_student_answers_with_grades(
                assessment_id=self.assessment_id,
                student_id=self.user_data['id']
            )

        except Exception as ex:
            self.show_error(f"Error loading assessment data: {str(ex)}")

    def show_error(self, message: str):
        """Show error message"""
        print(f"Error: {message}")
        # You could also show a dialog or navigate back
    
    def clean_student_answer(self, student_answer):
        """Clean student answer by removing quotes, brackets, and extra formatting"""
        if not student_answer:
            return student_answer
        
        student_answer = str(student_answer).strip()
        if student_answer.startswith('"') and student_answer.endswith('"'):
            student_answer = student_answer[1:-1]
        if student_answer.startswith("'") and student_answer.endswith("'"):
            student_answer = student_answer[1:-1]
        if student_answer.startswith('["') and student_answer.endswith('"]'):
            student_answer = student_answer[2:-2]
        if student_answer.startswith("['") and student_answer.endswith("']"):
            student_answer = student_answer[2:-2]
        # Handle cases like '["ert346546"' (incomplete bracket)
        if student_answer.startswith('["'):
            student_answer = student_answer[2:]
        if student_answer.startswith("['"):
            student_answer = student_answer[2:]
        if student_answer.endswith('"'):
            student_answer = student_answer[:-1]
        if student_answer.endswith("'"):
            student_answer = student_answer[:-1]
        
        return student_answer

    def create_results_view(self) -> ft.Container:
        """Create the main results view"""
        if not self.assessment or not self.results:
            return ft.Container(
                content=ft.Text("Error loading results", color=ft.Colors.RED),
                alignment=ft.alignment.center
            )

        # Calculate current score
        total_questions = len(self.questions)
        correct_count = self.results.get('correct_answers', 0)
        
        # Create header matching the grading page theme
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        self.assessment['title'],
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        self.assessment.get('description', 'Assessment Results'),
                        size=14,
                        color=ft.Colors.WHITE70,
                        style=ft.TextStyle(italic=True)
                    )
                ], spacing=8, expand=True),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"{correct_count}/{total_questions}",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "current score",
                            size=12,
                            color=ft.Colors.WHITE70,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="#B85450",
                    border_radius=12,
                    padding=ft.padding.all(12),
                    width=100
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(20),
            bgcolor="#D4817A",
            border_radius=15,
            margin=ft.margin.only(bottom=20)
        )

        # Create question results
        question_results = []
        for i, question in enumerate(self.questions):
            student_answer_data = self.student_answers.get(question['id'], {})
            student_answer = student_answer_data.get('answer_text', '') if isinstance(student_answer_data, dict) else student_answer_data
            question_results.append(
                self.create_question_result_card(question, student_answer, i + 1, student_answer_data)
            )

        # Scrollable content area
        content_area = ft.Container(
            content=ft.Column(question_results, spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=ft.padding.all(0)
        )

        # Back button matching grading page theme
        back_button = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ARROW_BACK, color=ft.Colors.WHITE),
                    ft.Text("BACK", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                bgcolor="#D4817A",
                color=ft.Colors.WHITE,
                width=200,
                height=45,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=20, vertical=12)
                ),
                on_click=self.go_back
            ),
            alignment=ft.alignment.bottom_right,
            padding=ft.padding.all(20)
        )

        # Main results layout
        return ft.Column([
            header,
            content_area,
            back_button
        ], spacing=0, expand=True)

    def create_question_result_card(self, question: Dict, student_answer: str, question_num: int, student_answer_data: Dict = None) -> ft.Container:
        """Create a question result card matching the grading page theme"""
        question_type = question.get('question_type', 'mcq')  # Default to mcq
        correct_answer = question.get('correct_answer', '')
        question_points = question.get('points', 1)
        
        # Determine correctness and status
        if question_type == 'mcq':
            # Clean student answer format
            cleaned_student_answer = self.clean_student_answer(student_answer)
            
            # Check if student answer matches correct answer using same logic as grading page
            is_correct = False
            options = question.get('options', [])
            if isinstance(options, str):
                import json
                try:
                    options = json.loads(options)
                except:
                    options = []
            
            for idx, option in enumerate(options):
                option_letter = chr(65 + idx)  # A, B, C, D
                
                # Check if this option is both selected and correct
                is_selected = (
                    cleaned_student_answer == option_letter or
                    cleaned_student_answer == str(idx) or
                    cleaned_student_answer == option or
                    cleaned_student_answer == str(idx + 1)
                )
                
                is_option_correct = (
                    correct_answer == option_letter or
                    correct_answer == str(idx) or
                    correct_answer == option or
                    correct_answer == str(idx + 1)
                )
                
                if is_selected and is_option_correct:
                    is_correct = True
                    break
            
            status_text = "Correct" if is_correct else "Incorrect"
            status_color = ft.Colors.WHITE
            status_bg = "#4CAF50" if is_correct else "#F44336"
        else:  # short_answer or answer_type
            # Check if graded using the actual database data
            if student_answer_data and isinstance(student_answer_data, dict):
                points_earned = student_answer_data.get('points_earned')
                if points_earned is not None:
                    status_text = f"Graded : {points_earned}"
                    status_color = ft.Colors.WHITE
                    status_bg = "#4CAF50"
                else:
                    status_text = "Pending to be graded"
                    status_color = ft.Colors.WHITE
                    status_bg = "#FF9800"  # Orange for pending
            else:
                status_text = "Pending to be graded"
                status_color = ft.Colors.WHITE
                status_bg = "#FF9800"  # Orange for pending

        # Question title - fix the type detection
        question_title = f"{'Multiple Choice' if question_type == 'mcq' else 'Answer Type'} Question #{question_num}"
        
        # Question header matching grading page theme
        question_header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        question_title,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        question.get('question_text', '')[:50] + "..." if len(question.get('question_text', '')) > 50 else question.get('question_text', ''),
                        size=12,
                        color=ft.Colors.WHITE70,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                ], spacing=4, expand=True),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Status", size=11, color=ft.Colors.WHITE70),
                            ft.Container(
                                content=ft.Text(
                                    status_text,
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=status_color
                                ),
                                bgcolor=status_bg,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=8
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=80
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Points", size=11, color=ft.Colors.WHITE70),
                            ft.Text(f"{question_points}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#B85450",
                        border_radius=8,
                        padding=ft.padding.all(8),
                        width=60
                    )
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#D4817A",
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
            padding=ft.padding.all(18)
        )
        
        # Create question content based on type
        if question_type == 'mcq':
            content_area = self.create_mcq_result_display(question, student_answer, correct_answer)
        else:
            content_area = self.create_answer_type_result_display(question, student_answer, student_answer_data)

        return ft.Container(
            content=ft.Column([
                question_header,
                ft.Container(
                    content=content_area,
                    bgcolor="#F8F9FA",
                    padding=ft.padding.all(20),
                    border_radius=ft.border_radius.only(bottom_left=12, bottom_right=12)
                )
            ], spacing=0),
            margin=ft.margin.only(bottom=15),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

    def create_mcq_result_display(self, question: Dict, student_answer: str, correct_answer: str) -> ft.Column:
        """Create MCQ result display matching grading page theme with proper highlighting"""
        options = question.get('options', [])
        if isinstance(options, str):
            import json
            try:
                options = json.loads(options)
            except:
                options = []

        # Clean student answer format
        cleaned_student_answer = self.clean_student_answer(student_answer)
        
        option_displays = []
        for i, option in enumerate(options):
            option_letter = chr(65 + i)  # A, B, C, D
            
            # Check multiple possible formats for student answer (same as grading page)
            is_student_choice = (
                cleaned_student_answer == option_letter or  # Letter format (A, B, C, D)
                cleaned_student_answer == str(i) or         # Index format (0, 1, 2, 3)
                cleaned_student_answer == option or         # Full option text
                cleaned_student_answer == str(i + 1)       # 1-based index (1, 2, 3, 4)
            )
            
            # Check multiple possible formats for correct answer (same as grading page)
            is_correct_answer = (
                correct_answer == option_letter or  # Letter format (A, B, C, D)
                correct_answer == str(i) or         # Index format (0, 1, 2, 3)
                correct_answer == option or         # Full option text
                correct_answer == str(i + 1)       # 1-based index (1, 2, 3, 4)
            )
            
            # Determine styling based on grading page theme (exact same logic)
            if is_student_choice and is_correct_answer:
                # Student selected correct answer - Green with check
                bgcolor = "#4CAF50"
                icon = ft.Icons.CHECK_CIRCLE
                text_color = ft.Colors.WHITE
                border_color = "#4CAF50"
                icon_color = ft.Colors.WHITE
            elif is_student_choice and not is_correct_answer:
                # Student selected wrong answer - Red with X
                bgcolor = "#F44336"
                icon = ft.Icons.CANCEL
                text_color = ft.Colors.WHITE
                border_color = "#F44336"
                icon_color = ft.Colors.WHITE
            elif not is_student_choice and is_correct_answer:
                # Correct answer not selected - Light green outline with check
                bgcolor = "#E8F5E8"
                icon = ft.Icons.CHECK_CIRCLE_OUTLINE
                text_color = "#2E7D32"
                border_color = "#4CAF50"
                icon_color = "#4CAF50"
            else:
                # Not selected, not correct - Light gray background with circle
                bgcolor = "#F8F9FA"
                icon = ft.Icons.CIRCLE_OUTLINED
                text_color = "#666666"
                border_color = "#E0E0E0"
                icon_color = "#999999"

            option_displays.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            icon,
                            size=20,
                            color=icon_color
                        ),
                        ft.Text(
                            f"{option_letter}. {option}",
                            size=14,
                            color=text_color,
                            weight=ft.FontWeight.BOLD if (is_student_choice or is_correct_answer) else ft.FontWeight.NORMAL,
                            expand=True
                        )
                    ], spacing=12),
                    padding=ft.padding.all(15),
                    bgcolor=bgcolor,
                    border=ft.border.all(2, border_color),
                    border_radius=8,
                    margin=ft.margin.only(bottom=8)
                )
            )

        # Add summary text showing student's choice (cleaned format)
        display_student_answer = cleaned_student_answer.upper() if cleaned_student_answer else 'No answer'
        display_correct_answer = correct_answer.upper() if correct_answer else 'N/A'
        summary_text = f"Student selected: {display_student_answer} | Correct answer: {display_correct_answer}"
        
        option_displays.append(
            ft.Container(
                content=ft.Text(
                    summary_text,
                    size=12,
                    color="#666666",
                    style=ft.TextStyle(italic=True)
                ),
                padding=ft.padding.all(10),
                bgcolor="#F0F8F0" if cleaned_student_answer.upper() == correct_answer.upper() else "#FFF0F0",
                border_radius=8,
                margin=ft.margin.only(top=10)
            )
        )

        return ft.Column(option_displays, spacing=0)

    def create_answer_type_result_display(self, question: Dict, student_answer: str, student_answer_data: Dict = None) -> ft.Container:
        """Create answer type result display matching grading page theme"""
        content_items = [
            ft.Text(
                "Student's Answer:",
                size=12,
                weight=ft.FontWeight.BOLD,
                color="#666666"
            ),
            ft.Container(
                content=ft.Text(
                    str(student_answer) if student_answer else "No answer provided",
                    size=13,
                    color=ft.Colors.BLACK87,
                ),
                bgcolor="#F8F9FA",
                border=ft.border.all(1, "#E0E0E0"),
                border_radius=8,
                padding=ft.padding.all(15),
                width=float('inf')
            )
        ]
        
        # Add feedback if available and graded
        if student_answer_data and isinstance(student_answer_data, dict):
            feedback = student_answer_data.get('feedback')
            points_earned = student_answer_data.get('points_earned')
            
            if points_earned is not None and feedback:
                content_items.extend([
                    ft.Text(
                        "Teacher's Feedback:",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#666666"
                    ),
                    ft.Container(
                        content=ft.Text(
                            str(feedback),
                            size=13,
                            color=ft.Colors.BLACK87,
                        ),
                        bgcolor="#FFF8E1",
                        border=ft.border.all(1, "#FFD54F"),
                        border_radius=8,
                        padding=ft.padding.all(15),
                        width=float('inf')
                    )
                ])
        
        return ft.Container(
            content=ft.Column(content_items, spacing=8),
            margin=ft.margin.only(bottom=10)
        )

    def go_back(self, e):
        """Navigate back to Scores page (not the main dashboard)."""
        # Import here to avoid circular imports
        from pages.student_dashboard import StudentDashboard

        # Ensure user_data is stored in page.data for StudentDashboard
        self.page.data = self.user_data

        # Clear views and navigate back to student dashboard Scores tab
        self.page.views.clear()
        student_dashboard = StudentDashboard(self.page, self.db_manager)
        student_dashboard.selected_nav = 4  # Ensure Scores tab is active
        student_dashboard.show_results()
        # Preserve current content; do not force default dashboard load
        self.page.views.append(student_dashboard.get_view_preserve_current())
        self.page.update()

    def get_view(self) -> ft.View:
        """Get the main view for this page"""
        return ft.View(
            "/student-results",
            [
                ft.Container(
                    content=self.create_results_view(),
                    expand=True,
                    bgcolor="#f4f1ec",
                    padding=ft.padding.all(50)
                )
            ],
            bgcolor="#f4f1ec",
            padding=0
        )
