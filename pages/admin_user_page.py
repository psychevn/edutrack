import flet as ft
import os
import shutil
from database.database_manager import DatabaseManager

class AdminUserPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, parent_dashboard=None):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data  # Assuming user data is passed via page.data
        self.parent_dashboard = parent_dashboard  # Reference to parent admin dashboard
        self.current_user_info = None  # Store current user info

        # Form field references for data binding
        self.first_name_field = None
        self.middle_name_field = None
        self.last_name_field = None
        self.sfx_field = None
        self.email_field = None
        self.admin_id_field = None
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
        self.populate_form_fields()
        self.load_user_data()
    
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
        
        return "Admin User"
    
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
                        bgcolor="#E8F4FD"
                    ),
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON, size=40, color="#87CEEB"),
                        alignment=ft.alignment.center,
                        width=80,
                        height=80
                    )
                ]),
                alignment=ft.alignment.center
            )

    def init_ui(self):
        """Initialize UI components"""
        # Left sidebar navigation (matching the admin dashboard exactly)
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
                            "Admin",
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
                        self.create_nav_item(ft.Icons.HOME, "Dashboard", True),
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
            bgcolor="#D4817A",  # Updated to match admin dashboard color
            padding=ft.padding.all(0)
        )
        
        # Main content area
        self.main_content = ft.Container(
            expand=True,
            bgcolor="#f4f1ec",  # Light beige background matching admin dashboard
            padding=ft.padding.all(20),
            content=self.create_user_form()
        )

    def create_nav_item(self, icon, text, is_active=False):
        """Create navigation item matching admin dashboard style exactly"""
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
            bgcolor="#B85450" if is_active else ft.Colors.TRANSPARENT,  # Active background matching admin dashboard
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
                self.load_user_data()
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
            first_name = self.current_user_info.get('first_name', 'A') if self.current_user_info else 'A'
            last_name = self.current_user_info.get('last_name', 'D') if self.current_user_info else 'D'
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
            first_name = self.current_user_info.get('first_name', 'A') if self.current_user_info else 'A'
            last_name = self.current_user_info.get('last_name', 'D') if self.current_user_info else 'D'
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
        admin_id = self.current_user_info.get('admin_id', '') if self.current_user_info else ''
        sex = self.current_user_info.get('sex', 'Male') if self.current_user_info else 'Male'
        username = self.current_user_info.get('username', '') if self.current_user_info else ''
        recovery_question = self.current_user_info.get('recovery_question', "What is your mother's maiden name?") if self.current_user_info else "What is your mother's maiden name?"
        
        # Debug logging to verify real data is being used
        print(f"🔧 Creating form fields with REAL DATA:")
        print(f"   First Name: '{first_name}'")
        print(f"   Middle Name: '{middle_name}'")
        print(f"   Last Name: '{last_name}'")
        print(f"   Email: '{email}'")
        print(f"   Admin ID: '{admin_id}'")
        print(f"   Username: '{username}'")
        
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
        self.admin_id_field = self.create_textfield("Admin ID Number", width=180, value=admin_id)
        
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
                # Enhanced Header section
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=32, color="#D4817A"),
                            ft.Text(
                                "Admin Profile Management", 
                                size=28, 
                                weight=ft.FontWeight.BOLD, 
                                color="#D4817A"
                            )
                        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
                        
                        ft.Container(
                            content=ft.Text(
                                "Manage your administrative profile and account settings",
                                size=15,
                                color="#777777",
                                text_align=ft.TextAlign.CENTER
                            ),
                            margin=ft.margin.only(top=10)
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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
                
                ft.Container(height=25),
                
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
                                        ft.Container(self.admin_id_field, col={"sm": 12, "md": 6, "lg": 6})
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

    def load_user_data(self):
        """Load existing user data into the form fields"""
        if self.user_data and isinstance(self.user_data, dict):
            # Populate fields with existing data
            if 'first_name' in self.user_data:
                self.first_name_field.value = self.user_data['first_name']
            if 'middle_name' in self.user_data:
                self.middle_name_field.value = self.user_data['middle_name']
            if 'last_name' in self.user_data:
                self.last_name_field.value = self.user_data['last_name']
            if 'email' in self.user_data:
                self.email_field.value = self.user_data['email']
            if 'admin_id' in self.user_data:
                self.admin_id_field.value = self.user_data['admin_id']
            if 'username' in self.user_data:
                self.username_field.value = self.user_data['username']
            if 'sex' in self.user_data:
                self.sex_field.value = self.user_data['sex']
            if 'suffix' in self.user_data:
                self.sfx_field.value = self.user_data['suffix']

    def navigate_to(self, view):
        """Navigate to different pages - works with parent dashboard for inline navigation"""
        if self.parent_dashboard:
            # Use parent dashboard's navigation for inline display
            if view == "dashboard":
                self.parent_dashboard.show_dashboard()
            elif view == "assessments":
                self.parent_dashboard.show_assessments_inline()
            elif view == "scores":
                self.parent_dashboard.show_results()
            elif view == "user":
                # Already on user page
                pass
        else:
            # Fallback to route navigation (for standalone use)
            if view == "dashboard":
                self.page.go("/admin")
            elif view == "assessments":
                self.page.go("/assessment-management")
            elif view == "scores":
                # Navigate to scores page when implemented
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
            print("🔄 Save changes clicked!")
            
            # Validate required fields
            if not self.first_name_field.value or not self.last_name_field.value:
                print("❌ Validation failed: Missing required fields")
                return
            
            if not self.email_field.value:
                print("❌ Validation failed: Missing email")
                return
            
            if not self.username_field.value:
                print("❌ Validation failed: Missing username")
                return
            
            # Get the new name values
            new_first_name = self.first_name_field.value.strip()
            new_middle_name = self.middle_name_field.value.strip() if self.middle_name_field.value else ''
            new_last_name = self.last_name_field.value.strip()
            
            print(f"🔄 New name: {new_first_name} {new_middle_name} {new_last_name}")
            
            # Update current user info IMMEDIATELY
            self.current_user_info['first_name'] = new_first_name
            self.current_user_info['middle_name'] = new_middle_name
            self.current_user_info['last_name'] = new_last_name
            self.current_user_info['email'] = self.email_field.value.strip()
            self.current_user_info['admin_id'] = self.admin_id_field.value.strip() if self.admin_id_field.value else ''
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
                'admin_id': self.admin_id_field.value.strip() if self.admin_id_field.value else '',
                'sex': self.sex_field.value if self.sex_field.value else 'Male',
                'username': self.username_field.value.strip(),
                'recovery_question': self.recovery_question_field.value if self.recovery_question_field.value else '',
                'security_answer': self.security_answer_field.value.strip() if self.security_answer_field.value else ''
            }
            
            # Add profile picture if uploaded
            if profile_photo_path:
                user_data['profile_photo'] = profile_photo_path
            
            # Add password if provided
            if self.password_field.value:
                user_data['password'] = self.password_field.value
            
            # Save to database
            self.save_to_database(user_data)
            
            # SHOW SUCCESS MESSAGE - GUARANTEED TO WORK
            self.show_guaranteed_success_message()
            
            # Clear password fields
            self.password_field.value = ""
            self.confirm_password_field.value = ""
            
            # Force page update
            self.page.update()
            
            print("✅ Save completed successfully!")
            
        except Exception as ex:
            print(f"❌ Save error: {ex}")
            import traceback
            traceback.print_exc()
    
    def show_guaranteed_success_message(self):
        """Show success message that WILL work"""
        try:
            print("🔄 Showing guaranteed success message...")
            
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
            
            print("✅ SUCCESS DIALOG SHOWN!")
            
        except Exception as e:
            print(f"❌ Error showing success message: {e}")
            # Fallback - just print to console
            print("✅✅✅ SAVE SUCCESSFUL - CHECK CONSOLE ✅✅✅")
    
    def close_success_dialog(self):
        """Close success dialog"""
        try:
            if self.page.dialog:
                self.page.dialog.open = False
                self.page.update()
                print("✅ Success dialog closed")
        except Exception as e:
            print(f"❌ Error closing dialog: {e}")

    def update_sidebar_name_immediately(self):
        """Update sidebar name immediately"""
        try:
            new_display_name = self.get_user_display_name()
            print(f"🔄 Updating sidebar to: '{new_display_name}'")
            
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
                        
                        print(f"✅ Sidebar updated to: '{new_display_name}'")
                        self.page.update()
                        
        except Exception as e:
            print(f"❌ Error updating sidebar: {e}")
    
    def load_current_user_info(self):
        """Load current user information from database"""
        try:
            # Get current user data from page.data (set during login)
            if self.page.data and isinstance(self.page.data, dict):
                user_data = self.page.data
                print(f"✅ Found logged-in user: {user_data.get('username', 'Unknown')}")
                print(f"🔍 Initial page data: {user_data}")
                
                # ALWAYS try to get fresh data from database first
                user_id = user_data.get('id')
                if user_id:
                    print(f"🔄 Fetching fresh data from database for user ID: {user_id}")
                    fresh_user_data = self.db_manager.get_user_by_id(user_id)
                    if fresh_user_data:
                        user_data = fresh_user_data
                        print(f"✅ Loaded fresh data from database: {fresh_user_data}")
                    else:
                        print(f"⚠️ No fresh data found in database for user ID: {user_id}")
                
                # Get the full_name from database
                full_name = user_data.get('full_name', '').strip()
                print(f"🔍 Full name from database: '{full_name}'")
                
                # Parse the full name more accurately
                first_name = ''
                middle_name = ''
                last_name = ''
                
                if full_name:
                    # Split by spaces and handle different name formats
                    name_parts = [part.strip() for part in full_name.split() if part.strip()]
                    print(f"🔍 Name parts: {name_parts}")
                    
                    if len(name_parts) == 1:
                        first_name = name_parts[0]
                    elif len(name_parts) == 2:
                        first_name = name_parts[0]
                        last_name = name_parts[1]
                    elif len(name_parts) >= 3:
                        first_name = name_parts[0]
                        # Everything except first and last is middle name
                        middle_name = ' '.join(name_parts[1:-1])
                        last_name = name_parts[-1]
                else:
                    # If no full name, use username as first name
                    first_name = user_data.get('username', 'Admin')
                    last_name = 'User'
                
                print(f"🔍 Parsed name components:")
                print(f"   First: '{first_name}'")
                print(f"   Middle: '{middle_name}'")
                print(f"   Last: '{last_name}'")
                
                # Get other user information
                email = user_data.get('email', '')
                admin_id = user_data.get('admin_id_number', '')
                username = user_data.get('username', '')
                security_question = user_data.get('security_question', "What is your mother's maiden name?")
                
                print(f"🔍 Other user data:")
                print(f"   Email: '{email}'")
                print(f"   Admin ID: '{admin_id}'")
                print(f"   Username: '{username}'")
                
                self.current_user_info = {
                    'id': user_data.get('id', 1),
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'last_name': last_name,
                    'suffix': '',  # Not stored separately in DB
                    'email': email,
                    'admin_id': admin_id,
                    'sex': 'Male',  # Default since not stored in current DB schema
                    'username': username,
                    'recovery_question': security_question,
                    'security_answer': '',  # Don't show the actual answer for security
                    'profile_photo': user_data.get('profile_photo', '')
                }
                
                # Set current profile photo
                if user_data.get('profile_photo'):
                    self.current_profile_photo = user_data.get('profile_photo')
                
                print(f"✅ Final user info: {self.current_user_info}")
                return
            
            # If no user data found, show error
            print("❌ No logged-in user found in page.data")
            self.current_user_info = {
                'id': 0,
                'first_name': 'No User',
                'middle_name': '',
                'last_name': 'Found',
                'suffix': '',
                'email': 'Please log in again',
                'admin_id': '',
                'sex': '',
                'username': '',
                'recovery_question': '',
                'security_answer': ''
            }
            
        except Exception as e:
            print(f"❌ Error loading user info: {e}")
            import traceback
            traceback.print_exc()
            # Use error data
            self.current_user_info = {
                'id': 0,
                'first_name': 'Error',
                'middle_name': '',
                'last_name': 'Loading',
                'suffix': '',
                'email': f'Error: {str(e)}',
                'admin_id': '',
                'sex': '',
                'username': '',
                'recovery_question': '',
                'security_answer': ''
            }

    def populate_form_fields(self):
        """Populate form fields with actual user data"""
        print(f"🔄 populate_form_fields called")
        print(f"🔄 current_user_info: {self.current_user_info}")
        print(f"🔄 first_name_field exists: {hasattr(self, 'first_name_field') and self.first_name_field is not None}")
        
        if self.current_user_info and hasattr(self, 'first_name_field') and self.first_name_field is not None:
            try:
                # Populate all form fields with actual user data
                print(f"🔄 Setting first_name to: {self.current_user_info.get('first_name', '')}")
                self.first_name_field.value = self.current_user_info.get('first_name', '')
                self.middle_name_field.value = self.current_user_info.get('middle_name', '')
                self.last_name_field.value = self.current_user_info.get('last_name', '')
                self.sfx_field.value = self.current_user_info.get('suffix', '')
                self.email_field.value = self.current_user_info.get('email', '')
                self.admin_id_field.value = self.current_user_info.get('admin_id', '')
                self.sex_field.value = self.current_user_info.get('sex', '')
                self.username_field.value = self.current_user_info.get('username', '')
                self.recovery_question_field.value = self.current_user_info.get('recovery_question', '')
                self.security_answer_field.value = self.current_user_info.get('security_answer', '')
                
                print(f"✅ Populated form with data for: {self.current_user_info.get('first_name', '')} {self.current_user_info.get('last_name', '')}")
                
                # Force update the page to show the populated data
                if hasattr(self, 'page'):
                    self.page.update()
                
            except Exception as e:
                print(f"❌ Error populating form fields: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ Cannot populate form fields:")
            print(f"   - current_user_info exists: {self.current_user_info is not None}")
            print(f"   - first_name_field exists: {hasattr(self, 'first_name_field')}")
            print(f"   - first_name_field is not None: {hasattr(self, 'first_name_field') and self.first_name_field is not None}")

    def update_sidebar_name(self):
        """Update the sidebar name with the current user's name"""
        if hasattr(self, 'sidebar') and self.sidebar:
            # Find and update the sidebar profile section
            profile_section = self.sidebar.content.controls[0]  # First container is profile section
            if profile_section and hasattr(profile_section, 'content'):
                profile_column = profile_section.content
                if hasattr(profile_column, 'controls') and len(profile_column.controls) >= 3:
                    # Update name text (second control)
                    profile_column.controls[1].value = self.get_user_display_name()
                    
                    print(f"✅ Updated sidebar with new name: '{self.get_user_display_name()}'")

    def show_simple_success(self, message):
        """Show a simple success message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(
                message,
                color=ft.Colors.WHITE,
                size=16,
                weight=ft.FontWeight.BOLD,
                expand=True
            ),
            bgcolor=ft.Colors.GREEN_600,
            duration=5000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.only(left=20, right=20, bottom=20),
            elevation=8,
            shape=ft.RoundedRectangleBorder(radius=12),
            width=500
        )
        self.page.snack_bar.open = True
        self.page.update()
        print(f"✅ Success message shown: {message}")

    def show_error(self, message):
        """Show error message"""
        # Close any existing snack bar first
        if self.page.snack_bar:
            self.page.snack_bar.open = False
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.WHITE, size=24),
                    ft.Text(
                        message, 
                        color=ft.Colors.WHITE, 
                        size=16, 
                        weight=ft.FontWeight.BOLD,
                        expand=True
                    )
                ], spacing=15, alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.all(15),
                border_radius=12
            ),
            bgcolor=ft.Colors.RED_600,
            duration=6000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.only(left=20, right=20, bottom=20),
            elevation=8,
            shape=ft.RoundedRectangleBorder(radius=12),
            width=500
        )
        self.page.snack_bar.open = True
        self.page.update()
        print(f"❌ Error message shown: {message}")

    def get_content_only(self):
        """Return only the main content without sidebar for inline display"""
        return self.create_user_form()

    def get_view(self):
        """Return the view for this page"""
        return ft.View(
            route="/admin-user",
            controls=[
                ft.Row(
                    [
                        self.sidebar,
                        self.main_content
                    ],
                    expand=True,
                    spacing=0
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )

    def save_to_database(self, user_data):
        """Save user data to database - implement actual database logic"""
        try:
            # Get current user ID from page data
            if not self.page.data or 'id' not in self.page.data:
                raise Exception("No user ID found in session data")
            
            user_id = self.page.data['id']
            
            # Combine name fields for database storage
            full_name = f"{user_data['first_name']} {user_data['middle_name']} {user_data['last_name']}".strip().replace("  ", " ")
            
            print(f"💾 Saving user data to database:")
            print(f"   User ID: {user_id}")
            print(f"   Full Name: '{full_name}'")
            print(f"   Email: '{user_data['email']}'")
            print(f"   Admin ID: '{user_data['admin_id']}'")
            print(f"   Username: '{user_data['username']}'")
            
            # Use direct SQL approach (more reliable)
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            try:
                # Update user profile directly with SQL
                cursor.execute('''
                    UPDATE users 
                    SET full_name = ?, email = ?, admin_id_number = ?, security_question = ?
                    WHERE id = ?
                ''', (full_name, user_data['email'], user_data['admin_id'], 
                      user_data['recovery_question'], user_id))
                
                print(f"✅ Updated user profile for ID {user_id}")
                
                # Update password if provided
                if user_data.get('password'):
                    password_hash = self.db_manager.hash_password(user_data['password'])
                    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                                 (password_hash, user_id))
                    print(f"✅ Updated password for user ID {user_id}")
                
                # Update profile photo if provided
                if user_data.get('profile_photo'):
                    cursor.execute('UPDATE users SET profile_photo = ? WHERE id = ?', 
                                 (user_data['profile_photo'], user_id))
                    print(f"✅ Updated profile photo for user ID {user_id}")
                
                # Update security answer if provided
                if user_data.get('security_answer'):
                    security_answer_hash = self.db_manager.hash_password(user_data['security_answer'].lower().strip())
                    cursor.execute('UPDATE users SET security_answer_hash = ? WHERE id = ?', 
                                 (security_answer_hash, user_id))
                    print(f"✅ Updated security answer for user ID {user_id}")
                
                conn.commit()
                print("✅ All database updates committed successfully")
                
            except Exception as e:
                print(f"❌ Database update failed: {e}")
                conn.rollback()
                raise Exception(f"Database update failed: {e}")
            finally:
                conn.close()
            
            # Update page data with new information
            if not self.page.data:
                self.page.data = {}
            self.page.data.update({
                'full_name': full_name,
                'username': user_data['username'],
                'email': user_data['email'],
                'admin_id_number': user_data['admin_id'],
                'profile_photo': user_data.get('profile_photo')
            })
            
            print("✅ Successfully saved user data to database")
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            raise e
