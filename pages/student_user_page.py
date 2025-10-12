import flet as ft
import os
import shutil
from database.database_manager import DatabaseManager

class StudentUserPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, parent_dashboard=None):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        self.parent_dashboard = parent_dashboard
        self.current_user_info = None

        # Form field references
        self.first_name_field = None
        self.middle_name_field = None
        self.last_name_field = None
        self.sfx_field = None
        self.email_field = None
        self.student_id_field = None
        self.sex_field = None
        self.username_field = None
        self.recovery_question_field = None
        self.security_answer_field = None
        self.password_field = None
        self.confirm_password_field = None
        
        # Profile picture related
        self.profile_image = None
        self.selected_image_path = None
        self.file_picker = None

        # Initialize UI components
        self.init_ui()
        self.init_file_picker()
        self.load_current_user_info()
        self.show_user_content()
    
    def _build_section_header(self, icon, title, horizontal_padding=0, vertical_padding=15, bottom_margin=20):
        """Build standardized header with adjustable positioning"""
        from datetime import datetime
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(icon, size=28, color="#D4817A"),
                    ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color="#D4817A")
                ], spacing=10),
                ft.Row([
                    ft.Text(
                        datetime.now().strftime("%B %d, %Y"),
                        size=14,
                        color="#D4817A"
                    )
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=horizontal_padding, vertical=vertical_padding),
            height=60,  # Fixed height for consistency
            bgcolor="#f4f1ec",  # Match main content background
            margin=ft.margin.only(bottom=bottom_margin)  # Adjustable spacing after header
        )

    def show_user_content(self):
        """Show user content with standardized header positioning"""
        # Use standardized header function
        header = self._build_section_header(
            ft.Icons.PERSON, 
            "User Profile",
            horizontal_padding=0,  # No horizontal padding for user page
            vertical_padding=15,
            bottom_margin=20
        )
        
        # Get content only without sidebar
        user_form = self.create_user_form()
        
        # Standardized layout: header + scrollable content
        content_body = ft.Container(
            content=user_form,
            expand=True,
            padding=ft.padding.all(0)
        )
        
        combined_content = ft.Column([
            header,  # Fixed header at top
            content_body
        ], spacing=0, expand=True)
        
        self.main_content.content = combined_content
        self.page.update()
    
    def get_user_display_name(self):
        """Get display name for the current user"""
        if self.current_user_info:
            first_name = self.current_user_info.get('first_name', '')
            last_name = self.current_user_info.get('last_name', '')
            if first_name and last_name:
                return f"{last_name}, {first_name}"
            elif first_name:
                return first_name
            elif last_name:
                return last_name
        
        # Fallback to page data
        if self.user_data and isinstance(self.user_data, dict):
            username = self.user_data.get('username', '')
            name = self.user_data.get('name', '')
            if name:
                return name
            elif username:
                return username
        
        return "Student User"
    
    def create_profile_photo(self):
        """Create profile photo container with user's actual photo or default"""
        import os
        
        # Get user's profile photo path
        profile_photo_path = None
        if self.user_data and isinstance(self.user_data, dict):
            profile_photo_path = self.user_data.get('profile_photo')
        
        # Check if photo file exists
        if profile_photo_path and os.path.exists(profile_photo_path):
            # Show actual user photo
            return ft.Container(
                content=ft.Image(
                    src=profile_photo_path,
                    width=80,
                    height=80,
                    fit=ft.ImageFit.COVER,
                    border_radius=40
                ),
                width=80,
                height=80,
                border_radius=40,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                alignment=ft.alignment.center
            )
        else:
            # Show default icon
            return ft.Container(
                content=ft.Stack([
                    ft.Container(
                        width=80,
                        height=80,
                        border_radius=40,
                        bgcolor=ft.Colors.BLUE_100
                    ),
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.GREEN_600),
                        alignment=ft.alignment.center,
                        width=80,
                        height=80
                    )
                ]),
                alignment=ft.alignment.center
            )

    def init_ui(self):
        """Initialize UI components"""
        # Left sidebar navigation (matching the student dashboard exactly)
        self.sidebar = ft.Container(
            content=ft.Column([
                # Profile section
                ft.Container(
                    content=ft.Column([
                        self.create_profile_photo(),
                        ft.Text(
                            f"{self.get_user_display_name()}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Student",
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
                        self.create_nav_item(ft.Icons.PERSON, "User", True),
                        self.create_nav_item(ft.Icons.HOME, "Dashboard", False),
                        self.create_nav_item(ft.Icons.ARTICLE, "Posts", False),
                        self.create_nav_item(ft.Icons.ASSIGNMENT, "Assessments", False),
                        self.create_nav_item(ft.Icons.STAR, "Scores", False)
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
                    ), alignment=ft.alignment.center,
                    padding=ft.padding.all(10)
                )
            ]),
            width=240,
            bgcolor="#efb6aa",  # Pink color matching student dashboard
            padding=ft.padding.all(0),
            margin=ft.margin.only(top=100),
            border_radius=ft.border_radius.only(
                top_left=0,
                top_right=120,
                bottom_left=0,
                bottom_right=0
            )
        )
        
        # Main content area
        self.main_content = ft.Container(
            expand=True,
            bgcolor="#f4f1ec",  # Light beige background matching student dashboard
            padding=ft.padding.all(50)  # Match dashboard padding
        )

    def create_nav_item(self, icon, text, is_active=False):
        """Create navigation item matching student dashboard style exactly"""
        return ft.Container(
            content=ft.TextButton(
                content=ft.Row([
                    ft.Icon(
                        icon,
                        color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70,
                        size=20
                    ),
                    ft.Text(
                        text,
                        color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70,
                        size=14,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL
                    )
                ], alignment=ft.MainAxisAlignment.START),
                on_click=lambda e, view=text.lower(): self.navigate_to(view),
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    overlay_color=ft.Colors.WHITE10,
                    shape=ft.RoundedRectangleBorder(radius=0)
                )
            ),
            bgcolor=ft.Colors.WHITE10 if is_active else ft.Colors.TRANSPARENT,
            border_radius=0
        )

    def init_file_picker(self):
        """Initialize file picker for profile pictures"""
        self.file_picker = ft.FilePicker(
            on_result=self.on_file_picked
        )
        self.page.overlay.append(self.file_picker)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files:
            file_path = e.files[0].path
            # Validate file type
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in allowed_extensions:
                self.selected_image_path = file_path
                self.update_profile_image_display()
                self.show_success("Profile picture selected successfully!")
            else:
                self.show_error("Please select a valid image file (JPG, PNG, GIF, BMP)")

    def update_profile_image_display(self):
        """Update the profile image display"""
        if self.profile_image and self.selected_image_path:
            # If it's currently a Container (initials), replace with Image
            if isinstance(self.profile_image, ft.Container):
                # Create new Image widget
                new_image = ft.Image(
                    src=self.selected_image_path,
                    width=120,
                    height=120,
                    fit=ft.ImageFit.COVER,
                    border_radius=60
                )
                self.profile_image = new_image
                # Need to refresh the form to show the new image
                self.show_user_content()
            else:
                # It's already an Image, just update the src
                self.profile_image.src = self.selected_image_path
                # Don't call update() directly, refresh the whole page instead
                self.page.update()

    def create_profile_picture_section(self):
        """Create profile picture upload section"""
        # Get current profile photo path
        current_photo = self.current_user_info.get('profile_photo', '') if self.current_user_info else ''
        
        # Default avatar or current photo
        if current_photo and os.path.exists(current_photo):
            image_src = current_photo
        else:
            # Create a default avatar with user initials
            first_name = self.current_user_info.get('first_name', 'U') if self.current_user_info else 'U'
            last_name = self.current_user_info.get('last_name', 'N') if self.current_user_info else 'N'
            initials = f"{first_name[0]}{last_name[0]}".upper()
            image_src = None  # We'll use a container with initials instead
        
        # Profile image container
        if image_src:
            self.profile_image = ft.Image(
                src=image_src,
                width=120,
                height=120,
                fit=ft.ImageFit.COVER,
                border_radius=60
            )
        else:
            # Default avatar with initials
            first_name = self.current_user_info.get('first_name', 'U') if self.current_user_info else 'U'
            last_name = self.current_user_info.get('last_name', 'N') if self.current_user_info else 'N'
            initials = f"{first_name[0]}{last_name[0]}".upper()
            
            self.profile_image = ft.Container(
                content=ft.Text(
                    initials,
                    size=40,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE
                ),
                width=120,
                height=120,
                bgcolor="#D4817A",
                border_radius=60,
                alignment=ft.alignment.center
            )
        
        return ft.Container(
            content=ft.Column([
                # Profile picture
                ft.Container(
                    content=self.profile_image,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=15)
                ),
                # Change picture button
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CAMERA_ALT, size=16, color=ft.Colors.WHITE),
                        ft.Text("Change Picture", size=12, color=ft.Colors.WHITE)
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor="#D4817A",
                    color=ft.Colors.WHITE,
                    width=140,
                    height=35,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    on_click=lambda e: self.file_picker.pick_files(
                        dialog_title="Select Profile Picture",
                        file_type=ft.FilePickerFileType.IMAGE,
                        allow_multiple=False
                    )
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, "#E8B4CB"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )

    def show_success(self, message):
        """Show success message"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN
        )
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

    def show_error(self, message):
        """Show error message"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED
        )
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

    def save_profile_picture(self):
        """Save the selected profile picture to the uploads directory"""
        try:
            if not self.selected_image_path:
                return None
            
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join(os.getcwd(), "uploads", "profile_pictures")
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate unique filename
            user_id = self.current_user_info.get('id', 'unknown')
            file_extension = os.path.splitext(self.selected_image_path)[1]
            filename = f"profile_{user_id}_{int(os.path.getmtime(self.selected_image_path))}{file_extension}"
            
            # Copy file to uploads directory
            destination_path = os.path.join(uploads_dir, filename)
            shutil.copy2(self.selected_image_path, destination_path)
            
            # Return relative path for database storage
            return os.path.join("uploads", "profile_pictures", filename)
            
        except Exception as e:
            print(f"Error saving profile picture: {e}")
            self.show_error("Failed to save profile picture")
            return None

    def create_user_form(self):
        """Create the main user form with improved visual design and auto-populated data"""
        # Initialize form fields with actual user data values
        first_name = self.current_user_info.get('first_name', '') if self.current_user_info else ''
        middle_name = self.current_user_info.get('middle_name', '') if self.current_user_info else ''
        last_name = self.current_user_info.get('last_name', '') if self.current_user_info else ''
        suffix = self.current_user_info.get('suffix', '') if self.current_user_info else ''
        email = self.current_user_info.get('email', '') if self.current_user_info else ''
        student_id = self.current_user_info.get('student_number', '') if self.current_user_info else ''
        sex = self.current_user_info.get('sex', 'Male') if self.current_user_info else 'Male'
        username = self.current_user_info.get('username', '') if self.current_user_info else ''
        recovery_question = self.current_user_info.get('recovery_question', "What is your mother's maiden name?") if self.current_user_info else "What is your mother's maiden name?"
        
        self.first_name_field = self.create_textfield("First Name", width=180, value=first_name)
        self.middle_name_field = self.create_textfield("Middle Name", width=180, value=middle_name)
        self.last_name_field = self.create_textfield("Last Name", width=180, value=last_name)
        
        self.sfx_field = ft.Dropdown(
            label="Suffix",
            value=suffix,
            options=[
                ft.dropdown.Option(""),
                ft.dropdown.Option("Jr."),
                ft.dropdown.Option("Sr."),
                ft.dropdown.Option("II"),
                ft.dropdown.Option("III"),
                ft.dropdown.Option("IV"),
            ],
            width=350,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            bgcolor=ft.Colors.WHITE,
            text_size=14
        )
        
        self.email_field = self.create_textfield("Email Address", width=280, value=email)
        self.student_id_field = self.create_textfield("Student ID Number", width=180, value=student_id)
        
        self.sex_field = ft.Dropdown(
            label="Gender",
            value=sex,
            options=[
                ft.dropdown.Option("Male"),
                ft.dropdown.Option("Female"),
            ],
            width=350,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            bgcolor=ft.Colors.WHITE,
            text_size=14
        )
        
        self.username_field = self.create_textfield("Username", width=280, value=username)
        
        self.recovery_question_field = ft.Dropdown(
            label="Security Question",
            value=recovery_question,
            options=[
                ft.dropdown.Option("What is your mother's maiden name?"),
                ft.dropdown.Option("What is the name of your first pet?"),
                ft.dropdown.Option("What city were you born in?"),
                ft.dropdown.Option("What is your favorite food?"),
                ft.dropdown.Option("What was your first car?"),
            ],
            width=350,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            bgcolor=ft.Colors.WHITE,
            text_size=14
        )
        
        self.security_answer_field = self.create_textfield("Security Answer", width=400, value="")
        
        self.password_field = self.create_textfield("New Password", password=True, width=280, value="")
        self.confirm_password_field = self.create_textfield("Confirm Password", password=True, width=280, value="")

        return ft.Container(
            content=ft.Column([
                
                # Personal Information Section with profile picture
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=20, color="#D4817A"),
                            ft.Text(
                                "Personal Information",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color="#333333"
                            )
                        ], spacing=10),
                        
                        ft.Container(height=20),
                        
                        # Profile picture and name fields layout
                        ft.Row([
                            # Profile picture section (left side)
                            ft.Container(
                                content=self.create_profile_picture_section(),
                                width=200
                            ),
                            
                            ft.Container(width=20),  # Spacing
                            
                            # Name fields section (right side)
                            ft.Container(
                                content=ft.Column([
                                    # Name fields in responsive row
                                    ft.ResponsiveRow([
                                        ft.Container(self.first_name_field, col={"sm": 12, "md": 4, "lg": 4}),
                                        ft.Container(self.middle_name_field, col={"sm": 12, "md": 4, "lg": 4}),
                                        ft.Container(self.last_name_field, col={"sm": 12, "md": 4, "lg": 4})
                                    ], spacing=15),
                                    
                                    ft.Container(height=15),
                                    
                                    # Contact and ID row
                                    ft.ResponsiveRow([
                                        ft.Container(self.email_field, col={"sm": 12, "md": 6, "lg": 6}),
                                        ft.Container(self.student_id_field, col={"sm": 12, "md": 6, "lg": 6})
                                    ], spacing=15),
                                    
                                    ft.Container(height=15),
                                    
                                    ft.ResponsiveRow([
                                        ft.Container(self.sex_field, col={"sm": 12, "md": 6, "lg": 6}),
                                        ft.Container(self.sfx_field, col={"sm": 12, "md": 6, "lg": 6})
                                    ], spacing=15),
                                ]),
                                expand=True
                            )
                        ], alignment=ft.MainAxisAlignment.START),
                    ]),
                    padding=ft.padding.all(25),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    border=ft.border.all(1, "#E8B4CB"),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=5,
                        color=ft.Colors.BLACK12,
                        offset=ft.Offset(0, 2)
                    )
                ),
                
                ft.Container(height=20),
                
                # Account Settings Section with enhanced styling
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SETTINGS, size=20, color="#D4817A"),
                            ft.Text(
                                "Account Settings",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color="#333333"
                            )
                        ], spacing=10),
                        
                        ft.Container(height=20),
                        
                        # Username and security in responsive layout
                        self.username_field,
                        
                        ft.Container(height=15),
                        
                        self.recovery_question_field,
                        
                        ft.Container(height=15),
                        
                        self.security_answer_field,
                        
                        ft.Container(
                            content=ft.Text(
                                "💡 This answer will be used for password recovery if you forget your password",
                                size=11,
                                color="#666666",
                                italic=True
                            ),
                            margin=ft.margin.only(top=5)
                        ),
                    ]),
                    padding=ft.padding.all(25),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    border=ft.border.all(1, "#E8B4CB"),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=5,
                        color=ft.Colors.BLACK12,
                        offset=ft.Offset(0, 2)
                    )
                ),
                
                ft.Container(height=20),
                
                # Password Section with enhanced styling
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LOCK, size=20, color="#D4817A"),
                            ft.Text(
                                "Change Password",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color="#333333"
                            )
                        ], spacing=10),
                        
                        ft.Container(
                            content=ft.Text(
                                "Leave blank to keep current password",
                                size=12,
                                color="#999999",
                                italic=True
                            ),
                            margin=ft.margin.only(top=8, bottom=20)
                        ),
                        
                        # Password fields in responsive row
                        ft.ResponsiveRow([
                            ft.Container(self.password_field, col={"sm": 12, "md": 6, "lg": 6}),
                            ft.Container(self.confirm_password_field, col={"sm": 12, "md": 6, "lg": 6})
                        ], spacing=15),
                    ]),
                    padding=ft.padding.all(25),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    border=ft.border.all(1, "#E8B4CB"),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=5,
                        color=ft.Colors.BLACK12,
                        offset=ft.Offset(0, 2)
                    )
                ),
                
                ft.Container(height=30),
                
                # Enhanced Save button
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE, size=18, color=ft.Colors.WHITE),
                            ft.Text("SAVE CHANGES", size=14, weight=ft.FontWeight.BOLD)
                        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                        on_click=self.save_changes,
                        style=ft.ButtonStyle(
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=40, vertical=15),
                            shape=ft.RoundedRectangleBorder(radius=20)
                        ),
                        width=220,
                        height=50
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], 
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True),
            padding=20,
            bgcolor="#f4f1ec"
        )

    def create_textfield(self, label, password=False, width=350, value=""):
        """Create a text field with improved styling and default value"""
        return ft.TextField(
            label=label,
            value=value,
            password=password,
            can_reveal_password=password,
            width=width,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            bgcolor=ft.Colors.WHITE,
            text_size=14,
            label_style=ft.TextStyle(color="#888888", size=12),
            cursor_color="#D4817A",
            content_padding=ft.padding.symmetric(horizontal=15, vertical=12)
        )


    def navigate_to(self, view):
        """Navigate to different pages without transitions"""
        if view == "dashboard":
            # Clear views and navigate directly to student dashboard
            self.page.views.clear()
            from pages.student_dashboard import StudentDashboard
            student_dashboard = StudentDashboard(self.page, self.db_manager)
            self.page.views.append(student_dashboard.get_view())
            self.page.update()
        elif view == "posts":
            # Clear views and navigate directly to student posts
            self.page.views.clear()
            from pages.student_posts_page import StudentPostsPage
            student_posts = StudentPostsPage(self.page, self.db_manager)
            self.page.views.append(student_posts.get_view())
            self.page.update()
        elif view == "assessments":
            # Navigate back to student dashboard and then to assessments
            self.page.views.clear()
            from pages.student_dashboard import StudentDashboard
            student_dashboard = StudentDashboard(self.page, self.db_manager)
            self.page.views.append(student_dashboard.get_view())
            self.page.update()
        elif view == "scores":
            # Navigate to scores when implemented
            pass
        elif view == "user":
            # Already on user page
            pass

    def logout(self, e):
        """Handle logout"""
        self.page.go("/")

    def save_changes(self, e):
        """Save user information changes to database"""
        try:
            # Validate required fields
            if not self.first_name_field.value or not self.last_name_field.value:
                return
            
            if not self.email_field.value:
                return
            
            if not self.username_field.value:
                return
            
            # Get the new name values
            new_first_name = self.first_name_field.value.strip()
            new_middle_name = self.middle_name_field.value.strip() if self.middle_name_field.value else ''
            new_last_name = self.last_name_field.value.strip()
            
            # Update current user info IMMEDIATELY
            self.current_user_info['first_name'] = new_first_name
            self.current_user_info['middle_name'] = new_middle_name
            self.current_user_info['last_name'] = new_last_name
            self.current_user_info['email'] = self.email_field.value.strip()
            self.current_user_info['student_number'] = self.student_id_field.value.strip() if self.student_id_field.value else ''
            self.current_user_info['username'] = self.username_field.value.strip()
            
            # Update sidebar name RIGHT NOW
            self.update_sidebar_name_immediately()
            
            # Handle profile picture upload
            profile_photo_path = None
            if self.selected_image_path:
                profile_photo_path = self.save_profile_picture()
            
            # Prepare data for database
            user_data = {
                'first_name': new_first_name,
                'middle_name': new_middle_name,
                'last_name': new_last_name,
                'suffix': self.sfx_field.value if self.sfx_field.value else '',
                'email': self.email_field.value.strip(),
                'student_number': self.student_id_field.value.strip() if self.student_id_field.value else '',
                'sex': self.sex_field.value if self.sex_field.value else 'Male',
                'username': self.username_field.value.strip(),
                'recovery_question': self.recovery_question_field.value if self.recovery_question_field.value else '',
                'recovery_answer': self.security_answer_field.value.strip() if self.security_answer_field.value else ''
            }
            
            # Add profile picture if uploaded
            if profile_photo_path:
                user_data['profile_photo'] = profile_photo_path
            
            # Add password if provided
            if self.password_field.value:
                user_data['password'] = self.password_field.value
            
            # Save to database
            self.save_to_database(user_data)
            
            # Show success message
            self.show_success_message()
            
            # Clear password fields
            self.password_field.value = ""
            self.confirm_password_field.value = ""
            
            # Force page update
            self.page.update()
            
        except Exception as ex:
            print(f"Save error: {ex}")
    
    def show_success_message(self):
        """Show success message"""
        try:
            # Create a simple, reliable dialog
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("SUCCESS!", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                content=ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=50, color=ft.Colors.GREEN),
                        ft.Text("✅ INFORMATION SAVED SUCCESSFULLY!", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("Your profile has been updated.", size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=20
                ),
                actions=[
                    ft.ElevatedButton(
                        "OK",
                        on_click=lambda _: self.close_success_dialog(),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=30, vertical=15)
                        )
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER
            )
            
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"Error showing success message: {e}")
    
    def close_success_dialog(self):
        """Close success dialog"""
        try:
            if self.page.dialog:
                self.page.dialog.open = False
                self.page.update()
        except Exception as e:
            print(f"Error closing dialog: {e}")

    def update_sidebar_name_immediately(self):
        """Update sidebar name immediately"""
        try:
            new_display_name = self.get_user_display_name()
            
            if hasattr(self, 'sidebar') and self.sidebar:
                # Find the profile section
                profile_section = self.sidebar.content.controls[0]
                if hasattr(profile_section, 'content') and hasattr(profile_section.content, 'controls'):
                    controls = profile_section.content.controls
                    if len(controls) >= 2:
                        # Update the name text (second control)
                        name_control = controls[1]
                        if hasattr(name_control, 'value'):
                            name_control.value = new_display_name
                        elif hasattr(name_control, 'content') and hasattr(name_control.content, 'value'):
                            name_control.content.value = new_display_name
                        
                        self.page.update()
                        
        except Exception as e:
            print(f"Error updating sidebar: {e}")
    
    def parse_full_name(self, full_name):
        """Parse full name into separate components"""
        if not full_name:
            return {'first_name': '', 'middle_name': '', 'last_name': '', 'suffix': ''}
        
        # Split the full name
        name_parts = full_name.strip().split()
        
        # Common suffixes
        suffixes = ['Jr.', 'Sr.', 'II', 'III', 'IV', 'V']
        
        result = {'first_name': '', 'middle_name': '', 'last_name': '', 'suffix': ''}
        
        if len(name_parts) == 0:
            return result
        elif len(name_parts) == 1:
            result['first_name'] = name_parts[0]
        elif len(name_parts) == 2:
            result['first_name'] = name_parts[0]
            result['last_name'] = name_parts[1]
        elif len(name_parts) >= 3:
            # Check if last part is a suffix
            if name_parts[-1] in suffixes:
                result['suffix'] = name_parts[-1]
                name_parts = name_parts[:-1]
            
            result['first_name'] = name_parts[0]
            result['last_name'] = name_parts[-1]
            
            # Everything in between is middle name
            if len(name_parts) > 2:
                result['middle_name'] = ' '.join(name_parts[1:-1])
        
        return result

    def load_current_user_info(self):
        """Load current user information from database"""
        try:
            # Get current user data from page.data (set during login)
            if self.page.data and isinstance(self.page.data, dict):
                user_data = self.page.data
                
                # Try to get fresh data from database first
                user_id = user_data.get('id')
                if user_id:
                    fresh_user_data = self.db_manager.get_student_by_id(user_id)
                    if fresh_user_data:
                        user_data = fresh_user_data
                        
                        # Parse full_name into separate components
                        if 'full_name' in user_data:
                            name_parts = self.parse_full_name(user_data['full_name'])
                            user_data.update(name_parts)
                
                self.current_user_info = user_data
            else:
                self.current_user_info = {}
                
        except Exception as e:
            print(f"Error loading current user info: {e}")
            self.current_user_info = {}
    
    
    def save_to_database(self, user_data):
        """Save user data to database"""
        try:
            if self.current_user_info and self.current_user_info.get('id'):
                user_id = self.current_user_info['id']
                
                # Prepare full name
                full_name_parts = []
                if user_data.get('first_name'):
                    full_name_parts.append(user_data['first_name'])
                if user_data.get('middle_name'):
                    full_name_parts.append(user_data['middle_name'])
                if user_data.get('last_name'):
                    full_name_parts.append(user_data['last_name'])
                if user_data.get('suffix'):
                    full_name_parts.append(user_data['suffix'])
                
                full_name = ' '.join(full_name_parts)
                
                # Update user profile using the existing method
                success = self.db_manager.update_user_profile(
                    user_id=user_id,
                    full_name=full_name,
                    email=user_data.get('email'),
                    student_number=user_data.get('student_number'),
                    section=self.current_user_info.get('section'),  # Keep existing section
                    security_question=user_data.get('recovery_question'),
                    security_answer=user_data.get('recovery_answer'),
                    profile_photo=user_data.get('profile_photo')
                )
                
                if success:
                    print("✅ User profile updated successfully")
                    # Update current user info with new profile photo path
                    if user_data.get('profile_photo'):
                        self.current_user_info['profile_photo'] = user_data['profile_photo']
                else:
                    print("❌ Failed to update user profile")
                    
        except Exception as e:
            print(f"Error saving to database: {e}")
            self.show_error(f"Failed to save changes: {str(e)}")
    
    def get_view(self):
        """Get the main view for this page"""
        return ft.View(
            "/student-user",
            [
                ft.Row([
                    self.sidebar,
                    self.main_content
                ], spacing=0, expand=True)
            ],
            bgcolor="#f4f1ec",
            padding=0
        )
