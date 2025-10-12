import flet as ft
from pages.role_selection import RoleSelectionPage
from pages.admin_login import AdminLoginPage
from pages.student_login import StudentLoginPage
from pages.admin_registration import AdminRegistrationPage
from pages.student_registration import StudentRegistrationPage
from pages.password_recovery import PasswordRecoveryPage
from pages.admin_dashboard import AdminDashboard
from pages.student_dashboard import StudentDashboard
from pages.assessment_management import AssessmentManagementPage
from pages.create_assessment import CreateAssessmentPage
from pages.admin_user_page import AdminUserPage
from pages.student_posts_page import StudentPostsPage
from pages.student_user_page import StudentUserPage
from pages.scores_page import ScoresPage
from pages.student_scores_list_page import StudentScoresListPage
from pages.student_submission_grading_page import StudentSubmissionGradingPage
from database.database_manager import DatabaseManager
import os

def main(page: ft.Page):
    # Configure page properties
    page.title = "Assessment Management System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1350
    page.window.height = 900
    page.window.resizable = True
    page.padding = 0
    
    # Global font: Poppins
    page.fonts = {
        "Poppins": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
        "Poppins-SemiBold": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
        "Poppins-Bold": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    }
    
    # Set theme with font family
    page.theme = ft.Theme(font_family="Poppins")
    
    # Disable page transition Animations completely
    page.page_transition_duration = 0
    page.route_change_animation = None
    page.view_pop_animation = None
    
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Set up routing
    def route_change(route):
        # Clear views only if we're actually changing routes
        page.views.clear()
        
        print(f"Navigating to route: {page.route}")
        
        try:
            if page.route == "/":
                role_selection = RoleSelectionPage(page, db_manager)
                page.views.append(role_selection.get_view())
            elif page.route == "/admin-login":
                admin_login = AdminLoginPage(page, db_manager)
                page.views.append(admin_login.get_view())
            elif page.route == "/student-login":
                student_login = StudentLoginPage(page, db_manager)
                page.views.append(student_login.get_view())
            elif page.route == "/admin-registration":
                admin_registration = AdminRegistrationPage(page, db_manager)
                page.views.append(admin_registration.get_view())
            elif page.route == "/student-registration":
                student_registration = StudentRegistrationPage(page, db_manager)
                page.views.append(student_registration.get_view())
            elif page.route == "/password-recovery":
                password_recovery = PasswordRecoveryPage(page, db_manager)
                page.views.append(password_recovery.get_view())
            elif page.route == "/admin":
                admin_dashboard = AdminDashboard(page, db_manager)
                page.views.append(admin_dashboard.get_view())
            elif page.route == "/admin-user":
                admin_user_page = AdminUserPage(page, db_manager)
                page.views.append(admin_user_page.get_view())
            elif page.route == "/admin-assessments":
                assessment_management = AssessmentManagementPage(page, db_manager)
                page.views.append(assessment_management.get_view())
            elif page.route == "/admin-scores":
                scores_page = ScoresPage(page, db_manager)
                page.views.append(scores_page.get_view())
            elif page.route.startswith("/admin/student-scores-list/"):
                # Extract assessment ID from route
                print(f"DEBUG: Processing student scores list route: {page.route}")
                try:
                    assessment_id = int(page.route.split("/")[-1])
                    print(f"DEBUG: Extracted assessment_id: {assessment_id}")
                    student_scores_list = StudentScoresListPage(page, db_manager, assessment_id)
                    page.views.append(student_scores_list.build())
                    print(f"DEBUG: Student scores list page created successfully")
                except Exception as e:
                    print(f"DEBUG: Error creating student scores list page: {e}")
                    import traceback
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            elif page.route.startswith("/admin/student-scores/") and "/submission/" in page.route:
                # Extract assessment ID and submission ID from route
                print(f"DEBUG: Processing grading route: {page.route}")
                try:
                    parts = page.route.split("/")
                    assessment_id = int(parts[-3])
                    submission_id = int(parts[-1])
                    print(f"DEBUG: Extracted assessment_id: {assessment_id}, submission_id: {submission_id}")
                    submission_grading = StudentSubmissionGradingPage(page, db_manager, assessment_id, submission_id)
                    page.views.append(submission_grading.build())
                    print(f"DEBUG: Grading page created successfully")
                except Exception as e:
                    print(f"DEBUG: Error creating grading page: {e}")
                    import traceback
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            elif page.route == "/create-assessment":
                create_assessment = CreateAssessmentPage(page, db_manager, [])
                page.views.append(create_assessment.get_view())
            elif page.route == "/student":
                student_dashboard = StudentDashboard(page, db_manager)
                page.views.append(student_dashboard.get_view())
            elif page.route == "/student-posts":
                student_posts_page = StudentPostsPage(page, db_manager)
                page.views.append(student_posts_page.get_view())
            elif page.route == "/student-user":
                student_user_page = StudentUserPage(page, db_manager)
                page.views.append(student_user_page.get_view())
            else:
                # Default to role selection page
                role_selection = RoleSelectionPage(page, db_manager)
                page.views.append(role_selection.get_view())
        except Exception as e:
            print(f"Error in route_change: {e}")
            # Fallback to role selection on error
            try:
                role_selection = RoleSelectionPage(page, db_manager)
                page.views.append(role_selection.get_view())
            except Exception as e2:
                print(f"Error in fallback route: {e2}")
        
        page.update()
    
    def view_pop(view):
        try:
            # Only pop if there are views to pop
            if len(page.views) > 1:
                page.views.pop()
                if len(page.views) > 0:
                    top_view = page.views[-1]
                    if hasattr(top_view, 'route'):
                        page.go(top_view.route)
                    else:
                        page.go("/")
                else:
                    page.go("/")
            elif len(page.views) == 1:
                # If only one view, go to home
                page.go("/")
            else:
                # If no views, go to home
                page.go("/")
        except Exception as e:
            print(f"Error in view_pop: {e}")
            # Fallback to home page
            page.go("/")
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Start with role selection page
    page.go("/")

if __name__ == "__main__":
    # Change to the correct directory to ensure imports work
    import os
    import sys
    
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add the script directory to Python path
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # Change to the script directory
        os.chdir(script_dir)
        
        print(f"Starting Assessment Management System from: {script_dir}")
        print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths
        print(f"Current working directory: {os.getcwd()}")
        
        ft.app(target=main)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
