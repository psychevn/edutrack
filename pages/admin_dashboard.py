import flet as ft
from datetime import datetime, timedelta
import json
from database.database_manager import DatabaseManager
from pages.assessment_management import AssessmentManagementPage
from pages.create_assessment import CreateAssessmentPage
from pages.scores_page import ScoresPage

class AdminDashboard:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        self.assessments = []
        self.current_view = "dashboard"
        self.selected_assessment = None
        self.sections = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
        self.post_dialog = None
        # Initialize announcement text field properly
        self.announcement_text = ft.TextField(
            label="What would you like to announce?",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=15,
            border_color="#E8B4CB",
            focused_border_color="#D4817A",
            bgcolor=ft.Colors.WHITE,
            text_size=14,
            value="",  # Initialize with empty value
            hint_text="Type your announcement here..."
        )
        
        # Initialize embedded page instances to preserve state
        self.scores_page = None
        
        # Initialize UI components
        self.init_ui()
        self.load_assessments()
        self.load_dashboard_stats()
    
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
                            "Admin",
                            size=12,
                            color=ft.Colors.WHITE70,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5),
                    padding=ft.padding.symmetric(horizontal=20, vertical=20),
                    alignment=ft.alignment.center
                ),
                
                ft.Divider(color="#fafafa", height=20),
                
                # Navigation items
                ft.Container(
                    content=ft.Column([
                        self.create_nav_item(ft.Icons.PERSON, "User", False),
                        self.create_nav_item(ft.Icons.HOME, "Dashboard", True),
                        self.create_nav_item(ft.Icons.ASSIGNMENT, "Assessments", False),
                        self.create_nav_item(ft.Icons.CAMPAIGN, "Classfeed", False),
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
            bgcolor="#efaaaa",  # Soft pink from screenshot
            padding=ft.padding.all(0),
            margin=ft.margin.only(top=100),
            border_radius=ft.border_radius.only(
                top_left=0,
                top_right=120,
                bottom_left=0,
                bottom_right=0
            )
        )
        
        # Main content area with scrolling support
        self.main_content = ft.Container(
            expand=True,
            bgcolor="#f4f1ec",  # Light beige background
            padding=ft.padding.all(0)  # Remove padding to allow full scroll
        )
        
        # Post creation form (used in modal)
        self.init_post_form()
        
        # Assessment management
        self.init_assessment_management()
        
        # Results view
        self.init_results_view()
        
        # Ensure initial active state on nav
        self.update_nav_active("dashboard")
    
    def create_profile_photo(self):
        """Create profile photo container with user's actual photo or default"""
        import os
        
        # Get user's profile photo path
        profile_photo_path = None
        if self.user_data and isinstance(self.user_data, dict):
            profile_photo_path = self.user_data.get('profile_photo')
            print(f" Admin Dashboard - User data: {self.user_data}")
            print(f" Admin Dashboard - Profile photo path: {profile_photo_path}")
        
        # Check if photo file exists
        if profile_photo_path and os.path.exists(profile_photo_path):
            print(f" Admin Dashboard - Photo file exists: {profile_photo_path}")
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
            print(f"❌ Admin Dashboard - Using default icon (no photo or file not found)")
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
    
    def get_user_display_name(self):
        """Get display name for the current user"""
        if self.user_data and isinstance(self.user_data, dict):
            name = self.user_data.get('full_name', '') or self.user_data.get('name', '')
            username = self.user_data.get('username', '')
            if name:
                return name
            elif username:
                return username.title()
        return "Admin User"
    
    def create_nav_item(self, icon, text, is_active=False):
        """Create navigation item matching screenshot style"""
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
            bgcolor="#bb5862" if is_active else ft.Colors.TRANSPARENT,  # Active background
            border_radius=0
        )
    
    def navigate_to(self, view):
        """Handle navigation"""
        if view == "dashboard":
            self.show_dashboard()
        elif view == "assessments":
            # Show Assessments inline (no route change)
            self.show_assessments_inline()
        elif view == "create_assessment":
            # Show Create Assessment inline (no route change)
            self.show_create_assessment_inline()
        elif view == "classfeed":
            # Show Classfeed inline (no route change)
            self.show_classfeed()
        elif view == "scores":
            self.show_results()
        elif view == "user":
            # Show User Management inline (no route change)
            self.show_user_management_inline()
    
    def show_user_management_inline(self):
        """Render the User Management UI inside the admin workspace without routing."""
        self.current_view = "user"
        self.update_nav_active("user")  # Highlight user button when clicked
        
        # Header with date (matching dashboard style)
        from datetime import datetime
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=28, color="#D4817A"),
                    ft.Text("User", size=24, weight=ft.FontWeight.BOLD, color="#D4817A")
                ], spacing=10),
                ft.Text(
                    datetime.now().strftime("%B %d, %Y"),
                    size=14,
                    color="#D4817A"
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=30)
        )
        
        # Build an instance of AdminUserPage to reuse its UI components
        from pages.admin_user_page import AdminUserPage
        self.admin_user_page = AdminUserPage(self.page, self.db_manager, parent_dashboard=self)
        # Get content only without sidebar
        user_content = self.admin_user_page.get_content_only()
        
        # Combine header and user content
        combined_content = ft.Column([
            header,
            user_content
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        
        # Place inside a container matching admin main content styling
        self.main_content.content = ft.Container(
            content=combined_content,
            expand=True,
            padding=ft.padding.all(40),
            bgcolor="#f4f1ec"
        )
        self.page.update()
    
    def show_assessments_inline(self):
        """Render the Assessment Management UI inside the admin workspace without routing."""
        self.current_view = "assessments"
        self.update_nav_active("assessments")
        
        # Build an instance of AssessmentManagementPage to reuse its UI components
        self.assessment_management_page = AssessmentManagementPage(self.page, self.db_manager)
        # Override the navigation method to show create assessment inline
        self.assessment_management_page.navigate_to_create_assessment = lambda assessment_id=None: self.show_create_assessment_inline(assessment_id)
        # Override the refresh method to work within the admin dashboard
        self.assessment_management_page._refresh_content = self._refresh_assessments_content
        # Get content only without sidebar
        assessment_content = self.assessment_management_page.get_content_only()
        # Place inside a container matching admin main content styling
        self.main_content.content = ft.Container(
            content=assessment_content,
            padding=40,
            bgcolor="#f4f1ec",
            expand=True
        )
        self.page.update()
    
    def _refresh_assessments_content(self):
        """Refresh the assessments content within the admin dashboard"""
        if hasattr(self, 'assessment_management_page'):
            # Reload the assessments data
            self.assessment_management_page.load_assessments()
            self.assessment_management_page.load_stats()
            # Recreate the content
            assessment_content = self.assessment_management_page.get_content_only()
            self.main_content.content = ft.Container(content=assessment_content, padding=40, bgcolor="#f4f1ec", expand=True)
            # Also refresh overall dashboard stats to reflect new submissions/completion
            try:
                self.load_assessments()
                self.load_dashboard_stats()
            except Exception:
                pass
            self.page.update()
    
    def show_create_assessment_inline(self, assessment_id=None):
        """Render the Create Assessment UI inside the admin workspace without routing."""
        print(f"ADMIN: show_create_assessment_inline called with assessment_id: {assessment_id}")
        self.current_view = "create_assessment"
        self.update_nav_active("create_assessment")
        # Build an instance of CreateAssessmentPage to reuse its UI components
        ca = CreateAssessmentPage(self.page, self.db_manager, self.sections, assessment_id)
        # Override the back button to return to assessments inline view
        ca.go_back = lambda e: self.show_assessments_inline()
        # Get content only without sidebar
        create_assessment_content = ca.get_content_only()
        # Place inside a container matching admin main content styling
        inline_container = ft.Container(
            content=create_assessment_content,
            padding=40,
            bgcolor="#f4f1ec"
        )
        self.main_content.content = inline_container
        
        # Load data after the view is created if editing
        if assessment_id is not None:
            print(f"ADMIN: Loading data for assessment_id: {assessment_id}")
            ca.load_data_after_view_created()
        
        self.page.update()
    
    def load_dashboard_stats(self):
        """Load dashboard statistics"""
        # Pull live stats from DB
        try:
            admin_id = self.user_data['id'] if isinstance(self.user_data, dict) and 'id' in self.user_data else None
            stats = self.db_manager.get_admin_dashboard_stats(admin_id) if admin_id is not None else {
                'total_students': 0, 'active_assessments': 0, 'completion_rate': 0, 'new_submissions': 0
            }
            self.total_students = stats.get('total_students', 0)
            self.active_assessments = stats.get('active_assessments', 0)
            self.completion_rate = stats.get('completion_rate', 0)
            self.new_submissions = stats.get('new_submissions', 0)
        except Exception:
            # Fallback to previous behavior if stats query fails
            self.total_students = 0
            self.active_assessments = len([a for a in self.assessments if a.get('is_active', True)])
            self.completion_rate = 0
            self.new_submissions = 0
    
    def create_stat_card(self, title, value, color="#bb5862"):
        """Create statistics card matching the prototype"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    str(value),
                    size=36,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    title,
                    size=14,
                    color=color,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8),
            width=180,
            height=120,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            border=ft.border.all(1, "#efb6aa"),
            padding=20
        )
    
    def create_action_button(self, text, icon, color, on_click):
        """Create action button"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="#bb5862", size=20), 
                ft.Text(text, color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.W_500)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8),
            bgcolor=color,
            border_radius=15,
            border=ft.border.all(2, ft.Colors.WHITE), 
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            on_click=on_click
        )
    
    def show_dashboard(self):
        """Show dashboard view matching the prototype"""
        self.current_view = "dashboard"
        self.update_nav_active("dashboard")
        # Always refresh live stats when opening the dashboard view
        try:
            self.load_assessments()
            self.load_dashboard_stats()
        except Exception:
            pass
        
        # Header with date
        refresh_btn = ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Refresh stats",
                                    on_click=lambda e: (self.load_assessments(), self.load_dashboard_stats(), self.show_dashboard()))
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.HOME, size=28, color="#D4817A"),
                    ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD, color="#D4817A")
                ], spacing=10),
                ft.Row([
                    ft.Text(
                        datetime.now().strftime("%B %d, %Y"),
                        size=14,
                        color="#D4817A"
                    ),
                    refresh_btn
                ], spacing=10)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=30)
        )
        
        # Statistics cards
        stats_row = ft.Row([
            self.create_stat_card("Total Students", self.total_students),
            self.create_stat_card("Active Assessment", self.active_assessments),
            self.create_stat_card("Completion Rate", f"{self.completion_rate}%"),
            self.create_stat_card("New Submissions", self.new_submissions)
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=20)
        
        # Quick Actions section
        quick_actions = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Quick Actions",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="#D4817A"
                ),
                ft.Container(height=15),
                ft.Row([
                    self.create_action_button(
                        "Create Assessment", 
                        ft.Icons.EDIT, 
                        "#efb6aa", 
                        lambda e: self.show_create_assessment()
                    ),
                    self.create_action_button(
                        "View Scores", 
                        ft.Icons.VISIBILITY, 
                        "#efb6aa", 
                        lambda e: self.show_results()
                    ),
                    self.create_action_button(
                        "Classfeed", 
                        ft.Icons.CAMPAIGN, 
                        "#efb6aa", 
                        lambda e: self.show_classfeed()
                    )
                ], spacing=15)
            ]),
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            border=ft.border.all(1, "#efb6aa"),
            padding=30
        )
        
        # Rebuild announcement section completely
        announcement_section = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.CAMPAIGN, size=24, color=ft.Colors.WHITE),
                    ft.Text(
                        "ANNOUNCE SOMETHING TO CLASS",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    )
                ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=20),
                
                # Text field
                self.announcement_text,
                
                ft.Container(height=20),
                
                # Button row
                ft.Row([
                    ft.Container(expand=True),  # Push button to right
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SEND, size=18, color=ft.Colors.WHITE),
                            ft.Text("POST ANNOUNCEMENT", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        style=ft.ButtonStyle(
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=ft.padding.symmetric(horizontal=24, vertical=16),
                            elevation=4,
                            surface_tint_color=ft.Colors.TRANSPARENT
                        ),
                        on_click=lambda e: self.handle_post_announcement(e),  # Explicit lambda
                        width=220,
                        height=55,
                        disabled=False  # Ensure button is enabled
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=0),
            bgcolor="#efb6aa",
            border_radius=20,
            padding=30,
            margin=ft.margin.only(top=10)
        )
        
        # Main dashboard content with scrolling
        dashboard_content = ft.Container(
            content=ft.Column([
                header,
                stats_row,
                ft.Container(height=30),
                quick_actions,
                ft.Container(height=30),
                announcement_section,
                ft.Container(height=50)  # Bottom padding
            ], spacing=0, scroll=ft.ScrollMode.AUTO),  # Enable scrolling
            padding=40,
            bgcolor="#f4f1ec",
            expand=True  # Allow container to expand
        )
        
        self.main_content.content = dashboard_content
        self.page.update()
    
    def handle_post_announcement(self, e):
        """Handle posting announcement - completely rebuilt method"""
        print("=" * 50)
        print("🚀 POST ANNOUNCEMENT BUTTON CLICKED!")
        print("🚀 Event received:", e)
        print("🚀 Button click handler called successfully!")
        print("=" * 50)
        
        try:
            # Get the announcement text
            if not hasattr(self, 'announcement_text') or self.announcement_text is None:
                print("❌ ERROR: announcement_text field not found!")
                self.show_error("Announcement text field not initialized!")
                return
            
            announcement_content = self.announcement_text.value
            print(f"📝 Raw announcement text: '{announcement_content}'")
            
            if not announcement_content or not announcement_content.strip():
                print("❌ ERROR: No announcement text provided")
                self.show_error("Please enter an announcement message!")
                return
            
            announcement_content = announcement_content.strip()
            print(f"✅ Cleaned announcement text: '{announcement_content}'")
            
            # Check user data
            if not self.user_data or not isinstance(self.user_data, dict):
                print("❌ ERROR: No user data available")
                self.show_error("User authentication error!")
                return
            
            user_id = self.user_data.get('id')
            user_name = self.user_data.get('full_name', 'Admin')
            print(f"👤 User ID: {user_id}")
            print(f"👤 User Name: {user_name}")
            
            if not user_id:
                print("❌ ERROR: No user ID found")
                self.show_error("User ID not found!")
                return
            
            # Check database manager
            if not self.db_manager:
                print("❌ ERROR: Database manager not available")
                self.show_error("Database connection error!")
                return
            
            print("💾 Creating announcement in database...")
            
            # Create the announcement
            announcement_id = self.db_manager.create_announcement(
                title="Class Announcement",
                content=announcement_content,
                created_by=user_id
            )
            
            print(f"💾 Database returned announcement ID: {announcement_id}")
            
            if announcement_id and announcement_id > 0:
                # Success! Clear the text field and show success message
                print("✅ SUCCESS: Announcement created successfully!")
                self.announcement_text.value = ""
                self.announcement_text.update()
                self.show_success(f"Announcement posted successfully! All students will see this announcement.")
                print(f"🎉 Announcement #{announcement_id} is now live for all students!")
            else:
                print("❌ ERROR: Failed to create announcement - invalid ID returned")
                self.show_error("Failed to save announcement to database!")
                
        except Exception as ex:
            print(f"💥 EXCEPTION in handle_post_announcement: {ex}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error posting announcement: {str(ex)}")
        
        print("=" * 50)
    
    
    def init_post_form(self):
        """Initialize generic post creation form"""
        self.post_title = ft.TextField(
            label="Post Title",
            prefix_icon=ft.Icons.TITLE,
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        self.post_description = ft.TextField(
            label="Description",
            prefix_icon=ft.Icons.DESCRIPTION,
            multiline=True,
            min_lines=3,
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        self.post_type = ft.Dropdown(
            label="Post Type",
            options=[
                ft.dropdown.Option("assessment", "Assessment"),
                ft.dropdown.Option("file", "File Upload"),
            ],
            value="assessment",
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
            on_change=lambda e: self.update_post_type_visibility()
        )
        
        self.link_assessment_info = ft.Text(
            "Select 'Create Assessment' to build the assessment, then publish as a post.",
            size=12, color=ft.Colors.BLUE_600
        )
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.post_start_date = ft.TextField(
            label="Start Date & Time",
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            hint_text="YYYY-MM-DD HH:MM",
            value=now_str,
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        self.post_end_date = ft.TextField(
            label="End Date & Time",
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            hint_text="YYYY-MM-DD HH:MM",
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        
        self.scheduling_column = ft.Column([self.post_start_date, self.post_end_date], spacing=15)

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        self.selected_file_path = ft.Text("No file selected", size=12, color=ft.Colors.BLUE_600)
        self.pick_file_button = ft.ElevatedButton(
            "Choose File",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=lambda e: self.file_picker.pick_files(allow_multiple=False),
        )
        self.file_section = ft.Column([
            ft.Row([self.pick_file_button, self.selected_file_path], alignment=ft.MainAxisAlignment.START)
        ])
        
        self.post_sections_checks_controls = [ft.Checkbox(label=sec) for sec in self.sections]
        def _build_sections_grid():
            rows = []
            ctrls = self.post_sections_checks_controls
            for i in range(0, len(ctrls), 3):
                rows.append(ft.Row(ctrls[i:i+3], alignment=ft.MainAxisAlignment.START))
            return ft.Column(rows, spacing=8)
        self.post_sections_checks = _build_sections_grid()
        self.publish_post_button = ft.ElevatedButton(
            "Publish",
            icon=ft.Icons.PUBLISH,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_500,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.publish_post
        )
    
    def init_assessment_management(self):
        """Initialize assessment management view"""
        self.assessments_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(10)
        )
    
    def init_results_view(self):
        """Initialize results view"""
        self.results_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(10)
        )
    
    def navigate(self, e):
        """Handle navigation"""
        selected_index = e.control.selected_index
        if selected_index == 0:
            self.show_dashboard()
        elif selected_index == 1:
            self.show_manage_assessments()
        elif selected_index == 2:
            self.show_results()
    
    def open_post_modal(self):
        """Open modal with post creation form"""
        self.post_title.value = ""
        self.post_description.value = ""
        self.post_type.value = "assessment"
        for ctrl in getattr(self, 'post_sections_checks_controls', []):
            ctrl.value = False
        self.selected_file_path.value = "No file selected"
        self.update_post_type_visibility()
        self.post_start_date.value = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.post_end_date.value = ""

        next_btn = ft.TextButton(
            "Next",
            icon=ft.Icons.ARROW_FORWARD,
            on_click=lambda e: self.next_to_create_assessment() if self.post_type.value == "assessment" else None,
            visible=True
        )
        
        actions = [
            ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.post_dialog)),
            next_btn,
            ft.ElevatedButton("Publish", icon=ft.Icons.PUBLISH, on_click=self.publish_post)
        ]

        modal_content = ft.Column([
            self.post_title,
            self.post_description,
            self.scheduling_column,
            self.post_type,
            self.link_assessment_info,
            self.file_section,
            ft.Text("Assign to Sections", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
            self.post_sections_checks,
        ], spacing=12)

        self.post_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create Post"),
            content=modal_content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.post_dialog
        self.post_dialog.open = True
        self.page.update()

    def next_to_create_assessment(self):
        """Navigate to Create Assessment view from modal"""
        if self.post_dialog:
            self.post_dialog.open = False
            self.page.update()
        self._modal_selected_sections = [ctrl.label for ctrl in getattr(self, 'post_sections_checks_controls', []) if getattr(ctrl, 'value', False)]
        self._modal_start_time = self.post_start_date.value
        self._modal_end_time = self.post_end_date.value
        self.show_create_assessment()
    
    def create_assessment_card(self, assessment):
        """Create an assessment card"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ASSIGNMENT, color=ft.Colors.BLUE_500),
                    ft.Column(
                        [
                            ft.Text(assessment['title'], weight=ft.FontWeight.BOLD),
                            ft.Text(assessment['description'][:50] + "..." if len(assessment['description']) > 50 else assessment['description']),
                            ft.Text(f"Duration: {assessment['duration_minutes']} minutes", size=12, color=ft.Colors.BLUE_600)
                        ],
                        expand=True
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.BLUE_300)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=ft.Colors.BLUE_50,
            padding=15,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_200)
        )
    
    def show_create_assessment(self):
        """Show create assessment view (embedded from CreateAssessmentPage)."""
        self.current_view = "create"
        self.update_nav_active("assessments")
        create_page = CreateAssessmentPage(self.page, self.db_manager, self.sections)
        self.main_content.content = create_page.get_content_only()
        self.page.update()

    def update_post_type_visibility(self):
        is_file = self.post_type.value == "file"
        self.file_section.visible = is_file
        self.link_assessment_info.visible = not is_file
        self.page.update()

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            self.selected_file_path.value = e.files[0].path or e.files[0].name
        else:
            self.selected_file_path.value = "No file selected"
        self.page.update()
    
    def add_question(self, e):
        """Add a new question to the form"""
        question_index = len(self.questions_container.controls)
        
        question_type = ft.Dropdown(
            label="Question Type",
            options=[
                ft.dropdown.Option("mcq", "Multiple Choice"),
                ft.dropdown.Option("short_answer", "Short Answer")
            ],
            value="mcq",
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        
        question_text = ft.TextField(
            label="Question Text",
            multiline=True,
            min_lines=2,
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        
        points = ft.TextField(
            label="Points",
            value="1",
            input_filter=ft.NumbersOnlyInputFilter(),
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        
        correct_answer = ft.TextField(
            label="Correct Answer",
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        
        options_field = ft.TextField(
            label="Options (comma-separated for MCQ)",
            hint_text="Option A, Option B, Option C, Option D",
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        
        remove_button = ft.IconButton(
            ft.Icons.DELETE,
            tooltip="Remove Question",
            on_click=lambda e: self.remove_question(question_index)
        )
        
        question_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [ft.Text(f"Question {question_index + 1}", weight=ft.FontWeight.BOLD), remove_button],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    question_type,
                    question_text,
                    ft.Row([points, correct_answer]),
                    options_field
                ],
                spacing=10
            ),
            bgcolor=ft.Colors.BLUE_50,
            padding=15,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_200)
        )
        
        self.questions_container.controls.append(question_card)
        self.page.update()
    
    def remove_question(self, question_index):
        """Remove a question from the form"""
        if 0 <= question_index < len(self.questions_container.controls):
            self.questions_container.controls.pop(question_index)
            for i, control in enumerate(self.questions_container.controls):
                if hasattr(control.content, 'controls') and len(control.content.controls) > 0:
                    if hasattr(control.content.controls[0], 'controls') and len(control.content.controls[0].controls) > 0:
                        control.content.controls[0].controls[0].value = f"Question {i + 1}"
            self.page.update()
    
    def create_assessment(self, e):
        """Create the assessment"""
        if not all([self.assessment_title.value, self.assessment_description.value, self.duration.value]):
            self.show_error("Please fill in all required fields")
            return
        
        if not self.questions_container.controls:
            self.show_error("Please add at least one question")
            return
        
        try:
            assessment_id = self.db_manager.create_assessment(
                title=self.assessment_title.value,
                description=self.assessment_description.value,
                created_by=self.user_data['id'],
                start_time=getattr(self, '_modal_start_time', datetime.now().strftime("%Y-%m-%d %H:%M")),
                end_time=getattr(self, '_modal_end_time', None),
                duration_minutes=int(self.duration.value)
            )
            
            for i, question_card in enumerate(self.questions_container.controls):
                question_data = question_card.content.controls
                
                question_type = question_data[1].value
                question_text = question_data[2].value
                points = int(question_data[3].controls[0].value)
                correct_answer = question_data[3].controls[1].value
                options = question_data[4].value if question_type == "mcq" else None
                
                self.db_manager.add_question(
                    assessment_id=assessment_id,
                    question_text=question_text,
                    question_type=question_type,
                    points=points,
                    correct_answer=correct_answer,
                    options=options,
                    order_index=i
                )
            
            selected_sections = getattr(self, '_modal_selected_sections', None)
            if not selected_sections:
                self.show_error("Please select at least one section to assign this assessment")
                return
            post_id = self.db_manager.create_post(
                title=self.assessment_title.value,
                description=self.assessment_description.value,
                post_type="assessment",
                created_by=self.user_data['id'],
                assessment_id=assessment_id,
                file_path=None
            )
            self.db_manager.assign_post_sections(post_id, selected_sections)

            self.show_success("Assessment created successfully!")
            self.load_assessments()
            self.show_dashboard()
            
        except Exception as ex:
            self.show_error(f"Error creating assessment: {str(ex)}")

    def publish_post(self, e):
        """Publish a generic post"""
        title = self.post_title.value.strip()
        description = self.post_description.value.strip()
        ptype = self.post_type.value
        if not title or not description:
            self.show_error("Please enter title and description")
            return
        selected_sections = [cb.label for cb in self.post_sections_checks.controls if getattr(cb, 'value', False)]
        if not selected_sections:
            self.show_error("Please select at least one section")
            return
        try:
            file_path_to_store = None
            if ptype == "file":
                import os, shutil
                src = self.selected_file_path.value
                if not src or src == "No file selected":
                    self.show_error("Please choose a file to upload")
                    return
                uploads_dir = os.path.join(os.getcwd(), "uploads")
                os.makedirs(uploads_dir, exist_ok=True)
                filename = os.path.basename(src)
                dest = os.path.join(uploads_dir, filename)
                try:
                    shutil.copyfile(src, dest)
                except Exception:
                    pass
                file_path_to_store = dest if os.path.exists(dest) else src

            post_id = self.db_manager.create_post(
                title=title,
                description=description,
                post_type=ptype,
                created_by=self.user_data['id'],
                assessment_id=None,
                file_path=file_path_to_store
            )
            self.db_manager.assign_post_sections(post_id, selected_sections)
            self.show_success("Post published successfully!")
            if self.post_dialog:
                self.post_dialog.open = False
            self.show_dashboard()
        except Exception as ex:
            self.show_error(f"Error publishing post: {str(ex)}")
    
    def show_manage_assessments(self):
        """Show manage assessments view"""
        self.current_view = "manage"
        self.load_assessments()
        
        # Update sidebar navigation highlighting
        self.update_sidebar_navigation("assessments")
        
        manage_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ASSIGNMENT, size=30, color="#D4817A"),
                                ft.Text(
                                    "Manage Assessments",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color="#D4817A"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START
                        ),
                        padding=ft.padding.only(bottom=20)
                    ),
                    
                    ft.Container(
                        content=self.assessments_list,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15,
                        border=ft.border.all(1, "#E8B4CB"),
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color="#E8B4CB30",
                            offset=ft.Offset(0, 2)
                        ),
                        expand=True
                    )
                ],
                spacing=20
            ),
            padding=40,
            bgcolor="#f4f1ec",
            expand=True
        )
        
        self.main_content.content = manage_content
        self.page.update()
    
    def show_results(self):
        """Show results view (embedded from ScoresPage)."""
        self.current_view = "results"
        self.update_nav_active("scores")
        
        # Preserve existing scores page instance if it exists
        if not hasattr(self, 'scores_page') or self.scores_page is None:
            # Create a fresh instance of ScoresPage only if needed
            self.scores_page = ScoresPage(self.page, self.db_manager)
            # Set parent dashboard reference for embedded navigation
            self.scores_page.parent_dashboard = self
        
        scores_content = self.scores_page.get_content_only()
        self.main_content.content = ft.Container(
            content=scores_content, 
            padding=40, 
            bgcolor="#f4f1ec", 
            expand=True
        )
        # Force a complete page refresh
        self.page.update()
        try:
            self.main_content.update()
        except:
            # If main_content update fails, just continue
            pass
    
    def show_student_scores_embedded(self, assessment_id: int):
        """Show student scores list embedded within admin dashboard - NO VIEW CLEARING"""
        print(f"DEBUG: Embedding student scores for assessment {assessment_id}")
        self.current_view = "student_scores"
        
        # Create student scores content
        from pages.student_scores_list_page import StudentScoresListPage
        student_scores_page = StudentScoresListPage(self.page, self.db_manager, assessment_id)
        student_scores_page.parent_dashboard = self
        
        # Get assessment details for title
        assessment_details = self.db_manager.get_assessment_by_id(assessment_id)
        assessment_title = assessment_details.get('title', f'Assessment {assessment_id}') if assessment_details else f'Assessment {assessment_id}'
        
        # Create back button header with assessment title
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#D4817A",
                        icon_size=24,
                        on_click=lambda e: self.show_results()
                    ),
                    ft.Text("Back to Scores", size=14, color="#D4817A"),
                    ft.Container(expand=True)
                ]),
                ft.Container(height=10),  # Spacing
                ft.Text(assessment_title, size=18, weight=ft.FontWeight.BOLD, color="#D4817A"),
                ft.Text("Student Scores", size=14, color="#666666")
            ], spacing=5),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            margin=ft.margin.only(bottom=15)
        )
        
        # Embed student scores content - ONLY UPDATE CONTENT, NO VIEW CLEARING
        student_content = ft.Column([
            header,
            student_scores_page.create_search_field(),
            student_scores_page.create_students_table()
        ], spacing=15)
        
        # Update main content only - this is the key to preventing transitions
        self.main_content.content = ft.Container(
            content=student_content,
            padding=ft.padding.all(20),
            expand=True,
            bgcolor="#f4f1ec"
        )
        # Only update the page, don't clear or manipulate views
        self.page.update()
        print(f"DEBUG: Student scores embedded successfully - NO TRANSITIONS")
    
    def update_nav_active(self, view_key: str):
        """Update sidebar nav items to reflect active selection.
        view_key should be one of: 'dashboard', 'assessments', 'classfeed', 'scores', 'user'.
        """
        try:
            # sidebar.content is a Column: [profile, divider, nav_container, spacer, logout]
            nav_container = self.sidebar.content.controls[2]
            nav_items = nav_container.content.controls  # list of Containers from create_nav_item
            keys = ["user", "dashboard", "assessments", "classfeed", "scores"]
            for idx, item in enumerate(nav_items):
                is_active = (keys[idx] == view_key)
                # Background
                item.bgcolor = "#bb5862" if is_active else ft.Colors.TRANSPARENT
                # Child TextButton -> Row -> [Icon, Text]
                btn = item.content
                row = btn.content
                icon = row.controls[0]
                text = row.controls[1]
                icon.color = ft.Colors.WHITE if is_active else ft.Colors.WHITE70
                text.color = ft.Colors.WHITE if is_active else ft.Colors.WHITE70
                text.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL
            self.page.update()
        except Exception:
            # If structure changes, avoid crashing
            pass

    def update_sidebar_navigation(self, active_view):
        """Deprecated: kept for compatibility but no-op since we now use update_nav_active."""
        return
    
    def load_assessments(self):
        """Load assessments from database"""
        self.assessments = self.db_manager.get_assessments(role='admin')
        
        self.assessments_list.controls.clear()
        for assessment in self.assessments:
            self.assessments_list.controls.append(
                self.create_management_assessment_card(assessment)
            )
    
    def create_management_assessment_card(self, assessment):
        """Create assessment card for management view"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ASSIGNMENT, color="#D4817A"),
                    ft.Column(
                        [
                            ft.Text(assessment['title'], weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(assessment['description'], color="#D4817A"),
                            ft.Text(f"Duration: {assessment['duration_minutes']} minutes", size=12, color="#D4817A")
                        ],
                        expand=True
                    ),
                    ft.Row(
                        [
                            ft.IconButton(ft.Icons.EDIT, tooltip="Edit", icon_color="#D4817A"),
                            ft.IconButton(ft.Icons.DELETE, tooltip="Delete", icon_color=ft.Colors.RED_500),
                            ft.IconButton(ft.Icons.VISIBILITY, tooltip="View Results", icon_color="#D4817A")
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor="#FFE8E8",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#E8B4CB")
        )
    
    def show_error(self, message: str):
        """Show error message"""
        # Create error snackbar
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_400
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def show_success(self, message: str):
        """Show success message"""
        # Create success snackbar
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_400
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def logout(self, e):
        """Handle logout"""
        self.page.data = None
        self.page.go("/")
    
    def show_submission_grading_embedded(self, assessment_id: int, submission_id: int):
        """Show submission grading embedded within admin dashboard - NO VIEW CLEARING"""
        print(f"DEBUG: Embedding grading for submission {submission_id}")
        self.current_view = "grading"
        
        # Create grading content
        from pages.student_submission_grading_page import StudentSubmissionGradingPage
        grading_page = StudentSubmissionGradingPage(self.page, self.db_manager, assessment_id, submission_id)
        grading_page.parent_dashboard = self
        
        # Get submission details for student name
        submission_details = self.db_manager.get_submission_details(submission_id)
        student_name = submission_details.get('student_name', 'Unknown Student') if submission_details else 'Unknown Student'
        
        # Create back button header with student name
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#D4817A",
                        icon_size=24,
                        on_click=lambda e: self.show_student_scores_embedded(assessment_id)
                    ),
                    ft.Text("Back to Students", size=14, color="#D4817A"),
                    ft.Container(expand=True)
                ]),
                ft.Container(height=10),  # Spacing
                ft.Text(f"Grading: {student_name}", size=18, weight=ft.FontWeight.BOLD, color="#D4817A"),
                ft.Text(f"Submission ID: {submission_id}", size=14, color="#666666")
            ], spacing=5),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            margin=ft.margin.only(bottom=15)
        )
        
        # Embed grading content - ONLY UPDATE CONTENT, NO VIEW CLEARING
        grading_content = ft.Column([
            header,
            grading_page.create_assessment_info_header(),
            grading_page.create_grading_interface()
        ], spacing=15)
        
        # Update main content only - this is the key to preventing transitions
        self.main_content.content = ft.Container(
            content=grading_content,
            padding=ft.padding.all(20),
            expand=True,
            bgcolor="#f4f1ec"
        )
        # Only update the page, don't clear or manipulate views
        self.page.update()
        print(f"DEBUG: Grading embedded successfully - NO TRANSITIONS")
    
    def get_view(self):
        """Return the admin dashboard view"""
        self.show_dashboard()
        
        return ft.View(
            "/admin",
            [
                ft.Container(
                    content=ft.Row(
                        [
                            self.sidebar,
                            ft.Container(self.main_content, expand=True)
                        ],
                        expand=True,
                        spacing=0
                    ),
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )

    def show_announcements_manager(self):
        """Show announcements manager view"""
        try:
            print("🔄 Loading announcements manager...")
            self.current_view = "announcements"
            self.update_nav_active("announcements")
            
            # Build an instance of AnnouncementPage
            from pages.announcement_page import AnnouncementPage
            self.announcement_page = AnnouncementPage(self.page, self.db_manager)
            
            # Override the go_back_to_dashboard method to return to dashboard
            self.announcement_page.go_back_to_dashboard = lambda e: self.show_dashboard()
            
            # Override the refresh_content method to properly refresh the embedded view
            def refresh_embedded_announcements():
                self.announcement_page.load_announcements()
                announcement_content = self.announcement_page.get_content_only()
                self.main_content.content = ft.Container(
                    content=announcement_content, 
                    padding=40, 
                    bgcolor="#f4f1ec", 
                    expand=True
                )
                self.page.update()
            
            self.announcement_page.refresh_content = refresh_embedded_announcements
            
            # Get content only without sidebar
            announcement_content = self.announcement_page.get_content_only()
            
            # Place inside a container matching admin main content styling
            self.main_content.content = ft.Container(
                content=announcement_content, 
                padding=40, 
                bgcolor="#f4f1ec", 
                expand=True
            )
            self.page.update()
            print(" Announcements manager loaded successfully")
            
        except Exception as e:
            print(f" Error loading announcements manager: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error loading announcements: {e}")
    
    def show_classfeed(self):
        """Show classfeed view (replaces announcement management)"""
        try:
            print("🔄 Loading classfeed...")
            self.current_view = "classfeed"
            self.update_nav_active("classfeed")
            
            # Force reload the module to ensure latest changes
            import importlib
            import sys
            if 'pages.classfeed_page' in sys.modules:
                importlib.reload(sys.modules['pages.classfeed_page'])
            
            # Build an instance of ClassfeedPage
            from pages.classfeed_page import ClassfeedPage
            self.classfeed_page = ClassfeedPage(self.page, self.db_manager)
            
            # Override the go_back_to_dashboard method to return to dashboard
            self.classfeed_page.go_back_to_dashboard = lambda e: self.show_dashboard()
            
            # Override the refresh_content method to properly refresh the embedded view
            def refresh_embedded_classfeed():
                self.classfeed_page.load_announcements()
                self.classfeed_page.load_materials()
                classfeed_content = self.classfeed_page.get_content_only()
                self.main_content.content = ft.Container(
                    content=classfeed_content, 
                    padding=40, 
                    bgcolor="#f4f1ec", 
                    expand=True
                )
                self.page.update()
            
            self.classfeed_page.refresh_content = refresh_embedded_classfeed
            
            # Get content only without sidebar
            classfeed_content = self.classfeed_page.get_content_only()
            
            # Place inside a container matching admin main content styling
            self.main_content.content = ft.Container(
                content=classfeed_content, 
                padding=40, 
                bgcolor="#f4f1ec", 
                expand=True
            )
            self.page.update()
            print("✅ Classfeed loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading classfeed: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error loading classfeed: {e}")