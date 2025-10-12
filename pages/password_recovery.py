import flet as ft
from database.database_manager import DatabaseManager

class PasswordRecoveryPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.current_step = 1  # 1: Enter username/email, 2: Answer security question, 3: Set new password
        self.user_data = None
        
        # Step 1: Username/Email input
        self.username_field = ft.TextField(
            label="Username or Email",
            prefix_icon=ft.Icons.PERSON,
            border_radius=15,
            border_color="#cfc6b5",
            focused_border_color="#bb5862",
            width=350,
            hint_text="Enter your username or email address",
            on_change=self.on_username_change
        )
        
        # Step 2: Security question
        self.security_question_text = ft.Text(
            "",
            size=16,
            weight=ft.FontWeight.BOLD,
            color="#1f2937",
            text_align=ft.TextAlign.CENTER
        )
        
        self.security_answer_field = ft.TextField(
            label="Your Answer",
            prefix_icon=ft.Icons.KEY,
            border_radius=15,
            border_color="#cfc6b5",
            focused_border_color="#bb5862",
            width=350
        )
        
        # Step 3: New password
        self.new_password_field = ft.TextField(
            label="New Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=15,
            border_color="#cfc6b5",
            focused_border_color="#bb5862",
            width=350
        )
        
        self.confirm_password_field = ft.TextField(
            label="Confirm New Password",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=15,
            border_color="#cfc6b5",
            focused_border_color="#bb5862",
            width=350
        )
        
        # Error message
        self.error_message = ft.Text(
            "",
            color=ft.Colors.RED_400,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )
        
        # Success message
        self.success_message = ft.Text(
            "",
            color=ft.Colors.GREEN_400,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )
        
        # Buttons
        self.next_button = ft.ElevatedButton(
            "Next",
            icon=ft.Icons.ARROW_FORWARD,
            style=ft.ButtonStyle(
                bgcolor="#bb5862",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=25),
                padding=ft.padding.symmetric(horizontal=30, vertical=14)
            ),
            on_click=self.handle_next,
            width=350
        )
        
        self.back_button = ft.TextButton(
            "← Back to Login",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(
                color="#bb5862"
            ),
            on_click=self.go_back
        )
        
        self.reset_button = ft.ElevatedButton(
            "Reset Password",
            icon=ft.Icons.KEY,
            style=ft.ButtonStyle(
                bgcolor="#bb5862",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=25),
                padding=ft.padding.symmetric(horizontal=30, vertical=14)
            ),
            on_click=self.handle_reset_password,
            width=350
        )
        
        # Initialize step indicators
        self.step1_indicator = None
        self.step2_indicator = None
        self.step3_indicator = None
        
        # Initialize step containers
        self.step1_container = None
        self.step2_container = None
        self.step3_container = None
        
        # Initialize button containers
        self.next_button_container = None
        self.reset_button_container = None
    
    def _create_step_indicator(self, step_num):
        """Create a step indicator container"""
        indicator = ft.Container(
            content=ft.Text(str(step_num), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor="#bb5862" if self.current_step >= step_num else ft.Colors.GREY_400,
            width=40,
            height=40,
            border_radius=20,
            alignment=ft.alignment.center
        )
        
        # Store reference for later updates
        if step_num == 1:
            self.step1_indicator = indicator
        elif step_num == 2:
            self.step2_indicator = indicator
        elif step_num == 3:
            self.step3_indicator = indicator
            
        return indicator
    
    def _create_step1_container(self):
        """Create step 1 container"""
        self.step1_container = ft.Container(
            content=self.username_field,
            visible=self.current_step == 1
        )
        return self.step1_container
    
    def _create_step2_container(self):
        """Create step 2 container"""
        self.step2_container = ft.Container(
            content=ft.Column([
                self.security_question_text,
                ft.Container(height=20),
                self.security_answer_field
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            visible=self.current_step == 2
        )
        return self.step2_container
    
    def _create_step3_container(self):
        """Create step 3 container"""
        self.step3_container = ft.Container(
            content=ft.Column([
                self.new_password_field,
                self.confirm_password_field
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            visible=self.current_step == 3
        )
        return self.step3_container
    
    def _create_next_button_container(self):
        """Create next button container"""
        self.next_button_container = ft.Container(
            content=self.next_button,
            visible=self.current_step in [1, 2]
        )
        return self.next_button_container
    
    def _create_reset_button_container(self):
        """Create reset button container"""
        self.reset_button_container = ft.Container(
            content=self.reset_button,
            visible=self.current_step == 3
        )
        return self.reset_button_container
    
    def on_username_change(self, e):
        """Handle username field change"""
        pass  # This ensures the field value is properly tracked
    
    def handle_next(self, e):
        """Handle next button click"""
        if self.current_step == 1:
            self.handle_username_step()
        elif self.current_step == 2:
            self.handle_security_question_step()
    
    def handle_username_step(self):
        """Handle step 1: username/email verification"""
        # Force update to get the latest value
        self.page.update()
        username = self.username_field.value.strip()
        print(f"Username entered: '{username}'")  # Debug
        
        if not username:
            self.show_error("Please enter your username or email")
            return
        
        print("Attempting to get user data...")  # Debug
        
        try:
            # Get user data - with proper error handling
            user_data = None
            
            # Check if the method exists
            if hasattr(self.db_manager, 'get_user_by_username_or_email'):
                print("Using get_user_by_username_or_email method")
                user_data = self.db_manager.get_user_by_username_or_email(username)
            else:
                print("Method get_user_by_username_or_email not found!")
                print("Available methods:", [m for m in dir(self.db_manager) if not m.startswith('_')])
                self.show_error("Database method not available. Please contact administrator.")
                return
            
            print(f"User data result: {user_data}")  # Debug
            
            if not user_data:
                print("No user found in database")  # Debug
                self.show_error("No account found with that username or email")
                return
            
            # Check if security question exists
            if not user_data.get('security_question'):
                print("No security question found for user")  # Debug
                self.show_error("No security question set for this account")
                return
            
            print(f"Security question: {user_data['security_question']}")  # Debug
            
            # Success - move to step 2
            self.user_data = user_data
            self.security_question_text.value = f"Security Question: {user_data['security_question']}"
            self.current_step = 2
            print("Moving to step 2")  # Debug
            self.update_view()
            
        except Exception as e:
            print(f"Exception in handle_username_step: {e}")  # Debug
            import traceback
            traceback.print_exc()
            self.show_error(f"Error accessing database: {str(e)}")
            return
    
    def handle_security_question_step(self):
        """Handle step 2: security question verification"""
        answer = self.security_answer_field.value.strip()
        
        if not answer:
            self.show_error("Please provide an answer to the security question")
            return
        
        # Verify security answer
        if self.db_manager.verify_security_answer(self.user_data['id'], answer):
            self.current_step = 3
            self.update_view()
        else:
            self.show_error("Incorrect answer. Please try again.")
    
    def handle_reset_password(self, e):
        """Handle password reset"""
        new_password = self.new_password_field.value.strip()
        confirm_password = self.confirm_password_field.value.strip()
        
        if not new_password or not confirm_password:
            self.show_error("Please fill in both password fields")
            return
        
        if new_password != confirm_password:
            self.show_error("Passwords do not match")
            return
        
        if len(new_password) < 6:
            self.show_error("Password must be at least 6 characters long")
            return
        
        # Update password
        success = self.db_manager.update_password(self.user_data['id'], new_password)
        
        if success:
            self.show_success("Password reset successfully! You can now login with your new password.")
            self.current_step = 1
            self.reset_form()
        else:
            self.show_error("Failed to reset password. Please try again.")
    
    def update_view(self):
        """Update the view based on current step"""
        self.error_message.visible = False
        self.success_message.visible = False
        
        # Update step visibility
        if hasattr(self, 'step1_container'):
            self.step1_container.visible = (self.current_step == 1)
        if hasattr(self, 'step2_container'):
            self.step2_container.visible = (self.current_step == 2)
        if hasattr(self, 'step3_container'):
            self.step3_container.visible = (self.current_step == 3)
        
        # Update step indicators
        if hasattr(self, 'step1_indicator'):
            self.step1_indicator.bgcolor = "#bb5862" if self.current_step >= 1 else ft.Colors.GREY_400
        if hasattr(self, 'step2_indicator'):
            self.step2_indicator.bgcolor = "#bb5862" if self.current_step >= 2 else ft.Colors.GREY_400
        if hasattr(self, 'step3_indicator'):
            self.step3_indicator.bgcolor = "#bb5862" if self.current_step >= 3 else ft.Colors.GREY_400
        
        # Update button visibility
        if hasattr(self, 'next_button_container'):
            self.next_button_container.visible = (self.current_step in [1, 2])
        if hasattr(self, 'reset_button_container'):
            self.reset_button_container.visible = (self.current_step == 3)
        
        if self.current_step == 1:
            self.next_button.text = "Next"
            self.next_button.icon = ft.Icons.ARROW_FORWARD
        elif self.current_step == 2:
            self.next_button.text = "Next"
            self.next_button.icon = ft.Icons.ARROW_FORWARD
        elif self.current_step == 3:
            pass  # Reset button is shown instead
        
        self.page.update()
    
    def reset_form(self):
        """Reset the form to step 1"""
        self.current_step = 1
        self.user_data = None
        self.username_field.value = ""
        self.security_answer_field.value = ""
        self.new_password_field.value = ""
        self.confirm_password_field.value = ""
        self.security_question_text.value = ""
        # Only update view if containers are created
        if hasattr(self, 'step1_container') and self.step1_container is not None:
            self.update_view()
    
    def show_error(self, message: str):
        """Show error message"""
        self.error_message.value = message
        self.error_message.visible = True
        self.success_message.visible = False
        self.page.update()
    
    def show_success(self, message: str):
        """Show success message"""
        self.success_message.value = message
        self.success_message.visible = True
        self.error_message.visible = False
        self.page.update()
    
    def go_back(self, e):
        """Go back to login"""
        self.page.go("/")
    
    def get_view(self):
        """Return the password recovery view"""
        # Don't reset form when view is created - only reset on first load
        if not hasattr(self, '_view_initialized'):
            self.reset_form()
            self._view_initialized = True
        return ft.View(
            "/password-recovery",
            [
                ft.Stack(
                    controls=[
                        # Background
                        ft.Container(
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=["#efaaaa", "#f4f1ec"]
                            ),
                            width=self.page.window.width,
                            height=self.page.window.height
                        ),
                        # Foreground
                        ft.Container(
                            alignment=ft.alignment.center,
                            content=ft.Column(
                        [
                            # Header
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(
                                            ft.Icons.LOCK_RESET,
                                            size=70,
                                            color="#bb5862"
                                        ),
                                        ft.Text(
                                            "Password Recovery",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color="#1f2937",
                                            text_align=ft.TextAlign.CENTER
                                        ),
                                        ft.Text(
                                            "Follow the steps to reset your password",
                                            size=16,
                                            color="#6b6b6b",
                                            text_align=ft.TextAlign.CENTER
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10
                                ),
                                padding=ft.padding.only(bottom=30)
                            ),
                            
                            # Step indicator
                            ft.Container(
                                content=ft.Row(
                                    [
                                        self._create_step_indicator(1),
                                        self._create_step_indicator(2),
                                        self._create_step_indicator(3)
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=20
                                ),
                                padding=ft.padding.only(bottom=30)
                            ),
                            
                            # Recovery Form
                            ft.Container(
                                content=ft.Column(
                                    [
                                        # Step 1: Username/Email
                                        self._create_step1_container(),
                                        
                                        # Step 2: Security Question
                                        self._create_step2_container(),
                                        
                                        # Step 3: New Password
                                        self._create_step3_container(),
                                        
                                        self.error_message,
                                        self.success_message,
                                        
                                        ft.Container(height=20),
                                        
                                        # Buttons
                                        self._create_next_button_container(),
                                        
                                        self._create_reset_button_container(),
                                        
                                        ft.Container(height=20),
                                        self.back_button
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=15
                                ),
                                bgcolor="#f4f1ec",
                                padding=40,
                                width=500,
                                border_radius=25,
                                border=ft.border.all(2, "#cfc6b5"),
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=18,
                                    color="#eadfd0",
                                    offset=ft.Offset(0, 6)
                                )
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    ),
                            padding=ft.padding.all(20)
                        )
                    ],
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )

