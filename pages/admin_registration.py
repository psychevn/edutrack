import flet as ft
import os
import shutil
from datetime import datetime
from database.database_manager import DatabaseManager

class AdminRegistrationPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        
        # Form fields (theming left as-is; layout updated below)
        self.admin_id_field = ft.TextField(
            label="Admin ID Number",
            prefix_icon=ft.Icons.BADGE,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            width=350,
            hint_text="e.g., ADMIN001"
        )
        
        self.first_name_field = ft.TextField(
            label="First Name",
            prefix_icon=ft.Icons.PERSON,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#E8B4CB",
            width=350
        )
        
        self.middle_name_field = ft.TextField(
            label="Middle Name",
            prefix_icon=ft.Icons.PERSON,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#E8B4CB",
            width=350
        )
        
        self.last_name_field = ft.TextField(
            label="Last Name",
            prefix_icon=ft.Icons.PERSON,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#E8B4CB",
            width=350
        )
        
        self.username_field = ft.TextField(
            label="Username",
            prefix_icon=ft.Icons.ACCOUNT_CIRCLE,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            width=350
        )
        
        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            width=350
        )
        
        self.confirm_password_field = ft.TextField(
            label="Confirm Password",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            width=350
        )
        
        self.email_field = ft.TextField(
            label="Email",
            prefix_icon=ft.Icons.EMAIL,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            width=350
        )
        
        # Security question dropdown
        self.security_question_dropdown = ft.Dropdown(
            label="Security Question",
            prefix_icon=ft.Icons.QUESTION_ANSWER,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            width=350,
            options=[]
        )
        
        self.security_answer_field = ft.TextField(
            label="Security Answer",
            prefix_icon=ft.Icons.KEY,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
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
        self.create_button = ft.ElevatedButton(
            "Create Admin Account",
            icon=ft.Icons.ADD_CIRCLE,
            style=ft.ButtonStyle(
                bgcolor="#D4817A",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=24, vertical=14)
            ),
            on_click=self.handle_create_account,
            width=350
        )
        
        self.back_button = ft.TextButton(
            "← Back to Admin Login",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(color="#D4817A"),
            on_click=self.go_back
        )
        
        # Photo upload functionality
        self.photo_picker = ft.FilePicker()
        self.page.overlay.append(self.photo_picker)
        self.photo_picker.on_result = self.on_photo_result
        self.selected_photo_path = None
        
        self.photo_path_text = ft.Text(
            "No photo selected", 
            size=12, 
            color="#7C6E66"
        )
        
        self.photo_preview = ft.Image(
            width=100, 
            height=100, 
            fit=ft.ImageFit.COVER, 
            visible=False, 
            border_radius=10
        )
        
        self.upload_photo_button = ft.ElevatedButton(
            "Upload Profile Photo",
            icon=ft.Icons.UPLOAD_FILE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=15),
                bgcolor="#E8B4CB",
                color=ft.Colors.BLACK
            ),
            on_click=self.pick_photo,
            width=350
        )
        
        # Load security questions
        self.load_security_questions()
    
    def pick_photo(self, e):
        """Open file picker for photo selection"""
        self.photo_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp"]
        )
    
    def on_photo_result(self, e: ft.FilePickerResultEvent):
        """Handle photo selection result"""
        if e.files and len(e.files) > 0:
            self.selected_photo_path = e.files[0].path
            self.photo_path_text.value = e.files[0].name
            self.photo_preview.src = self.selected_photo_path
            self.photo_preview.visible = True
            self.page.update()
    
    def save_photo(self, username):
        """Save uploaded photo with unique filename"""
        if not self.selected_photo_path:
            return None
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads/profile_photos"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Get file extension
        file_extension = os.path.splitext(self.selected_photo_path)[1]
        
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"admin_{username}_{timestamp}{file_extension}"
        new_path = os.path.join(uploads_dir, new_filename)
        
        try:
            # Copy file to uploads directory
            shutil.copy2(self.selected_photo_path, new_path)
            return new_path
        except Exception as ex:
            print(f"Error saving photo: {ex}")
            return None
    
    def load_security_questions(self):
        """Load security questions into dropdown"""
        questions = self.db_manager.get_security_questions()
        self.security_question_dropdown.options = [
            ft.dropdown.Option(question) for question in questions
        ]
        if questions:
            self.security_question_dropdown.value = questions[0]
    
    def handle_create_account(self, e):
        """Handle admin account creation"""
        # Get form values
        admin_id = self.admin_id_field.value.strip()
        first_name = self.first_name_field.value.strip()
        middle_name = self.middle_name_field.value.strip()
        last_name = self.last_name_field.value.strip()
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        confirm_password = self.confirm_password_field.value.strip()
        email = self.email_field.value.strip()
        security_question = self.security_question_dropdown.value
        security_answer = self.security_answer_field.value.strip()
        
        # Validate form
        if not all([admin_id, first_name, last_name, username, password, confirm_password, email, security_question, security_answer]):
            self.show_error("Please fill in all fields")
            return
        
        if password != confirm_password:
            self.show_error("Passwords do not match")
            return
        
        if len(password) < 6:
            self.show_error("Password must be at least 6 characters long")
            return
        
        # Validate email format
        if "@" not in email or "." not in email:
            self.show_error("Please enter a valid email address")
            return
        
        # Save photo first
        photo_path = self.save_photo(username)
        
        # Combine name fields
        full_name = f"{first_name} {middle_name} {last_name}".strip().replace("  ", " ")
        
        # Create account
        success = self.db_manager.create_admin_account(
            admin_id, full_name, username, password, email, security_question, security_answer, photo_path
        )
        
        if success:
            self.show_success("Admin account created successfully! You can now login.")
            self.clear_form()
        else:
            self.show_error("Failed to create account. Username, email, or Admin ID may already exist.")
    
    def clear_form(self):
        """Clear all form fields"""
        self.admin_id_field.value = ""
        self.first_name_field.value = ""
        self.middle_name_field.value = ""
        self.last_name_field.value = ""
        self.username_field.value = ""
        self.password_field.value = ""
        self.confirm_password_field.value = ""
        self.email_field.value = ""
        self.security_answer_field.value = ""
        self.page.update()
    
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
        """Go back to admin login"""
        self.page.go("/admin-login")
    
    def get_view(self):
        """Return the admin registration view"""
        return ft.View(
            "/admin-registration",
            [
                ft.Stack(
                    controls=[
                        # Background matching student dashboard light surface
                        ft.Container(
                            bgcolor="#f4f1ec",
                            expand=True
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
                                        ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=70, color="#D4817A"),
                                        ft.Text(
                                            "Create Admin Account",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color="#D4817A",
                                            text_align=ft.TextAlign.CENTER
                                        ),
                                        ft.Text(
                                            "Fill in the details to create your admin account",
                                            size=16,
                                            color=ft.Colors.BLACK54,
                                            text_align=ft.TextAlign.CENTER
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10
                                ),
                                padding=ft.padding.only(bottom=30)
                            ),
                            
                            # Registration Form
                            ft.Container(
                                content=ft.Column(
                                    [
                                        self.admin_id_field,
                                        
                                        ft.ResponsiveRow([
                                            ft.Container(
                                                self.first_name_field,
                                                col={"sm": 12, "md": 4, "lg": 4}
                                            ),
                                            ft.Container(
                                                self.middle_name_field,
                                                col={"sm": 12, "md": 4, "lg": 4}
                                            ),
                                            ft.Container(
                                                self.last_name_field,
                                                col={"sm": 12, "md": 4, "lg": 4}
                                            )
                                        ], spacing=20),
                                        
                                        ft.ResponsiveRow([
                                            ft.Container(
                                                self.username_field,
                                                col={"sm": 12, "md": 6, "lg": 6}
                                            ),
                                            ft.Container(
                                                self.email_field,
                                                col={"sm": 12, "md": 6, "lg": 6}
                                            )
                                        ], spacing=20),
                                        
                                        ft.ResponsiveRow([
                                            ft.Container(
                                                self.password_field,
                                                col={"sm": 12, "md": 6, "lg": 6}
                                            ),
                                            ft.Container(
                                                self.confirm_password_field,
                                                col={"sm": 12, "md": 6, "lg": 6}
                                            )
                                        ], spacing=20),
                                        
                                        ft.ResponsiveRow([
                                            ft.Container(
                                                self.security_question_dropdown,
                                                col={"sm": 12, "md": 6, "lg": 6}
                                            ),
                                            ft.Container(
                                                ft.Column([
                                                    ft.Container(height=10),
                                                    self.upload_photo_button,
                                                    self.photo_path_text,
                                                    ft.Container(height=5),
                                                    self.photo_preview,
                                                ], spacing=5),
                                                col={"sm": 12, "md": 6, "lg": 6}
                                            )
                                        ], spacing=20),
                                        
                                        self.security_answer_field,
                                        
                                        self.error_message,
                                        self.success_message,
                                        
                                        ft.Container(height=20),
                                        self.create_button,
                                        ft.Container(height=20),
                                        self.back_button
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=15,
                                    scroll=ft.ScrollMode.ADAPTIVE
                                ),
                                bgcolor=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(horizontal=40, vertical=30),
                                width=min(800, self.page.window.width * 0.9) if self.page.window.width else 800,
                                expand=True,
                                border_radius=25,
                                border=ft.border.all(1, "#E8B4CB"),
                                shadow=ft.BoxShadow(spread_radius=0, blur_radius=5, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2))
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
            bgcolor="#f4f1ec",
            scroll=ft.ScrollMode.ADAPTIVE
        )

