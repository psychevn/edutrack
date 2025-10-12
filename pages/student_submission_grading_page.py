import flet as ft
from datetime import datetime
from database.database_manager import DatabaseManager

class StudentSubmissionGradingPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, assessment_id: int, submission_id: int):
        self.page = page
        self.db_manager = db_manager
        self.assessment_id = assessment_id
        self.submission_id = submission_id
        self.submission_details = None
        self.assessment_details = None
        self.parent_dashboard = None  # Reference to parent dashboard for embedded navigation
        
        # Store references to input fields for score collection
        self.score_inputs = {}  # {answer_index: TextField}
        self.feedback_inputs = {}  # {answer_index: TextField}
        self.question_status_containers = {}  # {question_num: Container} for status updates
        
        # Get user data from page session
        self.user_data = self.page.data if hasattr(self.page, 'data') else None
        
        # Load data
        self.load_submission_data()
        self.load_assessment_data()
        self.init_ui()
        
    def load_submission_data(self):
        """Load submission details and assessment info for grading"""
        try:
            print(f"Loading submission data for ID: {self.submission_id}")
            self.submission_details = self.db_manager.get_submission_details(self.submission_id)
            print(f"Submission found: {self.submission_details.get('student_name') if self.submission_details else 'None'}")
            
            # Also load assessment details
            self.assessment_details = self.db_manager.get_assessment_by_id(self.assessment_id)
            print(f"Assessment found: {self.assessment_details.get('title') if self.assessment_details else 'None'}")
        except Exception as e:
            print(f"Error loading submission data: {e}")
            self.submission_details = None
            self.assessment_details = None
    
    def load_assessment_data(self):
        """Load assessment details - called separately for compatibility"""
        try:
            if not self.assessment_details:
                self.assessment_details = self.db_manager.get_assessment_by_id(self.assessment_id)
                print(f"Assessment loaded: {self.assessment_details.get('title') if self.assessment_details else 'None'}")
        except Exception as e:
            print(f"Error loading assessment data: {e}")
            self.assessment_details = None
    
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
            print(f"Grading Page - User data: {self.user_data}")
            print(f"Grading Page - Profile photo path: {profile_photo_path}")
        
        # Check if photo file exists
        if profile_photo_path and os.path.exists(profile_photo_path):
            print(f"Grading Page - Photo file exists: {profile_photo_path}")
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
            print(f"Grading Page - Using default logo")
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
        print(f"Navigating to {destination} from submission grading")
        
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
    
    def go_back_to_students(self, e=None):
        """Go back to student scores list using direct view manipulation"""
        print(f"Going back to student scores list for assessment {self.assessment_id}")
        # Use direct view manipulation to prevent transitions
        self.page.views.clear()
        from pages.student_scores_list_page import StudentScoresListPage
        scores_list_page = StudentScoresListPage(self.page, self.db_manager, self.assessment_id)
        self.page.views.append(scores_list_page.build())
        self.page.update()
    
    def finalize_grade(self, e=None):
        """Collect scores from interface and finalize the grade for current submission"""
        if not self.submission_id or not self.submission_details:
            # Use overlay to show error message
            error_snack = ft.SnackBar(
                content=ft.Text("Error: No submission data found", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED
            )
            self.page.overlay.append(error_snack)
            error_snack.open = True
            self.page.update()
            return
        
        try:
            # Get answers from submission details
            answers = self.submission_details.get('answers', [])
            if isinstance(answers, str):
                import json
                answers = json.loads(answers)
            
            total_earned_score = 0
            total_possible_score = 0
            updated_answers = []
            
            # Process each answer
            for i, answer in enumerate(answers):
                question_num = i + 1
                question_type = answer.get('question_type', 'mcq')
                max_points = answer.get('points', 1)
                
                if question_type == 'mcq':
                    # Auto-grade MCQ questions using enhanced comparison logic
                    student_answer = answer.get('student_answer', '')
                    correct_answer = answer.get('correct_answer', '')
                    
                    # Clean student answer format
                    student_answer = self.clean_student_answer(student_answer)
                    
                    # Check if student answer matches correct answer in any format
                    is_correct = False
                    options = answer.get('options', [])
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
                            student_answer == option_letter or
                            student_answer == str(idx) or
                            student_answer == option or
                            student_answer == str(idx + 1)
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
                    
                    earned_score = max_points if is_correct else 0
                    
                    answer['points_earned'] = earned_score
                    answer['is_graded'] = True
                    
                    print(f"DEBUG: MCQ Question {question_num}: {earned_score}/{max_points} points (auto-graded) - Student: '{student_answer}', Correct: '{correct_answer}', Match: {is_correct}")
                else:
                    # Manual grading for answer-type questions
                    earned_score = 0
                    
                    # Get score from input field if available
                    if question_num in self.score_inputs:
                        try:
                            score_value = self.score_inputs[question_num].value or "0"
                            earned_score = float(score_value)
                            earned_score = max(0, min(earned_score, max_points))  # Clamp between 0 and max
                        except ValueError:
                            print(f"DEBUG: Invalid score value for question {question_num}: {score_value}")
                            earned_score = 0
                    
                    # Get feedback from input field if available
                    feedback = ""
                    if question_num in self.feedback_inputs:
                        feedback = self.feedback_inputs[question_num].value or ""
                    
                    answer['points_earned'] = earned_score
                    answer['feedback'] = feedback
                    answer['is_graded'] = True
                    
                    print(f"DEBUG: Answer Question {question_num}: {earned_score}/{max_points} points (manual)")
                
                total_earned_score += earned_score
                total_possible_score += max_points
                updated_answers.append(answer)
            
            print(f"DEBUG: Final scores - Earned: {total_earned_score}, Possible: {total_possible_score}")
            print(f"DEBUG: Updated answers summary:")
            for i, ans in enumerate(updated_answers):
                print(f"  Question {i+1}: {ans.get('points_earned', 0)}/{ans.get('points', 1)} points, graded: {ans.get('is_graded', False)}")
            
            # Update submission in database
            success = self.db_manager.update_submission_grade(
                self.submission_id, 
                total_earned_score, 
                total_possible_score,
                updated_answers
            )
            
            print(f"DEBUG: Database update success: {success}")
            
            if success:
                # Show success notification
                success_snack = ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE),
                        ft.Text(f"Grade finalized successfully! Score: {total_earned_score}/{total_possible_score}", 
                                color=ft.Colors.WHITE, size=16)
                    ], spacing=10),
                    bgcolor=ft.Colors.GREEN
                )
                self.page.overlay.append(success_snack)
                success_snack.open = True
                self.page.update()
                
                # Stay on the grading page - admin can navigate back manually if needed
            else:
                error_snack = ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.WHITE),
                        ft.Text("Error saving grade to database", color=ft.Colors.WHITE)
                    ], spacing=10),
                    bgcolor=ft.Colors.RED
                )
                self.page.overlay.append(error_snack)
                error_snack.open = True
                self.page.update()
                
        except Exception as ex:
            print(f"ERROR in finalize_grade: {ex}")
            error_snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.WHITE),
                    ft.Text(f"Error finalizing grade: {str(ex)}", color=ft.Colors.WHITE)
                ], spacing=10),
                bgcolor=ft.Colors.RED
            )
            self.page.overlay.append(error_snack)
            error_snack.open = True
            self.page.update()
    
    def create_assessment_info_header(self):
        """Create enhanced assessment info header with score display"""
        if not self.assessment_details:
            return ft.Container()
        
        # Calculate student's current earned score and total possible score
        current_earned_score = 0
        total_possible_score = 0
        
        if self.submission_details and 'answers' in self.submission_details:
            answers = self.submission_details['answers']
            if isinstance(answers, str):
                import json
                try:
                    answers = json.loads(answers)
                except:
                    answers = []
            
            for i, answer in enumerate(answers):
                question_num = i + 1
                max_points = answer.get('points', 1)
                total_possible_score += max_points
                
                # Calculate current earned score
                question_type = answer.get('question_type', 'mcq')
                if question_type == 'mcq':
                    # Auto-calculate MCQ score - only count if correct
                    student_answer = answer.get('student_answer', '')
                    correct_answer = answer.get('correct_answer', '')
                    
                    # Clean student answer format
                    student_answer = self.clean_student_answer(student_answer)
                    
                    # Check if student answer matches correct answer in any format
                    is_correct = False
                    options = answer.get('options', [])
                    if isinstance(options, str):
                        import json
                        try:
                            options = json.loads(options)
                        except:
                            options = []
                    
                    for i, option in enumerate(options):
                        option_letter = chr(65 + i)  # A, B, C, D
                        
                        # Check if this option is both selected and correct
                        is_selected = (
                            student_answer == option_letter or
                            student_answer == str(i) or
                            student_answer == option or
                            student_answer == str(i + 1)
                        )
                        
                        is_option_correct = (
                            correct_answer == option_letter or
                            correct_answer == str(i) or
                            correct_answer == option or
                            correct_answer == str(i + 1)
                        )
                        
                        if is_selected and is_option_correct:
                            is_correct = True
                            break
                    
                    earned_points = max_points if is_correct else 0
                    current_earned_score += earned_points
                else:
                    # For answer-type questions, get score from input field or existing data
                    if question_num in self.score_inputs:
                        try:
                            score_value = self.score_inputs[question_num].value or "0"
                            earned_points = float(score_value)
                            earned_points = max(0, min(earned_points, max_points))
                            current_earned_score += earned_points
                        except ValueError:
                            # Use existing points_earned if input is invalid
                            current_earned_score += answer.get('points_earned', 0)
                    else:
                        # Use existing points_earned
                        current_earned_score += answer.get('points_earned', 0)
        
        # Store the score display container for updates
        self.score_display_container = ft.Container(
            content=ft.Column([
                ft.Text("Current Score", size=12, color=ft.Colors.GREY_600),
                ft.Text(f"{current_earned_score:.1f}/{total_possible_score}", size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
                ft.Text(f"{(current_earned_score/total_possible_score*100):.1f}%" if total_possible_score > 0 else "0%", 
                        size=12, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#F5F5F5",
            border_radius=8,
            padding=ft.padding.all(12),
            width=120
        )
        
        return ft.Container(
            content=ft.Column([
                # Title and Score Row
                ft.Row([
                    ft.Column([
                        ft.Text(
                            self.assessment_details.get('title', 'Assessment'),
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color="#D4817A"
                        ),
                        ft.Text(
                            self.assessment_details.get('description', 'No description available'),
                            size=14,
                            color=ft.Colors.GREY_700,
                            max_lines=3
                        )
                    ], expand=True),
                    self.score_display_container
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),  # Spacing
                ft.Divider(color="#E0E0E0", height=1)
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            margin=ft.margin.only(bottom=20),
            border=ft.border.all(1, "#E0E0E0")
        )
    
    def grade_individual_question(self, question_num: int):
        """Grade an individual answer-type question"""
        try:
            if not self.submission_details or 'answers' not in self.submission_details:
                return
            
            answers = self.submission_details['answers']
            if isinstance(answers, str):
                import json
                try:
                    answers = json.loads(answers)
                except:
                    return
            
            # Find the specific answer
            if question_num - 1 >= len(answers):
                return
            
            answer = answers[question_num - 1]
            question_type = answer.get('question_type', 'mcq')
            
            # Only grade answer-type questions individually
            if question_type == 'mcq':
                return
            
            # Get score from input field
            earned_score = 0
            if question_num in self.score_inputs:
                try:
                    score_value = self.score_inputs[question_num].value or "0"
                    earned_score = float(score_value)
                    max_points = answer.get('points', 1)
                    earned_score = max(0, min(earned_score, max_points))  # Clamp between 0 and max
                except ValueError:
                    earned_score = 0
            
            # Get feedback from input field
            feedback = ""
            if question_num in self.feedback_inputs:
                feedback = self.feedback_inputs[question_num].value or ""
            
            # Update the answer data
            answer['points_earned'] = earned_score
            answer['feedback'] = feedback
            answer['is_graded'] = True
            
            # Update the submission details
            self.submission_details['answers'] = answers
            
            # Save the individual question grade to database
            try:
                # Calculate total scores for database update
                total_earned_score = 0
                total_possible_score = 0
                
                for ans in answers:
                    max_points = ans.get('points', 1)
                    total_possible_score += max_points
                    
                    question_type = ans.get('question_type', 'mcq')
                    if question_type == 'mcq':
                        # Auto-calculate MCQ score
                        student_ans = ans.get('student_answer', '')
                        correct_ans = ans.get('correct_answer', '')
                        
                        # Clean student answer format
                        student_ans = self.clean_student_answer(student_ans)
                        
                        # Check if student answer matches correct answer in any format
                        is_correct = False
                        options = ans.get('options', [])
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
                                student_ans == option_letter or
                                student_ans == str(idx) or
                                student_ans == option or
                                student_ans == str(idx + 1)
                            )
                            
                            is_option_correct = (
                                correct_ans == option_letter or
                                correct_ans == str(idx) or
                                correct_ans == option or
                                correct_ans == str(idx + 1)
                            )
                            
                            if is_selected and is_option_correct:
                                is_correct = True
                                break
                        
                        earned_points = max_points if is_correct else 0
                        total_earned_score += earned_points
                    else:
                        # Use graded score for answer-type questions
                        total_earned_score += ans.get('points_earned', 0)
                
                # Update submission in database with current progress
                success = self.db_manager.update_submission_grade(
                    self.submission_id, 
                    total_earned_score, 
                    total_possible_score,
                    answers
                )
                
                if not success:
                    print(f"Warning: Failed to save individual grade to database")
                
            except Exception as db_error:
                print(f"Error saving individual grade to database: {db_error}")
            
            # Reload submission data to get updated grading status
            self.load_submission_data()
            
            # Update the status container for this question
            if question_num in self.question_status_containers:
                status_container = self.question_status_containers[question_num]
                status_container.content = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                    ft.Text("Graded", size=12, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
                ], spacing=5)
                status_container.bgcolor = ft.Colors.GREEN_50
            
            # Update score display
            self.update_score_display()
            
            # Refresh the entire page content to reflect graded status
            self.page.views.clear()
            self.page.views.append(self.build())
            
            # Show success notification
            success_snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE),
                    ft.Text(f"Question {question_num} graded successfully! Score: {earned_score}/{answer.get('points', 1)}", 
                            color=ft.Colors.WHITE, size=14)
                ], spacing=10),
                bgcolor=ft.Colors.GREEN
            )
            self.page.overlay.append(success_snack)
            success_snack.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Error grading individual question {question_num}: {e}")
            error_snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.WHITE),
                    ft.Text(f"Error grading question {question_num}", color=ft.Colors.WHITE)
                ], spacing=10),
                bgcolor=ft.Colors.RED
            )
            self.page.overlay.append(error_snack)
            error_snack.open = True
            self.page.update()

    def clean_student_answer(self, student_answer):
        """Clean student answer by removing quotes, brackets, and extra formatting"""
        if not student_answer:
            return student_answer
        
        student_answer = student_answer.strip()
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

    def update_score_display(self):
        """Update the score display in the header when scores change"""
        if not hasattr(self, 'score_display_container') or not self.score_display_container:
            return
            
        # Recalculate current score
        current_earned_score = 0
        total_possible_score = 0
        
        if self.submission_details and 'answers' in self.submission_details:
            answers = self.submission_details['answers']
            if isinstance(answers, str):
                import json
                try:
                    answers = json.loads(answers)
                except:
                    answers = []
            
            for i, answer in enumerate(answers):
                question_num = i + 1
                max_points = answer.get('points', 1)
                total_possible_score += max_points
                
                # Calculate current earned score
                question_type = answer.get('question_type', 'mcq')
                if question_type == 'mcq':
                    # Auto-calculate MCQ score - only count if correct
                    student_answer = answer.get('student_answer', '')
                    correct_answer = answer.get('correct_answer', '')
                    
                    # Clean student answer format
                    student_answer = self.clean_student_answer(student_answer)
                    
                    # Check if student answer matches correct answer in any format
                    is_correct = False
                    options = answer.get('options', [])
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
                            student_answer == option_letter or
                            student_answer == str(idx) or
                            student_answer == option or
                            student_answer == str(idx + 1)
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
                    
                    earned_points = max_points if is_correct else 0
                    current_earned_score += earned_points
                else:
                    # For answer-type questions, get score from input field
                    if question_num in self.score_inputs:
                        try:
                            score_value = self.score_inputs[question_num].value or "0"
                            earned_points = float(score_value)
                            earned_points = max(0, min(earned_points, max_points))
                            current_earned_score += earned_points
                        except ValueError:
                            current_earned_score += answer.get('points_earned', 0)
                    else:
                        current_earned_score += answer.get('points_earned', 0)
        
        # Update the score display
        self.score_display_container.content = ft.Column([
            ft.Text("Current Score", size=12, color=ft.Colors.GREY_600),
            ft.Text(f"{current_earned_score:.1f}/{total_possible_score}", size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
            ft.Text(f"{(current_earned_score/total_possible_score*100):.1f}%" if total_possible_score > 0 else "0%", 
                    size=12, color=ft.Colors.GREY_600)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Update the page
        self.page.update()
    
    def create_header(self):
        """Create page header with student info and back button"""
        if not self.submission_details:
            return ft.Container(
                content=ft.Text("Submission not found", color=ft.Colors.RED),
                padding=ft.padding.all(20)
            )
        
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#D4817A",
                    icon_size=24,
                    on_click=self.go_back_to_students
                ),
                ft.Text("Back", size=14, color="#D4817A"),
                ft.Container(expand=True),
                ft.Text(
                    f"{self.submission_details.get('student_number', 'N/A')} - {self.submission_details.get('student_name', 'Unknown')}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color="#D4817A",
                ),
                ft.Text(
                    f"Score: {self.submission_details.get('total_score', '___')}",
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
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            margin=ft.margin.only(bottom=10)
        )
    
    def create_question_card(self, answer: dict, question_num: int) -> ft.Control:
        """Create individual question card for grading"""
        question_type = answer.get('question_type', 'mcq')
        is_mcq = question_type == 'mcq'
        
        # Enhanced question header with better styling
        question_points = answer.get('points', 1)
        question_header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        f"Question {question_num}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        answer.get('question_text', 'Question text not available'),
                        size=13,
                        color=ft.Colors.WHITE,
                        max_lines=4
                    )
                ], expand=True, spacing=8),
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
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#D4817A",
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
            padding=ft.padding.all(18)
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
            student_answer = answer.get('student_answer', '')
            correct_answer = answer.get('correct_answer', '')
            
            # Clean student answer - remove quotes, brackets, and extra formatting
            student_answer = self.clean_student_answer(student_answer)
            
            print(f"DEBUG MCQ - Original student answer: '{answer.get('student_answer', '')}', Cleaned: '{student_answer}', Correct answer: '{correct_answer}'")
            print(f"DEBUG MCQ - Options: {options}")
            
            for i, option in enumerate(options):
                option_letter = chr(65 + i)  # A, B, C, D
                
                # Check multiple possible formats for student answer
                is_selected = (
                    student_answer == option_letter or  # Letter format (A, B, C, D)
                    student_answer == str(i) or         # Index format (0, 1, 2, 3)
                    student_answer == option or         # Full option text
                    student_answer == str(i + 1)       # 1-based index (1, 2, 3, 4)
                )
                
                # Check multiple possible formats for correct answer
                is_correct = (
                    correct_answer == option_letter or  # Letter format (A, B, C, D)
                    correct_answer == str(i) or         # Index format (0, 1, 2, 3)
                    correct_answer == option or         # Full option text
                    correct_answer == str(i + 1)       # 1-based index (1, 2, 3, 4)
                )
                
                print(f"DEBUG MCQ - Option {option_letter} ({option}): selected={is_selected}, correct={is_correct}")
                
                # Determine colors and icons based on selection and correctness
                if is_selected and is_correct:
                    # Student selected correct answer - Green with check
                    bgcolor = "#4CAF50"
                    icon = ft.Icons.CHECK_CIRCLE
                    text_color = ft.Colors.WHITE
                    border_color = "#4CAF50"
                    icon_color = ft.Colors.WHITE
                elif is_selected and not is_correct:
                    # Student selected wrong answer - Red with X
                    bgcolor = "#F44336"
                    icon = ft.Icons.CANCEL
                    text_color = ft.Colors.WHITE
                    border_color = "#F44336"
                    icon_color = ft.Colors.WHITE
                elif not is_selected and is_correct:
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
                
                option_control = ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            icon, 
                            size=20, 
                            color=icon_color
                        ),
                        ft.Text(
                            f"{option_letter}. {option}", 
                            size=13, 
                            color=text_color, 
                            weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
                        ),
                    ], spacing=12, alignment=ft.MainAxisAlignment.START),
                    bgcolor=bgcolor,
                    border_radius=8,
                    padding=ft.padding.all(15),
                    margin=ft.margin.only(bottom=8),
                    border=ft.border.all(2, border_color),
                    width=float('inf')
                )
                option_controls.append(option_control)
            
            question_content.extend(option_controls)
            
            # Show answer summary
            is_correct_answer = student_answer == correct_answer
            question_content.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(
                            f"Student Answer: {student_answer or 'No answer'}",
                            size=12,
                            color="#4CAF50" if is_correct_answer else "#F44336",
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(width=20),
                        ft.Text(
                            f"Correct Answer: {correct_answer}",
                            size=12,
                            color="#4CAF50",
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(expand=True),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if is_correct_answer else ft.Icons.CANCEL,
                            color="#4CAF50" if is_correct_answer else "#F44336",
                            size=20
                        )
                    ]),
                    padding=ft.padding.all(10),
                    bgcolor="#F0F8F0" if is_correct_answer else "#FFF0F0",
                    border_radius=8,
                    margin=ft.margin.only(top=10)
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
            
        else:
            # Answer-type question with enhanced grading interface
            current_score = answer.get('points_earned', 0)
            max_points = answer.get('points', 1)
            # Determine if graded based on whether points_earned is not None or has feedback
            is_graded = (current_score is not None) or bool(answer.get('feedback', '').strip())
            
            # Status indicator - store reference for updates
            status_container = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.PENDING if not is_graded else ft.Icons.CHECK_CIRCLE,
                        color=ft.Colors.ORANGE if not is_graded else ft.Colors.GREEN,
                        size=16
                    ),
                    ft.Text(
                        "Pending Review" if not is_graded else "Graded",
                        size=12,
                        color=ft.Colors.ORANGE if not is_graded else ft.Colors.GREEN,
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=5),
                bgcolor=ft.Colors.ORANGE_50 if not is_graded else ft.Colors.GREEN_50,
                border_radius=15,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                margin=ft.margin.only(bottom=15)
            )
            # Store reference for status updates
            self.question_status_containers[question_num] = status_container
            question_content.append(status_container)
            
            # Student answer display
            question_content.append(
                ft.Text(
                    "Student Answer:",
                    size=13,
                    color="#D4817A",
                    weight=ft.FontWeight.BOLD,
                )
            )
            question_content.append(
                ft.Container(
                    content=ft.Text(
                        answer.get('student_answer') or "No answer provided",
                        size=13,
                        color=ft.Colors.BLACK87,
                    ),
                    bgcolor="#F8F9FA",
                    border=ft.border.all(1, "#E0E0E0"),
                    border_radius=8,
                    padding=ft.padding.all(15),
                    width=float('inf'),
                    margin=ft.margin.only(bottom=15)
                )
            )
            
            # Enhanced scoring section with individual grade button
            score_section = ft.Container(
                content=ft.Column([
                    ft.Text("Grading", size=13, color="#D4817A", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("Score:", size=12, color="#666"),
                        (score_input := ft.TextField(
                            value=str(current_score),
                            width=70,
                            height=40,
                            text_size=13,
                            border_color="#D4817A",
                            data=question_num,  # Use question number as identifier
                            text_align=ft.TextAlign.CENTER,
                            on_change=lambda e: self.update_score_display()  # Update score when changed
                        )),
                        ft.Text(f"/ {max_points}", size=12, color="#666"),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            content=ft.Text("Grade", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            bgcolor="#8BC34A",
                            color=ft.Colors.WHITE,
                            width=60,
                            height=35,
                            on_click=lambda e, qnum=question_num: self.grade_individual_question(qnum),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8)
                            )
                        ) if not is_graded else ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                                ft.Text("Graded", size=11, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
                            ], spacing=5),
                            width=60,
                            height=35,
                            alignment=ft.alignment.center
                        )
                    ], alignment=ft.MainAxisAlignment.START, spacing=10),
                    ft.Row([
                        ft.Container(expand=True),
                        ft.Text(f"{(current_score/max_points*100):.1f}%" if max_points > 0 else "0%", 
                                size=12, color="#D4817A", weight=ft.FontWeight.BOLD)
                    ])
                ], spacing=8),
                bgcolor="#F5F5F5",
                border_radius=8,
                padding=ft.padding.all(12),
                margin=ft.margin.only(bottom=15)
            )
            question_content.append(score_section)
            
            # Comment section
            question_content.append(
                ft.Text(
                    "Feedback:",
                    size=13,
                    color="#D4817A",
                    weight=ft.FontWeight.BOLD,
                )
            )
            # Store reference to score input
            self.score_inputs[question_num] = score_input
            
            # Feedback field
            feedback_input = ft.TextField(
                value=answer.get('feedback') or "",
                multiline=True,
                min_lines=3,
                max_lines=5,
                border_color="#D4817A",
                text_size=12,
                data=question_num,  # Use question number as identifier
                hint_text="Provide feedback for the student's answer..."
            )
            
            # Store reference to feedback input
            self.feedback_inputs[question_num] = feedback_input
            
            question_content.append(feedback_input)
        
        return ft.Container(
            content=ft.Column([
                question_header,
                ft.Container(
                    content=ft.Column(question_content, spacing=12),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.WHITE,
                ),
            ], spacing=0),
            border=ft.border.all(1, "#E0E0E0"),
            border_radius=12,
            margin=ft.margin.only(bottom=20)
        )
    
    def create_grading_interface(self):
        """Create the main grading interface"""
        if not self.submission_details:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_400),
                    ft.Text("Submission not found", size=18, color=ft.Colors.RED_600),
                    ft.Text("The requested submission could not be loaded", size=14, color=ft.Colors.RED_500)
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                height=400
            )
        
        # Questions and answers
        questions_column = []
        answers = self.submission_details.get('answers', [])
        
        if not answers:
            questions_column.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.QUIZ, size=64, color=ft.Colors.GREY_400),
                        ft.Text("No answers found for this submission", size=18, color=ft.Colors.GREY_600),
                        ft.Text("The student may not have submitted any answers", size=14, color=ft.Colors.GREY_500)
                    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.all(50),
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    height=300
                )
            )
        else:
            for i, answer in enumerate(answers):
                question_card = self.create_question_card(answer, i + 1)
                questions_column.append(question_card)
            
            # Add Grade button at the bottom
            grade_button_section = ft.Container(
                content=ft.Column([
                    ft.Divider(color="#D4817A", height=2),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.GRADE, color=ft.Colors.WHITE),
                                ft.Text("Finalize Grade", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD)
                            ], spacing=8),
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            width=200,
                            height=50,
                            on_click=self.finalize_grade,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=25)
                            )
                        ),
                        ft.Container(expand=True)
                    ]),
                    ft.Container(height=10),
                    ft.Text(
                        "Click to save all scores and update the submission status",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], spacing=5),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=ft.padding.all(20),
                margin=ft.margin.only(top=20, bottom=10),
                border=ft.border.all(1, "#E0E0E0")
            )
            questions_column.append(grade_button_section)
        
        return ft.Container(
            content=ft.ListView(
                controls=questions_column,
                spacing=15,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.all(10),
            bgcolor="#f4f1ec"
        )
    
    def build(self):
        """Build the complete page"""
        try:
            return ft.View(
                "/admin/student-submission-grading",
                [
                    ft.Row([
                        self.sidebar,
                        ft.Container(
                            content=ft.Column([
                                self.create_assessment_info_header(),
                                self.create_header(),
                                self.create_grading_interface()
                            ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
                            padding=ft.padding.all(20),
                            expand=True,
                            bgcolor="#f4f1ec"
                        )
                    ], spacing=0, expand=True)
                ],
                padding=0,
                bgcolor="#f4f1ec"
            )
        except Exception as e:
            print(f"❌ Error building submission grading page: {e}")
            # Return a simple error view
            return ft.View(
                "/admin/student-submission-grading",
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Error loading submission grading", size=18, color=ft.Colors.RED),
                            ft.Text(f"Details: {str(e)}", size=12, color=ft.Colors.GREY)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(50),
                        alignment=ft.alignment.center
                    )
                ],
                padding=0,
                bgcolor="#f4f1ec"
            )
