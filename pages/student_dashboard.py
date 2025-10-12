import flet as ft
from datetime import datetime, timedelta
import json
from database.database_manager import DatabaseManager

class StudentDashboard:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        self.assessments = []
        self.posts = []
        self.materials = []  # Add materials list
        self.pending_count = 0
        self.completed_count = 0
        self.current_view = "dashboard"
        self.current_assessment = None
        self.current_questions = []
        self.answers = {}
        self.timer_seconds = 0
        self.timer_active = False
        # Per-question mode state
        self.per_question_mode = False
        self.current_question_index = 0
        self.per_question_seconds = 0
        self.per_question_remaining = 0
        self.per_question_slices = []
        self.progress_bar = None
        self.progress_text = None
        self.next_button = None
        self.question_title = None
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        self.date_picker = ft.DatePicker(
            on_change=lambda e: print("Selected date:", e.control.value)
        )
        self.page.overlay.append(self.date_picker)
        self._pending_upload_post_id = None
        self.selected_nav = 0
        # Initialize UI components
        self.init_ui()
        self.load_assessments()
        self.load_announcements()  # Load announcements as well
        self.load_materials()  # Load class materials
        # Shared state for calendar
        self._calendar_display_month = None
        self._calendar_display_year = None
    
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
        """Initialize UI components with modern design"""
        # Left sidebar
        self.sidebar = ft.Container(
            content=ft.Column([
                # Profile section
                ft.Container(
                content=ft.Column([
                    # Profile photo container - ensure perfect centering
                    ft.Container(
                        content=self.create_profile_photo(),
                        alignment=ft.alignment.center,  # FIX: Explicit center alignment
                        width=240,  # FIX: Match sidebar width for perfect centering
                    ),
                    # Name text - ensure perfect centering
                    ft.Container(
                        content=ft.Text(
                            f"{self.user_data.get('full_name', 'Student') if self.user_data else 'Student'}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,  # FIX: Explicit center alignment
                        width=240,  # FIX: Match sidebar width for perfect centering
                    ),
                    # Role text - ensure perfect centering
                    ft.Container(
                        content=ft.Text(
                            "Student",
                            size=12,
                            color=ft.Colors.WHITE70,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,  # FIX: Explicit center alignment
                        width=240,  # FIX: Match sidebar width for perfect centering
                    )
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Column center alignment
                spacing=5),
                padding=ft.padding.all(20),
                alignment=ft.alignment.center  # FIX: Container-level center alignment
            ),
            
            ft.Divider(color="#fafafa", height=20),
            
            # Navigation items
            ft.Container(
                content=ft.Column([
                    self.create_nav_item(ft.Icons.PERSON_OUTLINED, "User", 0),
                    self.create_nav_item(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", 1),
                    self.create_nav_item(ft.Icons.FEED, "Classfeed", 2),
                    self.create_nav_item(ft.Icons.ASSIGNMENT_OUTLINED, "Assessments", 3),
                    self.create_nav_item(ft.Icons.STAR_OUTLINE, "Scores", 4),
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
        bgcolor="#efaaaa",  # Pink color from the design
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
            bgcolor="#f4f1ec",
            padding=ft.padding.all(50)
        )
        
        # Timer display
        self.timer_display = ft.Text(
            "00:00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.RED_500
        )
        
        # Exam taking components
        self.init_exam_components()
        
        # Set initial selected nav item (Dashboard)
        self.selected_nav = 1
        # Track which assessment cards are expanded (to show TAKE/RESULT)
        self.expanded_cards = set()
    
    def create_nav_item(self, icon, text, index):
        """Create a navigation item"""
        is_selected = index == self.selected_nav
        
        return ft.Container(
            content=ft.TextButton(
                content=ft.Row([
                    ft.Icon(
                        icon,
                        color=ft.Colors.WHITE if is_selected else ft.Colors.WHITE70,
                        size=20
                    ),
                    ft.Text(
                        text,
                        color=ft.Colors.WHITE if is_selected else ft.Colors.WHITE70,
                        size=14,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL
                    )
                ], alignment=ft.MainAxisAlignment.START),
                on_click=lambda e, idx=index: self.navigate_to(idx),
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    overlay_color=ft.Colors.WHITE10,
                    shape=ft.RoundedRectangleBorder(radius=0)
                )
            ),
            bgcolor="#bb5862" if is_selected else ft.Colors.TRANSPARENT,
            border_radius=0,
            on_click=lambda e, idx=index: self.navigate_to(idx)
        )
    
    def navigate_to(self, index):
        """Handle navigation"""
        # Block navigation while in exam mode
        if getattr(self, 'per_question_mode', False):
            return
        
        try:
            self.selected_nav = index
            self.update_nav_items()
            
            if index == 0:
                # Show user content within the same page structure
                self.show_user_content()
            elif index == 1:
                self.show_dashboard()
            elif index == 2:
                # Show posts content within the same page structure
                self.show_posts_content()
            elif index == 3:
                # Navigate to assessments
                print("Navigating to Assessments tab")
                # Show a temporary placeholder so user immediately sees a change
                self.main_content.content = ft.Container(
                    content=ft.Text("Loading assessments...", size=16),
                    alignment=ft.alignment.center,
                    expand=True,
                )
                self.page.update()
                self.show_available_exams()
            elif index == 4:
                self.show_results()
        except Exception as e:
            print(f"Error in navigation: {e}")
            # Fallback to dashboard if navigation fails
            try:
                self.show_dashboard()
            except Exception as e2:
                print(f"Error in fallback navigation: {e2}")
    
    def update_nav_items(self):
        """Update navigation items appearance (safe version, matches AdminDashboard style)"""
        try:
            nav_container = self.sidebar.content.controls[2]  # Nav items wrapper
            nav_items = nav_container.content.controls

            for i, nav_item in enumerate(nav_items):
                if not nav_item:
                    continue

                is_selected = i == self.selected_nav
                nav_item.bgcolor = "#bb5862" if is_selected else ft.Colors.TRANSPARENT

                # Dig into button -> row -> [icon, text]
                if hasattr(nav_item, "content") and nav_item.content:
                    button = nav_item.content
                    if hasattr(button, "content") and button.content:
                        row = button.content
                        if hasattr(row, "controls") and len(row.controls) >= 2:
                            icon, text = row.controls[0], row.controls[1]
                            icon.color = ft.Colors.WHITE if is_selected else ft.Colors.WHITE70
                            text.color = ft.Colors.WHITE if is_selected else ft.Colors.WHITE70
                            text.weight = ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL

                            # Special case: add pending badge on "Assessments"
                            if i == 3:
                                base_label = "Assessments"
                                badge = f" ({self.pending_count})" if self.pending_count > 0 else ""
                                text.value = base_label + badge

            self.page.update()

        except Exception as ex:
            print(f"update_nav_items error: {ex}")

    
    def init_exam_components(self):
        """Initialize exam taking components"""
        self.question_container = ft.Column([])
        self.submit_button = ft.ElevatedButton(
            "Submit Exam",
            icon=ft.Icons.SEND,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_500,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=25),
                padding=ft.padding.symmetric(horizontal=30, vertical=15)
            ),
            on_click=self.submit_exam
        )
    
    def show_dashboard(self):
        """Show dashboard view with modern design"""
        self.current_view = "dashboard"
        
        # Get statistics (kept in attributes for reuse)
        total_assessments = len(self.assessments)
        available_assessments = self.pending_count
        submitted_assessments = self.completed_count
        
        # Dashboard header
        from datetime import datetime
        header = self._build_section_header(ft.Icons.DASHBOARD, "Dashboard")
        
        # Statistics cards row
        stats_row = ft.Row([
            self.create_stat_card_modern(str(self.pending_count), "Pending Assessment", "#D4817A"),
            self.create_stat_card_modern(str(self.completed_count), "Completed Assessment", "#D4817A"),
        ], spacing=30)
        
        # Interactive calendar widget (replaces static card)
        today = datetime.now()
        if self._calendar_display_month is None:
            self._calendar_display_month = today.month
            self._calendar_display_year = today.year
        calendar_card = self._build_calendar_widget()
        
        # Top section with stats and calendar
        top_section = ft.Row([
            ft.Column([
                stats_row,
            ], expand=True),
            calendar_card
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=30)
        
        # Announcements Section (from Admin/Teacher)
        if self.announcements:
            announcement_cards = []
            for i, announcement in enumerate(self.announcements[:3]):  # Show only 3 on dashboard
                announcement_cards.append(
                    self.create_enhanced_announcement_card(announcement, i)
                )
            
            announcements_content = ft.Column([
                ft.Column(announcement_cards, spacing=12),
                ft.Container(height=15),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.VISIBILITY, size=16, color=ft.Colors.WHITE),
                            ft.Text("View All Announcements", size=14, color=ft.Colors.WHITE)
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        style=ft.ButtonStyle(
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=ft.padding.symmetric(horizontal=20, vertical=12)
                        ),
                        on_click=self.show_all_announcements
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            f"{len(self.announcements)} total",
                            size=12,
                            color="#9CA3AF",
                            weight=ft.FontWeight.W_500
                        ),
                        alignment=ft.alignment.center_right
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=0)
        else:
            announcements_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=48, color="#D1D5DB"),
                    ft.Container(height=12),
                    ft.Text(
                        "No announcements yet",
                        size=16,
                        color="#9CA3AF",
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Text(
                        "Check back later for updates from your instructors",
                        size=12,
                        color="#D1D5DB",
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                padding=ft.padding.all(40),
                bgcolor="#FAFAFA",
                border_radius=16,
                border=ft.border.all(1, "#F3F4F6"),
                alignment=ft.alignment.center
            )
        
        announcements_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CAMPAIGN, size=22, color=ft.Colors.WHITE),
                        width=44,
                        height=44,
                        bgcolor="#D4817A",
                        border_radius=22,
                        alignment=ft.alignment.center
                    ),
                    ft.Text(
                        "Announcements",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#1F2937"
                    ),
                    ft.Container(expand=True),
                    # Notification badge for unread announcements
                    ft.Container(
                        content=ft.Text(
                            str(self.unread_announcements_count) if self.unread_announcements_count > 0 else "",
                            size=12,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD
                        ),
                        width=24,
                        height=24,
                        bgcolor=ft.Colors.RED_500,
                        border_radius=12,
                        alignment=ft.alignment.center,
                        visible=self.unread_announcements_count > 0
                    )
                ], spacing=12, alignment=ft.MainAxisAlignment.START),
                ft.Container(height=20),
                announcements_content
            ], spacing=0),
            padding=ft.padding.all(24),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            border=ft.border.all(1, "#F3F4F6"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )
        
        # Class Materials section (replaces Recent Posts)
        # Refresh materials to get the latest uploaded materials from admin
        try:
            self.load_materials()
        except Exception:
            pass
        
        recent_materials = (self.materials or [])[:3]  # Show latest 3 materials
        if recent_materials:
            material_cards = [self.create_material_card_modern(m) for m in recent_materials]
            materials_body = ft.Column(material_cards, spacing=10)
        else:
            materials_body = ft.Container(
                content=ft.Text(
                    "No class materials available",
                    size=14,
                    color=ft.Colors.BLACK54
                ),
                alignment=ft.alignment.center,
                height=100
            )
        materials_card = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Class Materials",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="#D4817A"
                ),
                ft.Container(height=10),
                materials_body
            ], spacing=15),
            padding=ft.padding.all(20),
            border=ft.border.all(1, "#F3F4F6"),
            border_radius=15,
            bgcolor=ft.Colors.WHITE
        )
        
        # Main dashboard layout with standardized structure
        content_body = ft.Column([
            top_section,
            ft.Container(height=30),
            announcements_section,
            ft.Container(height=30),
            materials_card
        ], spacing=0, scroll=ft.ScrollMode.AUTO)
        
        # Standardized layout: header + scrollable content
        dashboard_content = ft.Column([
            header,  # Fixed header at top
            ft.Container(
                content=content_body,
                expand=True,
                padding=ft.padding.all(0)
            )
        ], spacing=0, expand=True)
        
        self.main_content.content = dashboard_content
        self.page.update()

    def _build_calendar_widget(self):
        import calendar as cal
        from datetime import datetime
        month = self._calendar_display_month
        year = self._calendar_display_year
        today = datetime.now()
        month_matrix = cal.monthcalendar(year, month)
        month_name = cal.month_name[month]
        
        # Track selected date (if not already set)
        if not hasattr(self, '_selected_date'):
            self._selected_date = None

        def go_prev(e):
            m, y = self._calendar_display_month, self._calendar_display_year
            if m == 1:
                self._calendar_display_month, self._calendar_display_year = 12, y - 1
            else:
                self._calendar_display_month = m - 1
            self.show_dashboard()

        def go_next(e):
            m, y = self._calendar_display_month, self._calendar_display_year
            if m == 12:
                self._calendar_display_month, self._calendar_display_year = 1, y + 1
            else:
                self._calendar_display_month = m + 1
            self.show_dashboard()
        
        def go_today(e):
            self._calendar_display_month = today.month
            self._calendar_display_year = today.year
            self._selected_date = None
            self.show_dashboard()

        # Enhanced header with today button on the right
        header = ft.Row([
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT, 
                on_click=go_prev, 
                icon_color="#5D4E37",
                icon_size=20,
                tooltip="Previous month"
            ),
            ft.Column([
                ft.Text(
                    month_name, 
                    size=16, 
                    weight=ft.FontWeight.BOLD, 
                    color="#5D4E37",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    str(year), 
                    size=12, 
                    color="#FFFFFF",
                    text_align=ft.TextAlign.CENTER
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT, 
                on_click=go_next, 
                icon_color="#5D4E37",
                icon_size=20,
                tooltip="Next month"
            ),
            ft.Container(width=8),  # Spacing
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.TODAY, size=14, color="#8B7355"),
                    ft.Text("Today", size=11, color="#FFFFFF", weight=ft.FontWeight.W_500)
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                on_click=go_today,
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    shape=ft.RoundedRectangleBorder(radius=8),
                    bgcolor={"": ft.Colors.TRANSPARENT, "hovered": "#5D4E37"}
                )
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Day headers with improved styling - wider spacing
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_headers = ft.Row([
            ft.Container(
                content=ft.Text(
                    d, 
                    size=11, 
                    weight=ft.FontWeight.W_600, 
                    color="#5D4E37"
                ), 
                width=38, 
                alignment=ft.alignment.center
            )
            for d in days
        ], spacing=4)

        # Enhanced grid with hover effects and selection
        grid_rows = []
        for week in month_matrix:
            row = ft.Row([], spacing=2)
            for day in week:
                is_today = (day == today.day and month == today.month and year == today.year)
                is_selected = (self._selected_date and 
                             day == self._selected_date[0] and 
                             month == self._selected_date[1] and 
                             year == self._selected_date[2])
                
                if day == 0:
                    cell = ft.Container(width=38, height=36)
                else:
                    def create_tap_handler(d=day):
                        def on_tap(e):
                            self._selected_date = (d, month, year)
                            self.show_dashboard()
                        return on_tap
                    
                    # Determine styling based on state
                    if is_today:
                        bg_color = "#5D4E37"
                        text_color = ft.Colors.WHITE
                        border_radius = 17
                        font_weight = ft.FontWeight.BOLD
                    elif is_selected:
                        bg_color = "#F3C9C0"
                        text_color = "#5D4E37"
                        border_radius = 17
                        font_weight = ft.FontWeight.BOLD
                    else:
                        bg_color = ft.Colors.TRANSPARENT
                        text_color = "#374151"
                        border_radius = 8
                        font_weight = ft.FontWeight.NORMAL
                    
                    cell = ft.Container(
                        content=ft.Text(
                            str(day), 
                            size=13, 
                            color=text_color, 
                            weight=font_weight
                        ),
                        width=38,
                        height=36,
                        bgcolor=bg_color,
                        border_radius=border_radius,
                        alignment=ft.alignment.center,
                        ink=True,
                        on_click=create_tap_handler(day),
                        on_hover=lambda e, d=day: self._handle_calendar_hover(e, d) if not is_today and not is_selected else None
                    )
                row.controls.append(cell)
            grid_rows.append(row)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=20, color="#8B7355"),
                    ft.Text("Calendar", size=18, weight=ft.FontWeight.BOLD, color="#5D4E37"),
                ], spacing=8),
                ft.Container(height=11),
                header,
                ft.Container(height=11),
                day_headers,
                ft.Container(height=11),
                ft.Column(grid_rows, spacing=3)
            ], spacing=0),
            width=330,
            height=335,
            padding=ft.padding.all(18),
            bgcolor="#cfc6b5",
            border_radius=16,
            border=ft.border.all(1, "#B8AE9D"),
            shadow=ft.BoxShadow(
                spread_radius=0, 
                blur_radius=12, 
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), 
                offset=ft.Offset(0, 4)
            )
        )
    
    def _handle_calendar_hover(self, e, day):
        """Handle hover effect on calendar days"""
        if e.data == "true":  # Mouse enter
            e.control.bgcolor = "#FEF3F2"
        else:  # Mouse leave
            e.control.bgcolor = ft.Colors.TRANSPARENT
        e.control.update()
    
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
    
    def create_stat_card_modern(self, value: str, title: str, color: str):
        """Create a modern statistics card"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    value,
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    title,
                    size=14,
                    color=ft.Colors.BLACK87,
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10),
            width=200,
            height=120,
            padding=ft.padding.all(20),
            border=ft.border.all(1, color),
            border_radius=15,
            bgcolor=ft.Colors.WHITE
        )
    
    def navigate(self, e):
        """Handle navigation - kept for compatibility"""
        self.navigate_to(e.control.selected_index)
    
    def show_posts(self):
        """Show posts and announcements filtered by student's section"""
        print("=== SHOW_POSTS CALLED IN STUDENT DASHBOARD ===")
        self.current_view = "posts"
        self.load_posts()
        self.load_announcements()  # Load announcements as well
        self.load_materials()  # Load materials as well
        self.load_assessments()  # Load assessments as well
        print(f"Loaded {len(self.announcements)} announcements")
        print(f"Loaded {len(getattr(self, 'materials', []))} materials")

        # Classfeed header
        header = ft.Row([
            ft.Icon(ft.Icons.FEED, size=28, color="#D4817A"),
            ft.Text(
                "Classfeed",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="#D4817A"
            ),
            ft.Container(expand=True),
            ft.Text(datetime.now().strftime("%B %d, %Y"), size=14, color="#D4817A"),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Create section references for scrolling
        announcements_ref = ft.Ref[ft.Container]()
        materials_ref = ft.Ref[ft.Container]()
        assessments_ref = ft.Ref[ft.Container]()
        main_scroll_ref = ft.Ref[ft.Column]()
        
        # Section navigation buttons with enhanced UI
        def scroll_to_section(section_name):
            """Scroll to a specific section with smooth animation"""
            print(f"Scrolling to {section_name} section")
            try:
                if main_scroll_ref.current:
                    if section_name == "announcements":
                        main_scroll_ref.current.scroll_to(key="announcements_section", duration=500)
                    elif section_name == "materials":
                        main_scroll_ref.current.scroll_to(key="materials_section", duration=500)
                    elif section_name == "assessments":
                        main_scroll_ref.current.scroll_to(key="assessments_section", duration=500)
                    self.page.update()
                    print(f"Successfully scrolled to {section_name}")
                else:
                    print("Main scroll reference not found")
            except Exception as e:
                print(f"Scroll error: {e}")
            
        # Enhanced section navigation with modern design
        section_nav = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Quick Navigation",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color="#ba5963",
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=8),
                ft.Row([
                    # Announcements Button - Enhanced
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Icon(ft.Icons.CAMPAIGN, size=24, color="#D4817A"),
                                width=50,
                                height=50,
                                bgcolor="#FFF5F5",
                                border_radius=25,
                                alignment=ft.alignment.center,
                                border=ft.border.all(2, "#F3C9C0")
                            ),
                            ft.Container(height=8),
                            ft.Text(
                                "Announcements",
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color="#D4817A",
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(12),
                        border_radius=15,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        ),
                        on_click=lambda e: scroll_to_section("announcements"),
                        ink=True
                    ),
                    
                    # Materials Button - Enhanced
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Icon(ft.Icons.FOLDER, size=24, color="#4CAF50"),
                                width=50,
                                height=50,
                                bgcolor="#F0FDF4",
                                border_radius=25,
                                alignment=ft.alignment.center,
                                border=ft.border.all(2, "#BBF7D0")
                            ),
                            ft.Container(height=8),
                            ft.Text(
                                "Materials",
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color="#4CAF50",
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(12),
                        border_radius=15,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        ),
                        on_click=lambda e: scroll_to_section("materials"),
                        ink=True
                    ),
                    
                    # Assessments Button - Enhanced
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Icon(ft.Icons.ASSIGNMENT, size=24, color="#FF9800"),
                                width=50,
                                height=50,
                                bgcolor="#FEF3E2",
                                border_radius=25,
                                alignment=ft.alignment.center,
                                border=ft.border.all(2, "#FED7AA")
                            ),
                            ft.Container(height=8),
                            ft.Text(
                                "Assessments",
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color="#FF9800",
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(12),
                        border_radius=15,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        ),
                        on_click=lambda e: scroll_to_section("assessments"),
                        ink=True
                    )
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(20),
            bgcolor="#efaaaa",
            border_radius=20,
            margin=ft.margin.only(bottom=25),
            border=ft.border.all(1, "#E5E7EB")
        )

        # Create content sections
        content_sections = []

        # Announcements Section (from Admin/Teacher)
        if self.announcements:
            announcement_cards = []
            for announcement in self.announcements[:5]:  # Show latest 5 announcements
                announcement_cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CAMPAIGN, size=20, color=ft.Colors.WHITE),
                                    width=50,
                                    height=50,
                                    bgcolor="#D4817A",
                                    border_radius=20,
                                    alignment=ft.alignment.center
                                ),
                                ft.Column([
                                    ft.Text(
                                        announcement.get('title', 'Announcement'),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1F2937"
                                    ),
                                    ft.Row([
                                        ft.Text(
                                            f"By {announcement.get('creator_name', 'Admin')}",
                                            size=12,
                                            color="#D4817A",
                                            weight=ft.FontWeight.W_500
                                        ),
                                        ft.Text("•", size=12, color="#D1D5DB"),
                                        ft.Text(
                                            self.format_date(announcement.get('created_at', '')),
                                            size=12,
                                            color="#9CA3AF"
                                        )
                                    ], spacing=6)
                                ], spacing=4, expand=True)
                            ], spacing=12),
                            ft.Container(height=8),
                            ft.Text(
                                announcement.get('content', ''),
                                size=14,
                                color="#4B5563",
                                max_lines=3
                            ),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Container(expand=True),
                                ft.TextButton(
                                    "Comments",
                                    icon=ft.Icons.COMMENT,
                                    style=ft.ButtonStyle(color="#D4817A"),
                                    on_click=lambda e, ann=announcement: (print(f"Comment button clicked for announcement: {ann.get('id')}"), self.show_announcement_detail(ann))[1]
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ], spacing=0),
                        padding=ft.padding.all(18),
                        margin=ft.margin.only(bottom=15),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        )
                    )
                )

            content_sections.append(
                ft.Container(
                    ref=announcements_ref,
                    key="announcements_section",
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.CAMPAIGN, size=22, color=ft.Colors.WHITE),
                                width=44,
                                height=44,
                                bgcolor="#D4817A",
                                border_radius=22,
                                alignment=ft.alignment.center
                            ),
                            ft.Text(
                                "Latest Announcements",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#1F2937"
                            )
                        ], spacing=12),
                        ft.Container(height=15),
                        ft.Column(announcement_cards, spacing=0)
                    ], spacing=0)
                )
            )

        # Materials Section (Uploaded by Admin)
        if hasattr(self, 'materials') and self.materials:
            material_cards = []
            for material in self.materials[:5]:  # Show latest 5 materials
                # Get file extension for icon
                file_path = material.get('file_path', '')
                file_extension = file_path.split('.')[-1].lower() if '.' in file_path else 'file'
                
                # Choose appropriate icon based on file type
                if file_extension in ['pdf']:
                    file_icon = ft.Icons.PICTURE_AS_PDF
                    file_color = "#FF5722"
                elif file_extension in ['doc', 'docx']:
                    file_icon = ft.Icons.DESCRIPTION
                    file_color = "#2196F3"
                elif file_extension in ['ppt', 'pptx']:
                    file_icon = ft.Icons.SLIDESHOW
                    file_color = "#FF9800"
                elif file_extension in ['xls', 'xlsx']:
                    file_icon = ft.Icons.TABLE_CHART
                    file_color = "#4CAF50"
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                    file_icon = ft.Icons.IMAGE
                    file_color = "#9C27B0"
                elif file_extension in ['mp4', 'avi', 'mov']:
                    file_icon = ft.Icons.VIDEO_FILE
                    file_color = "#E91E63"
                else:
                    file_icon = ft.Icons.ATTACH_FILE
                    file_color = "#607D8B"
                
                material_cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(file_icon, size=20, color=ft.Colors.WHITE),
                                    width=40,
                                    height=40,
                                    bgcolor=file_color,
                                    border_radius=20,
                                    alignment=ft.alignment.center
                                ),
                                ft.Column([
                                    ft.Text(
                                        material.get('title', 'Material'),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1F2937"
                                    ),
                                    ft.Row([
                                        ft.Text(
                                            f"By {material.get('creator_name', 'Admin')}",
                                            size=12,
                                            color="#D4817A",
                                            weight=ft.FontWeight.W_500
                                        ),
                                        ft.Text("•", size=12, color="#D1D5DB"),
                                        ft.Text(
                                            self.format_date(material.get('created_at', '')),
                                            size=12,
                                            color="#9CA3AF"
                                        )
                                    ], spacing=6)
                                ], spacing=4, expand=True)
                            ], spacing=12),
                            ft.Container(height=8),
                            ft.Text(
                                material.get('description', 'No description available'),
                                size=14,
                                color="#4B5563",
                                max_lines=2
                            ),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    "Download",
                                    icon=ft.Icons.DOWNLOAD,
                                    style=ft.ButtonStyle(
                                        bgcolor="#D4817A",
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=20),
                                        padding=ft.padding.symmetric(horizontal=20, vertical=8)
                                    ),
                                    on_click=lambda e, path=material.get('file_path'): self.download_material(path)
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ], spacing=0),
                        padding=ft.padding.all(18),
                        margin=ft.margin.only(bottom=15),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        )
                    )
                )

            content_sections.append(
                ft.Container(
                    ref=materials_ref,
                    key="materials_section",
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.FOLDER, size=22, color=ft.Colors.WHITE),
                                width=44,
                                height=44,
                                bgcolor="#4CAF50",
                                border_radius=22,
                                alignment=ft.alignment.center
                            ),
                            ft.Text(
                                "Class Materials",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#1F2937"
                            )
                        ], spacing=12),
                        ft.Container(height=15),
                        ft.Column(material_cards, spacing=0)
                    ], spacing=0)
                )
            )

        # Available Assessments Section (Posted by Admin)
        if self.assessments:
            assessment_cards = []
            for assessment in self.assessments[:5]:  # Show latest 5 assessments
                is_submitted = assessment.get('is_submitted', False)
                status_text = "COMPLETED" if is_submitted else "AVAILABLE"
                status_color = ft.Colors.GREEN_500 if is_submitted else "#D4817A"
                button_text = "VIEW RESULTS" if is_submitted else "TAKE ASSESSMENT"

                assessment_cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.STAR if is_submitted else ft.Icons.ASSIGNMENT,
                                        size=20,
                                        color=ft.Colors.WHITE
                                    ),
                                    width=40,
                                    height=40,
                                    bgcolor=status_color,
                                    border_radius=20,
                                    alignment=ft.alignment.center
                                ),
                                ft.Column([
                                    ft.Text(
                                        assessment.get('title', 'Assessment'),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1F2937"
                                    ),
                                    ft.Text(
                                        f"Duration: {assessment.get('duration_minutes', 0)} minutes",
                                        size=12,
                                        color="#9CA3AF"
                                    ),
                                    ft.Text(
                                        status_text,
                                        size=11,
                                        color=status_color,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ], spacing=4, expand=True)
                            ], spacing=12),
                            ft.Container(height=8),
                            ft.Text(
                                assessment.get('description', 'No description available')[:100] + "..." if len(assessment.get('description', '')) > 100 else assessment.get('description', 'No description available'),
                                size=13,
                                color="#4B5563",
                                max_lines=2
                            ),
                            ft.Container(height=12),
                            ft.ElevatedButton(
                                button_text,
                                icon=ft.Icons.VISIBILITY if is_submitted else ft.Icons.PLAY_ARROW,
                                style=ft.ButtonStyle(
                                    bgcolor=status_color,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10)
                                ),
                                on_click=lambda e, aid=assessment['id']: self.take_exam(aid) if not is_submitted else self.view_results(aid)
                            )
                        ], spacing=0),
                        padding=ft.padding.all(18),
                        margin=ft.margin.only(bottom=15),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        )
                    )
                )

            content_sections.append(
                ft.Container(
                    ref=assessments_ref,
                    key="assessments_section",
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.SCHOOL, size=22, color=ft.Colors.WHITE),
                                width=44,
                                height=44,
                                bgcolor="#D4817A",
                                border_radius=22,
                                alignment=ft.alignment.center
                            ),
                            ft.Text(
                                "Available Assessments",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#1F2937"
                            )
                        ], spacing=12),
                        ft.Container(height=15),
                        ft.Column(assessment_cards, spacing=0)
                    ], spacing=0)
                )
            )


        # If no content, show empty state
        if not content_sections:
            content_sections.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, size=64, color="#D1D5DB"),
                        ft.Container(height=16),
                        ft.Text(
                            "No posts, announcements, or assessments yet",
                            size=16,
                            color="#9CA3AF",
                            weight=ft.FontWeight.W_500,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Check back later for updates from your instructors",
                            size=14,
                            color="#D1D5DB",
                            text_align=ft.TextAlign.CENTER
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.alignment.center,
                    height=300,
                    bgcolor="#FAFAFA",
                    border_radius=16,
                    border=ft.border.all(1, "#F3F4F6")
                )
            )

        # Main content with improved layout
        main_content = ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=20),
                section_nav,  # Add section navigation buttons
                ft.Container(
                    content=ft.Column(
                        ref=main_scroll_ref,
                        controls=content_sections, 
                        spacing=25, 
                        scroll=ft.ScrollMode.AUTO
                    ),
                    expand=True,
                    height=600
                )
            ], spacing=0),
            padding=ft.padding.all(20),
            bgcolor="#f4f1ec"
        )

        self.main_content.content = main_content
        self.page.update()
    
    def create_post_card_modern(self, post):
        """Create a modern post card"""
        is_assessment = post['post_type'] == 'assessment'
        
        primary_btn = None
        if is_assessment and post.get('assessment_id'):
            primary_btn = ft.ElevatedButton(
                "Take Assessment",
                icon=ft.Icons.PLAY_ARROW,
                style=ft.ButtonStyle(
                    bgcolor="#f3c9c0",
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    padding=ft.padding.symmetric(horizontal=20, vertical=10)
                ),
                on_click=lambda e, aid=post['assessment_id']: self.take_exam(aid)
            )
        else:
            actions = []
            if post.get('file_path'):
                actions.append(ft.TextButton(
                    "Download", 
                    icon=ft.Icons.DOWNLOAD,
                    style=ft.ButtonStyle(color="#D4817A")
                ))
            actions.append(ft.ElevatedButton(
                "Turn In File",
                icon=ft.Icons.FILE_UPLOAD,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_500,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    padding=ft.padding.symmetric(horizontal=15, vertical=8)
                ),
                on_click=lambda e, pid=post['id']: self.choose_file_for_submission(pid)
            ))
            primary_btn = ft.Row(actions, spacing=10)

        comments_btn = ft.TextButton(
            "Comments",
            icon=ft.Icons.COMMENT,
            style=ft.ButtonStyle(color="#D4817A"),
            on_click=lambda e, pid=post['id']: self.open_comments_dialog(pid, post['title'])
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.Icons.ASSIGNMENT if is_assessment else ft.Icons.ARTICLE,
                        color="#D4817A",
                        size=20
                    ),
                    ft.Text(
                        post['title'],
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                        size=16,
                        expand=True
                    ),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Text(
                    post['description'] or "No description available",
                    color=ft.Colors.BLACK54,
                    size=12,
                    max_lines=2
                ),
                ft.Text(
                    f"Author: {post.get('author_name', 'Unknown')}",
                    size=10,
                    color=ft.Colors.BLACK45
                ),
                ft.Container(height=5),
                ft.Row([
                    primary_btn,
                    comments_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(15),
            border_radius=15,
            border=ft.border.all(1, "#E8B4CB"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_material_card_modern(self, material):
        """Create a modern material card"""
        import os
        
        # Extract file extension for icon
        file_path = material.get('file_path', '')
        file_ext = os.path.splitext(file_path)[1].lower() if file_path else ''
        
        # Choose appropriate icon based on file type
        if file_ext in ['.pdf']:
            icon = ft.Icons.PICTURE_AS_PDF
        elif file_ext in ['.doc', '.docx']:
            icon = ft.Icons.DESCRIPTION
        elif file_ext in ['.ppt', '.pptx']:
            icon = ft.Icons.SLIDESHOW
        elif file_ext in ['.xls', '.xlsx']:
            icon = ft.Icons.TABLE_CHART
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            icon = ft.Icons.IMAGE
        else:
            icon = ft.Icons.ATTACH_FILE
        
        # Download button
        download_btn = ft.ElevatedButton(
            "Download",
            icon=ft.Icons.DOWNLOAD,
            style=ft.ButtonStyle(
                bgcolor="#D4817A",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=20, vertical=10)
            ),
            on_click=lambda e, path=material.get('file_path'): self.download_material(path)
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        icon,
                        color="#D4817A",
                        size=20
                    ),
                    ft.Text(
                        material.get('title', 'Untitled Material'),
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                        size=16,
                        expand=True
                    ),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Text(
                    material.get('description', 'No description available'),
                    color=ft.Colors.BLACK54,
                    size=12,
                    max_lines=2
                ),
                ft.Text(
                    f"Uploaded by: {material.get('creator_name', 'Unknown')}",
                    size=10,
                    color=ft.Colors.BLACK45
                ),
                ft.Text(
                    f"Date: {self.format_date(material.get('created_at', ''))}",
                    size=10,
                    color=ft.Colors.BLACK45
                ),
                ft.Container(height=5),
                ft.Row([
                    download_btn
                ], alignment=ft.MainAxisAlignment.START)
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(15),
            border_radius=15,
            border=ft.border.all(1, "#E8B4CB"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )
    
    def download_material(self, file_path):
        """Handle material download"""
        if not file_path:
            return
        
        try:
            import os
            import shutil
            from tkinter import filedialog
            import tkinter as tk
            
            # Create a temporary root window (hidden)
            root = tk.Tk()
            root.withdraw()
            
            # Get the filename from the path
            filename = os.path.basename(file_path)
            
            # Ask user where to save the file
            save_path = filedialog.asksaveasfilename(
                defaultextension=os.path.splitext(filename)[1],
                filetypes=[("All files", "*.*")],
                initialvalue=filename
            )
            
            if save_path:
                # Copy the file to the selected location
                shutil.copy2(file_path, save_path)
                self.show_success(f"Material downloaded to: {save_path}")
            
            root.destroy()
            
        except Exception as e:
            self.show_error(f"Error downloading material: {str(e)}")
    
    def create_stat_card(self, title: str, value, icon, color):
        """Create a statistics card - kept for compatibility"""
        return self.create_stat_card_modern(str(value), title, color)
    
    def create_assessment_card_photo_style(self, assessment):
        """Create an enhanced assessment card with detailed time/date and modern styling"""
        from datetime import datetime
        
        # State-driven labels/colors
        is_submitted = assessment.get('is_submitted', False)
        expanded = assessment.get('id') in self.expanded_cards
        status_text = "COMPLETED" if is_submitted else "PENDING"
        # Completed -> green, Pending -> coral for consistency
        status_bg = "#4CAF50" if is_submitted else "#D4817A"
        # Buttons use dashboard accent color
        button_text = "VIEW RESULTS" if is_submitted else "TAKE ASSESSMENT"
        button_bg = "#D4817A"  # same accent as headers
        
        # Enhanced colors for better visual appeal
        pink_surface = "#f3c9c0"   # inner pink header
        white = ft.Colors.WHITE
        
        # Format detailed date and time
        created_at = assessment.get('created_at', '')
        end_time = assessment.get('end_time', '')  # This is the due date from database
        
        try:
            if created_at:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_created = created_dt.strftime("%B %d, %Y at %I:%M %p")
            else:
                formatted_created = "Date not available"
        except:
            formatted_created = "Date not available"
            
        try:
            if end_time:
                due_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                formatted_due = due_dt.strftime("%B %d, %Y at %I:%M %p")
            else:
                formatted_due = "No due date set"
        except:
            formatted_due = "No due date set"
        
        # Enhanced status chip with better styling
        status_chip_inside = ft.Container(
            content=ft.Text(
                status_text, 
                size=11, 
                weight=ft.FontWeight.BOLD, 
                color=white
            ),
            bgcolor=status_bg,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

        # Enhanced header with better layout and typography
        top_header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(
                            assessment.get('title', 'Assessment'), 
                            size=18, 
                            weight=ft.FontWeight.BOLD, 
                            color="#8B4B5C"
                        ),
                        ft.Text(
                            assessment.get('description', 'No description available')[:80] + ("..." if (assessment.get('description') and len(assessment.get('description')) > 80) else ""),
                            size=13,
                            color="#6B4B5C",
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ], spacing=6, expand=True),
                    ft.Column([
                        status_chip_inside,
                        ft.Container(expand=True),
                        ft.Icon(
                            ft.Icons.EXPAND_MORE if not expanded else ft.Icons.EXPAND_LESS, 
                            color="#8B4B5C", 
                            size=20
                        ),
                    ], spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], alignment=ft.MainAxisAlignment.START),
                
                # Detailed time and date information
                ft.Container(height=8),
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SCHEDULE, size=16, color="#8B4B5C"),
                        ft.Text(
                            f"Duration: {assessment.get('duration_minutes', 'N/A')} minutes",
                            size=12,
                            color="#8B4B5C",
                            weight=ft.FontWeight.W_500
                        )
                    ], spacing=6),
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color="#8B4B5C"),
                        ft.Text(
                            f"Created: {formatted_created}",
                            size=12,
                            color="#8B4B5C"
                        )
                    ], spacing=6),
                    ft.Row([
                        ft.Icon(ft.Icons.EVENT, size=16, color="#8B4B5C"),
                        ft.Text(
                            f"Due: {formatted_due}",
                            size=12,
                            color="#8B4B5C"
                        )
                    ], spacing=6),
                ], spacing=4)
            ], spacing=0),
            bgcolor=pink_surface,
            border_radius=18,
            padding=ft.padding.all(20),
            on_click=lambda e, aid=assessment['id']: self.toggle_assessment_card(aid),
        )
        
        # Enhanced action row with better styling and proper positioning
        if expanded:
            action_row = ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        button_text,
                        icon=ft.Icons.VISIBILITY if is_submitted else ft.Icons.PLAY_ARROW,
                        style=ft.ButtonStyle(
                            bgcolor=button_bg,
                            color=white,
                            shape=ft.RoundedRectangleBorder(radius=20),
                            padding=ft.padding.symmetric(horizontal=24, vertical=14),
                            elevation=4,
                            shadow_color=ft.Colors.with_opacity(0.3, button_bg)
                        ),
                        on_click=lambda e, assessment_id=assessment['id']: self.handle_assessment_action(assessment_id, is_submitted),
                    ),
                ], alignment=ft.MainAxisAlignment.END), 
                padding=ft.padding.only(top=8, right=16, bottom=8),
                bgcolor=ft.Colors.WHITE
            )
        else:
            action_row = ft.Container(height=0)
        
        return ft.Container(
            content=ft.Column([
                top_header,
                action_row,
            ], spacing=0),
            bgcolor=white,
            border_radius=20,
            padding=ft.padding.all(0),
            margin=ft.margin.only(bottom=15),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            height=220 if expanded else 180,
        )

    def toggle_assessment_card(self, assessment_id: int):
        """Toggle expanded state for an assessment card and refresh the list view."""
        if assessment_id in self.expanded_cards:
            self.expanded_cards.remove(assessment_id)
        else:
            self.expanded_cards.add(assessment_id)
        # Re-render the assessments section to reflect expansion state
        self.show_available_exams()
    
    def handle_assessment_action(self, assessment_id, is_submitted):
        """Handle assessment action based on status"""
        if is_submitted:
            self.view_results(assessment_id)
        else:
            self.take_exam(assessment_id)
    
    def create_assessment_card(self, assessment):
        """Create an assessment card with modern styling - kept for compatibility"""
        status_color = ft.Colors.GREEN_500 if assessment.get('is_submitted', False) else "#E8B4CB"
        status_text = "Completed" if assessment.get('is_submitted', False) else "Available"
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, color=status_color, size=24),
                ft.Column([
                    ft.Text(
                        assessment['title'],
                        weight=ft.FontWeight.BOLD,
                        size=16,
                        color=ft.Colors.BLACK87
                    ),
                    ft.Text(
                        assessment['description'][:50] + "..." if len(assessment['description']) > 50 else assessment['description'],
                        size=12,
                        color=ft.Colors.BLACK54
                    ),
                    ft.Text(
                        f"Duration: {assessment['duration_minutes']} minutes",
                        size=10,
                        color=ft.Colors.BLACK45
                    ),
                    ft.Text(
                        status_text,
                        size=12,
                        color=status_color,
                        weight=ft.FontWeight.BOLD
                    )
                ], expand=True, spacing=4),
                ft.ElevatedButton(
                    "Take Exam" if not assessment.get('is_submitted', False) else "View Results",
                    icon=ft.Icons.PLAY_ARROW if not assessment.get('is_submitted', False) else ft.Icons.VISIBILITY,
                    style=ft.ButtonStyle(
                        bgcolor=status_color,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        padding=ft.padding.symmetric(horizontal=20, vertical=10)
                    ),
                    on_click=lambda e, assessment_id=assessment['id']: self.take_exam(assessment_id) if not assessment.get('is_submitted', False) else self.view_results(assessment_id)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(20),
            border_radius=15,
            border=ft.border.all(1, "#E8B4CB"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )
    
    def show_available_exams(self):
        """Show available exams view with modern styling matching the photo design"""
        self.current_view = "available"
        # Always attempt to refresh assessments
        try:
            self.load_assessments()
        except Exception as ex:
            try:
                print(f"Error loading assessments: {ex}")
            except Exception:
                pass
        
        try:
            # Build header matching other pages
            from datetime import datetime
            header = self._build_section_header(ft.Icons.ASSIGNMENT, "Assessments")
            
            # List of assessment cards (or empty state)
            cards_column = ft.Column(
                [self.create_assessment_card_photo_style(a) for a in (self.assessments or [])] or [
                    ft.Container(
                        content=ft.Text(
                            "No assessments available",
                            color=ft.Colors.BLACK54,
                            size=14,
                        ),
                        padding=ft.padding.all(20),
                        bgcolor="#fafafa",
                        border_radius=10,
                    )
                ],
                spacing=10,
            )
            
            # Outer container with enhanced styling: white card with elegant box shadow
            manage_assessment_container = ft.Container(
                content=ft.Column([
                    cards_column,
                ], spacing=15),
                padding=ft.padding.all(25),
                bgcolor=ft.Colors.WHITE,
                border_radius=20,
                width=1050,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                    offset=ft.Offset(0, 8)
                )
            )
            
            # Standardized layout: header + scrollable content
            content_body = ft.Container(
                content=manage_assessment_container,
                expand=True,
                padding=ft.padding.all(0)
            )
            
            combined_content = ft.Column([
                header,  # Fixed header at top
                content_body
            ], spacing=0, expand=True)
            
            # Place into main content
            self.main_content.content = combined_content
        except Exception as ex:
            # As a last resort, show a very simple view so the user sees feedback
            fallback = ft.Column([
                ft.Text("Manage Assessment", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"An error occurred rendering the assessments: {ex}", color=ft.Colors.RED_400),
            ])
            self.main_content.content = fallback
        
        self.page.update()
    
    def show_past_exams(self):
        """Show past exams view - kept for compatibility"""
        self.show_results()
    
    def show_results(self):
        """Show results view with modern styling"""
        self.current_view = "results"
        
        # Header matching other pages
        from datetime import datetime
        header = self._build_section_header(ft.Icons.STAR, "Scores")
        
        # Fetch student's completed assessments with scores and graded status
        results = self.get_student_completed_results()
        
        # Empty state
        if not results:
            content_body = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ASSIGNMENT, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No completed assessments yet", size=16, color=ft.Colors.GREY_600),
                    ft.Text("Your taken assessments will appear here", size=12, color=ft.Colors.GREY_500)
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(40),
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=15
            )
        else:
            # Build table header (no rank column, include graded status)
            header_row = ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Text("Assessment", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=4, alignment=ft.alignment.center_left, bgcolor="#D4817A", padding=ft.padding.symmetric(vertical=12, horizontal=8)),
                    ft.Container(content=ft.Text("Score", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=2, alignment=ft.alignment.center, bgcolor="#D4817A", padding=ft.padding.symmetric(vertical=12)),
                    ft.Container(content=ft.Text("%", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=2, alignment=ft.alignment.center, bgcolor="#D4817A", padding=ft.padding.symmetric(vertical=12)),
                    ft.Container(content=ft.Text("Status", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=2, alignment=ft.alignment.center, bgcolor="#D4817A", padding=ft.padding.symmetric(vertical=12)),
                    ft.Container(content=ft.Text("Date", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), expand=2, alignment=ft.alignment.center, bgcolor="#D4817A", padding=ft.padding.symmetric(vertical=12)),
                    ft.Container(content=ft.Text("View", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), width=100, alignment=ft.alignment.center, bgcolor="#D4817A", padding=ft.padding.symmetric(vertical=12))
                ], spacing=0),
                border_radius=ft.border_radius.only(top_left=10, top_right=10)
            )
            
            # Build table rows
            table_rows = [header_row]
            for i, r in enumerate(results, start=1):
                max_score = r.get('max_score', 0) or 0
                score_val = r.get('score', 0) or 0
                percentage = (score_val / max_score * 100) if max_score > 0 else 0
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
                
                # Alternating background colors (striped rows)
                row_bg = ft.Colors.WHITE if i % 2 == 0 else ft.Colors.GREY_50

                # Graded status
                is_graded = bool(r.get('is_graded', 0))
                status_text = "Graded" if is_graded else "Not Graded"
                status_color = ft.Colors.GREEN if is_graded else ft.Colors.ORANGE
                status_badge = ft.Container(
                    content=ft.Text(status_text, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=status_color,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=10
                )
                
                row = ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Text(r.get('title') or 'Untitled', size=13, color=ft.Colors.BLACK87, weight=ft.FontWeight.W_500), expand=4, alignment=ft.alignment.center_left, padding=ft.padding.only(left=8)),
                        ft.Container(content=ft.Text(f"{score_val}/{max_score}", size=13, color=score_color, weight=ft.FontWeight.BOLD), expand=2, alignment=ft.alignment.center),
                        ft.Container(content=ft.Text(f"{percentage:.1f}%", size=13, color=score_color, weight=ft.FontWeight.BOLD), expand=2, alignment=ft.alignment.center),
                        ft.Container(content=status_badge, expand=2, alignment=ft.alignment.center),
                        ft.Container(content=ft.Text(self.format_date(r.get('submitted_at')), size=12, color=ft.Colors.BLACK87), expand=2, alignment=ft.alignment.center),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                icon_color="#D4817A",
                                icon_size=18,
                                tooltip="View Detailed Results",
                                on_click=lambda e, aid=r.get('assessment_id'): self.view_results(aid)
                            ),
                            width=100,
                            alignment=ft.alignment.center
                        )
                    ], spacing=0),
                    bgcolor=row_bg,
                    padding=ft.padding.symmetric(vertical=12),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
                )
                table_rows.append(row)
            
            content_body = ft.Container(
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
        
        # Standardized layout: header + content
        content = ft.Column([
            header,
            ft.Container(height=20),
            content_body
        ], spacing=0, expand=True)
        
        self.main_content.content = content
        self.page.update()
    
    def create_result_card_modern(self, assessment):
        """Create a modern result card"""
        # This would show actual results from the database
        score = "85%"  # Placeholder
        status = "Passed" if score > "70%" else "Failed"
        status_color = ft.Colors.GREEN_500 if status == "Passed" else ft.Colors.RED_500
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, color="#D4817A", size=24),
                ft.Column([
                    ft.Text(
                        assessment['title'],
                        weight=ft.FontWeight.BOLD,
                        size=16,
                        color=ft.Colors.BLACK87
                    ),
                    ft.Text(
                        f"Score: {score}",
                        size=14,
                        color=ft.Colors.BLACK54
                    ),
                    ft.Text(
                        f"Status: {status}",
                        size=14,
                        color=status_color,
                        weight=ft.FontWeight.BOLD
                    )
                ], expand=True, spacing=4),
                ft.IconButton(
                    ft.Icons.VISIBILITY,
                    tooltip="View Detailed Results",
                    icon_color="#D4817A",
                    icon_size=24
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(20),
            border_radius=15,
            border=ft.border.all(1, "#E8B4CB"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_result_card(self, assessment):
        """Create a result card - kept for compatibility"""
        return self.create_result_card_modern(assessment)
    
    # Keep all other methods unchanged for functionality
    def take_exam(self, assessment_id):
        """Start taking an exam"""
        # Find the assessment
        assessment = next((a for a in self.assessments if a['id'] == assessment_id), None)
        if not assessment:
            return
        
        self.current_assessment = assessment
        self.current_questions = self.db_manager.get_questions(assessment_id)
        self.answers = {}
        # Configure per-question mode: split duration equally per question
        total_seconds = max(1, assessment['duration_minutes'] * 60)
        q_count = max(1, len(self.current_questions))
        base = total_seconds // q_count
        rem = total_seconds % q_count
        # Distribute the remainder: first 'rem' questions get +1 second
        self.per_question_slices = [base + (1 if i < rem else 0) for i in range(q_count)]
        self.per_question_seconds = base if q_count == 0 else self.per_question_slices[0]
        self.per_question_remaining = self.per_question_seconds
        self.current_question_index = 0
        self.per_question_mode = True
        self.timer_active = True

        # Enter exam mode (immersive)
        self.enter_exam_mode()
        # Render first question and start timer
        self.show_exam_interface_per_question()
        self.start_timer()
    
    def start_timer(self):
        """Start the exam timer"""
        # Per-question countdown logic
        if not self.timer_active:
            return
        if self.per_question_mode:
            minutes = self.per_question_remaining // 60
            seconds = self.per_question_remaining % 60
            self.timer_display.value = f"{minutes:02d}:{seconds:02d}"
            if self.per_question_remaining > 0:
                self.per_question_remaining -= 1
                self.page.update()
                self.page.run_thread(self.timer_tick)
            else:
                # Auto advance to next question or submit at end
                self.go_next_question()
        else:
            if self.timer_seconds > 0:
                minutes = self.timer_seconds // 60
                seconds = self.timer_seconds % 60
                self.timer_display.value = f"{minutes:02d}:{seconds:02d}"
                self.timer_seconds -= 1
                self.page.update()
                self.page.run_thread(self.timer_tick)
            else:
                self.submit_exam(None)
    
    def timer_tick(self):
        """Timer tick function"""
        import time
        time.sleep(1)
        self.start_timer()
    
    def show_exam_interface(self):
        """Show the exam taking interface"""
        # Kept for compatibility; no longer used in per-question mode
        self.show_exam_interface_per_question()

    def show_exam_interface_per_question(self):
        """Render a single question at a time with progress bar and Next button."""
        self.question_container.controls.clear()

        total_q = len(self.current_questions)
        idx = min(self.current_question_index, total_q - 1)
        question = self.current_questions[idx]

        # Header with Back, title and timer
        left_header_clickable = ft.GestureDetector(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ARROW_BACK, color="#D4817A"),
                    ft.Column([
                        ft.Text(self.current_assessment['title'], size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Text("Direction", size=12, italic=True, color=ft.Colors.BLACK54),
                    ], spacing=2),
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                bgcolor=ft.Colors.TRANSPARENT,
            ),
            on_tap=lambda e: self._handle_back_click(),
            mouse_cursor=ft.MouseCursor.CLICK,
        )
        header = ft.Container(
            content=ft.Row([
                left_header_clickable,
                ft.Container(expand=True),
                ft.Row([
                    ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.BLACK54),
                    self.timer_display,
                ], spacing=6),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#f7ebe8",
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border=ft.border.all(1, "#E8B4CB"),
            border_radius=15,
        )

        # Current question widget
        q_widget = self.create_question_widget(question, idx)

        # Determine if Next/Submit should be enabled (require selection for all questions)
        is_last = (idx == total_q - 1)
        # Only enable when answer exists
        curr_q_id = question['id']
        has_answer = curr_q_id in self.answers and str(self.answers[curr_q_id]).strip() != ""
        self.next_button = ft.ElevatedButton(
            "Submit" if is_last else "Next",
            style=ft.ButtonStyle(
                bgcolor="#D4817A",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=24, vertical=10)
            ),
            on_click=lambda e: self.submit_exam(None) if is_last else self.go_next_question()
        )
        self.next_button.disabled = not has_answer

        # Progress bar and percentage
        progress = (idx / total_q) if total_q > 0 else 0
        self.progress_bar = ft.ProgressBar(value=progress, color="#F4B183", bgcolor="#D9D9D9", height=12)
        self.progress_text = ft.Text(f"{int(progress*100)}%", size=12, color="#D4817A")
        progress_row = ft.Row([
            self.progress_text,
            ft.Container(width=10),
            ft.Container(content=self.progress_bar, expand=True),
            ft.Container(width=10),
            self.next_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Assemble content with a medium width card centered on screen
        card = ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=16),
                q_widget,
                ft.Container(height=16),
                progress_row
            ], spacing=10),
            width=860,
            height=480,
            padding=ft.padding.symmetric(horizontal=24)
        )
        self.main_content.content = ft.Container(
            content=card,
            alignment=ft.alignment.center,
            padding=ft.padding.all(0),
            expand=True
        )
        self.page.update()

    def get_student_completed_results(self):
        """Fetch current student's completed assessments with scores and submission info"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            query = """
            SELECT 
                a.id as assessment_id,
                a.title,
                s.id as submission_id,
                COALESCE(s.score, s.total_score, 0) as score,
                COALESCE(s.total_questions, s.max_score, 0) as max_score,
                s.submitted_at,
                s.is_graded
            FROM submissions s
            JOIN assessments a ON s.assessment_id = a.id
            WHERE s.student_id = ?
            ORDER BY s.submitted_at DESC
            """
            cursor.execute(query, (self.user_data['id'],))
            rows = cursor.fetchall()
            conn.close()
            results = []
            for row in rows:
                results.append({
                    'assessment_id': row[0],
                    'title': row[1],
                    'submission_id': row[2],
                    'score': row[3] or 0,
                    'max_score': row[4] or 0,
                    'submitted_at': row[5],
                    'is_graded': row[6] or 0
                })
            # Only include those that are completed/submitted
            return results
        except Exception as ex:
            print(f"Error fetching student results: {ex}")
            return []

    # Exam mode helpers
    def enter_exam_mode(self):
        """Hide sidebar/nav and make the quiz view take the entire screen."""
        try:
            # Hide sidebar
            self.sidebar.visible = False
            # Optional: enter window fullscreen for desktop
            try:
                self.page.window.full_screen = True
            except Exception:
                pass
            self.page.update()
        except Exception:
            pass

    def exit_exam_mode(self):
        """Restore sidebar/nav and exit full screen after quiz."""
        try:
            self.sidebar.visible = True
            try:
                self.page.window.full_screen = False
            except Exception:
                pass
            # Clean state
            self.per_question_mode = False
            self.current_question_index = 0
            self.page.update()
        except Exception:
            pass

    def _confirm_exit_exam(self):
        """Ask the student to confirm leaving the exam in progress."""
        def close_dialog(*_):
            try:
                dialog.open = False
                self.page.update()
            except Exception:
                pass
        def confirm_exit(e):
            try:
                dialog.open = False
                self.page.update()
            except Exception:
                pass
            # Stop timer and exit exam mode
            self.timer_active = False
            self.exit_exam_mode()
            self.navigate_to(2)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Leave Assessment?", color="#D4817A"),
            content=ft.Text("Your current progress will be kept, but the timer will stop. Do you want to go back to Assessments?", size=12),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Exit", on_click=confirm_exit, style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _handle_back_click(self):
        """Decide if we need to confirm before exiting the exam.
        - If there are no answers at all, exit immediately.
        - If there is any answer (partial progress), ask for confirmation.
        """
        try:
            any_answered = any(str(v or "").strip() != "" for v in (self.answers or {}).values())
        except Exception:
            any_answered = False
        if any_answered:
            self._confirm_exit_exam()
        else:
            # No answers yet, exit quietly
            self.timer_active = False
            self.exit_exam_mode()
            self.navigate_to(2)

    def go_next_question(self):
        """Advance to next question, save state, reset per-question timer or submit at end."""
        total_q = len(self.current_questions)
        if self.current_question_index < total_q - 1:
            self.current_question_index += 1
            # Pick the designated slice for the next question
            try:
                self.per_question_seconds = self.per_question_slices[self.current_question_index]
            except Exception:
                # Fallback to previous value if index out of range
                pass
            self.per_question_remaining = self.per_question_seconds
            # Update progress bar value and re-render
            self.show_exam_interface_per_question()
            # Reset timer display immediately and restart ticking
            try:
                m = self.per_question_remaining // 60
                s = self.per_question_remaining % 60
                self.timer_display.value = f"{m:02d}:{s:02d}"
            except Exception:
                pass
            self.page.update()
            self.start_timer()
        else:
            # Last question completed -> submit
            self.submit_exam(None)
    
    def create_question_widget(self, question, index):
        """Create a question widget"""
        question_text = ft.Text(
            f"Question {index + 1}: {question['question_text']}",
            weight=ft.FontWeight.BOLD,
            size=16,
            color=ft.Colors.BLACK87
        )
        
        if question['question_type'] == 'mcq':
            # Multiple choice question - properly parse JSON options
            options = []
            if question['options']:
                try:
                    import json
                    if isinstance(question['options'], str):
                        # Parse JSON string to get the list
                        parsed_options = json.loads(question['options'])
                        if isinstance(parsed_options, list):
                            # Clean each option to remove extra quotes/brackets
                            for opt in parsed_options:
                                if isinstance(opt, str) and opt.strip():
                                    clean_opt = opt.strip().strip('"').strip("'").strip('[]').strip()
                                    if clean_opt:
                                        options.append(clean_opt)
                        else:
                            # Single option as string
                            clean_opt = str(parsed_options).strip().strip('"').strip("'").strip('[]').strip()
                            if clean_opt:
                                options.append(clean_opt)
                    elif isinstance(question['options'], list):
                        # Already a list
                        for opt in question['options']:
                            if isinstance(opt, str) and opt.strip():
                                clean_opt = opt.strip().strip('"').strip("'").strip('[]').strip()
                                if clean_opt:
                                    options.append(clean_opt)
                    else:
                        # Fallback to string conversion
                        clean_opt = str(question['options']).strip().strip('"').strip("'").strip('[]').strip()
                        if clean_opt:
                            options.append(clean_opt)
                    
                    print(f"Student view - parsed options for question {question['id']}: {options}")
                except Exception as e:
                    print(f"Error parsing options for question {question['id']}: {e}")
                    # Fallback to old method if JSON parsing fails
                    options = question['options'].split(',') if question['options'] else []
                    options = [opt.strip() for opt in options if opt.strip()]
            
            radio_group = ft.RadioGroup(
                content=ft.Column(
                    [ft.Radio(value=opt, label=opt) for opt in options],
                    spacing=8
                )
            )
            
            # Store reference for answer collection and enable Next when selected
            def on_choice_change(e, q_id=question['id']):
                self.set_answer(q_id, e.control.value)
                # Enable Next/Submit when an option is chosen
                total_q = len(self.current_questions)
                is_last = (self.current_question_index == total_q - 1)
                if self.next_button:
                    self.next_button.disabled = (str(e.control.value or "").strip() == "")
                    self.page.update()
            radio_group.on_change = on_choice_change
            
            return ft.Container(
                content=ft.Column([question_text, radio_group], spacing=15),
                bgcolor=ft.Colors.WHITE,
                padding=ft.padding.all(20),
                border_radius=15,
                border=ft.border.all(1, "#E8B4CB"),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=5,
                    color=ft.Colors.BLACK12,
                    offset=ft.Offset(0, 2)
                )
            )
        else:
            # Short answer question
            def on_text_change(e, q_id=question['id']):
                text_val = e.control.value or ""
                self.set_answer(q_id, text_val)
                total_q = len(self.current_questions)
                is_last_here = (self.current_question_index == total_q - 1)
                if self.next_button:
                    self.next_button.disabled = (text_val.strip() == "")
                    self.page.update()
            answer_field = ft.TextField(
                label="Your Answer",
                multiline=True,
                min_lines=3,
                border_radius=10,
                border_color="#E8B4CB",
                focused_border_color="#D4817A",
                on_change=on_text_change
            )
            
            return ft.Container(
                content=ft.Column([question_text, answer_field], spacing=15),
                bgcolor=ft.Colors.WHITE,
                padding=ft.padding.all(20),
                border_radius=15,
                border=ft.border.all(1, "#E8B4CB"),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=5,
                    color=ft.Colors.BLACK12,
                    offset=ft.Offset(0, 2)
                )
            )
    
    def set_answer(self, question_id, answer):
        """Set answer for a question"""
        self.answers[question_id] = answer
    
    def submit_exam(self, e):
        """Submit the exam"""
        self.timer_active = False
        
        # Prepare answers for submission
        answers_list = []
        for question in self.current_questions:
            answer_text = self.answers.get(question['id'], '')
            answers_list.append({
                'question_id': question['id'],
                'answer_text': answer_text
            })
        
        try:
            # Submit to database
            submission_id = self.db_manager.submit_assessment(
                assessment_id=self.current_assessment['id'],
                student_id=self.user_data['id'],
                answers=answers_list
            )
            
            self.show_success("Exam submitted successfully!")
            self.load_assessments()
            # Exit immersive mode and return to dashboard
            self.exit_exam_mode()
            self.show_dashboard()
            
        except Exception as ex:
            self.show_error(f"Error submitting exam: {str(ex)}")
    
    def view_results(self, assessment_id):
        """Navigate to dedicated results page"""
        try:
            from pages.student_results_page import StudentResultsPage
            
            # Clear views and navigate to results page
            self.page.views.clear()
            results_page = StudentResultsPage(self.page, self.db_manager, self.user_data, assessment_id)
            self.page.views.append(results_page.get_view())
            self.page.update()
            
        except Exception as ex:
            self.show_error(f"Error loading results: {str(ex)}")

    def load_assessments(self):
        """Load assessments from database"""
        self.assessments = self.db_manager.get_assessments(user_id=self.user_data['id'], role='student')
        # Recompute counters
        try:
            self.pending_count = len([a for a in (self.assessments or []) if not a.get('is_submitted', False)])
            self.completed_count = len([a for a in (self.assessments or []) if a.get('is_submitted', False)])
        except Exception:
            self.pending_count = 0
            self.completed_count = 0
        # Refresh nav to reflect counts
        try:
            self.update_nav_items()
        except Exception:
            pass
    
    def load_posts(self):
        """Load posts assigned to student's section"""
        try:
            self.posts = self.db_manager.get_posts_for_student_section(self.user_data['id'])
        except Exception as ex:
            print(f"Error loading posts: {ex}")

    def load_announcements(self):
        """Load active announcements from database"""
        try:
            self.announcements = self.db_manager.get_active_announcements()
            # For now, assume all announcements are unread (can be enhanced with read tracking)
            self.unread_announcements_count = len(self.announcements)
        except Exception as ex:
            print(f"Error loading announcements: {ex}")
            self.announcements = []
            self.unread_announcements_count = 0

    def load_materials(self):
        """Load class materials uploaded by admin"""
        try:
            self.materials = self.db_manager.get_materials()
        except Exception as ex:
            print(f"Error loading materials: {ex}")
            self.materials = []

    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return ""
        try:
            # Try to parse the date string and format it nicely
            from datetime import datetime
            if isinstance(date_str, str):
                # Handle different date formats
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime("%b %d, %Y")
            return str(date_str)
        except:
            return str(date_str)

    def choose_file_for_submission(self, post_id: int):
        """Choose file for submission"""
        self._pending_upload_post_id = post_id
        self.file_picker.pick_files(allow_multiple=False)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if not self._pending_upload_post_id:
            return
        if e.files and len(e.files) > 0:
            try:
                import os, shutil
                src = e.files[0].path or e.files[0].name
                submissions_dir = os.path.join(os.getcwd(), "uploads", "submissions")
                os.makedirs(submissions_dir, exist_ok=True)
                filename = os.path.basename(src)
                dest = os.path.join(submissions_dir, f"{self.user_data['id']}_{filename}")
                try:
                    shutil.copyfile(src, dest)
                except Exception:
                    pass
                file_path_to_store = dest if os.path.exists(dest) else src
                self.db_manager.create_file_submission(self._pending_upload_post_id, self.user_data['id'], file_path_to_store)
                self.show_success("File submitted successfully!")
            except Exception as ex:
                self.show_error(f"Error submitting file: {str(ex)}")
        self._pending_upload_post_id = None

    def open_comments_dialog(self, post_id: int, title: str):
        """Open comments dialog with modern styling"""
        comments = self.db_manager.get_comments(post_id)
        
        # Comments list
        comments_list = ft.ListView(spacing=8, padding=ft.padding.all(10), height=300)
        for c in comments:
            comment_card = ft.Container(
                content=ft.Column([
                    ft.Text(
                        c['user_name'],
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#D4817A"
                    ),
                    ft.Text(
                        c['content'],
                        size=12,
                        color=ft.Colors.BLACK87
                    )
                ], spacing=4),
                bgcolor=ft.Colors.WHITE,
                padding=ft.padding.all(10),
                border_radius=8,
                border=ft.border.all(1, "#E8B4CB")
            )
            comments_list.controls.append(comment_card)
        
        # Input field
        input_field = ft.TextField(
            label="Add a comment",
            autofocus=True,
            border_radius=10,
            border_color="#E8B4CB",
            focused_border_color="#D4817A"
        )
        
        def send_comment(e):
            text = input_field.value.strip()
            if text:
                self.db_manager.add_comment(post_id, self.user_data['id'], text)
                input_field.value = ""
                # Refresh comments
                new_comments = self.db_manager.get_comments(post_id)
                comments_list.controls.clear()
                for c in new_comments:
                    comment_card = ft.Container(
                        content=ft.Column([
                            ft.Text(
                                c['user_name'],
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color="#D4817A"
                            ),
                            ft.Text(
                                c['content'],
                                size=12,
                                color=ft.Colors.BLACK87
                            )
                        ], spacing=4),
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.padding.all(10),
                        border_radius=8,
                        border=ft.border.all(1, "#E8B4CB")
                    )
                    comments_list.controls.append(comment_card)
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Comments - {title}", color="#D4817A"),
            content=ft.Column([
                ft.Container(
                    content=comments_list,
                    bgcolor="#F5F5F5",
                    border_radius=10,
                    padding=ft.padding.all(5)
                ),
                ft.Container(height=10),
                input_field
            ], spacing=10, width=400),
            actions=[
                ft.TextButton(
                    "Close",
                    style=ft.ButtonStyle(color=ft.Colors.BLACK54),
                    on_click=lambda e: self.page.close(dialog)
                ),
                ft.ElevatedButton(
                    "Send",
                    icon=ft.Icons.SEND,
                    style=ft.ButtonStyle(
                        bgcolor="#E8B4CB",
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=20)
                    ),
                    on_click=send_comment
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_error(self, message: str):
        """Show error message"""
        print(f"Error: {message}")
        # Could implement a snackbar or dialog here
    
    def show_success(self, message: str):
        """Show success message"""
        print(f"Success: {message}")
        # Could implement a snackbar or dialog here
    
    def show_user_content(self):
        """Show user profile content within the dashboard"""
        from pages.student_user_page import StudentUserPage
        
        # Create user page instance but get only the content, not the full view
        user_page = StudentUserPage(self.page, self.db_manager)
        
        # Get the user form content from the user page
        user_content = user_page.create_user_form()
        
        # Add header similar to other sections
        from datetime import datetime
        header = self._build_section_header(ft.Icons.PERSON, "User Profile")
        
        # Combine header and user content
        combined_content =   ft.Column([
            header,
            user_content
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        
        # Update main content without transitions
        self.main_content.content = combined_content
        self.page.update()
    
    def show_posts_content(self):
        """Show posts content within the same dashboard view (no transition)"""
        # Simply call show_posts which already has the comprehensive UI
        self.show_posts()

    def logout(self, e):
        """Handle logout"""
        self.page.data = None
        self.page.go("/")
    
    def get_view(self):
        """Return the student dashboard view with modern design"""
        # Show dashboard by default
        self.show_dashboard()
        
        return ft.View(
            "/student",
            [
                ft.Container(
                    content=ft.Row([
                        self.sidebar,
                        ft.Container(self.main_content, expand=True)
                    ], expand=True, spacing=0),
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"  # Light gray background
        )

    def get_view_preserve_current(self):
        """Return the view without forcing a switch to dashboard (preserves current content)."""
        return ft.View(
            "/student",
            [
                ft.Container(
                    content=ft.Row([
                        self.sidebar,
                        ft.Container(self.main_content, expand=True)
                    ], expand=True, spacing=0),
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )
    
    def create_enhanced_announcement_card(self, announcement, index):
        """Create an enhanced announcement card with better interactions"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CAMPAIGN, size=18, color=ft.Colors.WHITE),
                        width=36,
                        height=36,
                        bgcolor="#D4817A",
                        border_radius=18,
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(
                            announcement.get('title', 'Announcement'),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="#1F2937"
                        ),
                        ft.Row([
                            ft.Text(
                                f"By {announcement.get('creator_name', 'Admin')}",
                                size=12,
                                color="#9CA3AF"
                            ),
                            ft.Text("•", size=12, color="#D1D5DB"),
                            ft.Text(
                                self.format_date(announcement.get('created_at', '')),
                                size=12,
                                color="#9CA3AF"
                            )
                        ], spacing=6)
                    ], spacing=4, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_FULL,
                        icon_size=16,
                        icon_color="#9CA3AF",
                        tooltip="View full announcement",
                        on_click=lambda e, ann=announcement: self.show_announcement_detail(ann)
                    )
                ], spacing=12),
                ft.Container(height=8),
                ft.Text(
                    announcement.get('content', ''),
                    size=14,
                    color="#4B5563",
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
                ft.Container(height=10),
                ft.Row([
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Comments",
                        icon=ft.Icons.COMMENT,
                        style=ft.ButtonStyle(color="#D4817A"),
                        on_click=lambda e, ann=announcement: self.show_announcement_detail(ann)
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=0),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, "#F3F4F6"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=6,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            on_click=lambda e, ann=announcement: self.show_announcement_detail(ann),
            ink=True
        )
    
    def show_announcement_detail(self, announcement):
        """Show detailed view of an announcement in a modal"""
        print(f"=== SHOW ANNOUNCEMENT DETAIL CALLED ===")
        print(f"Announcement: {announcement}")
        
        # Comments list builder
        def build_comments_list(announcement_id):
            comments = self.db_manager.get_announcement_comments(announcement_id)
            lv = ft.ListView(spacing=8, padding=ft.padding.all(6), height=240)
            for c in comments:
                lv.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(c['user_name'], size=12, weight=ft.FontWeight.BOLD, color="#D4817A"),
                                ft.Container(expand=True),
                                ft.Text(self.format_date(c.get('created_at')), size=11, color=ft.Colors.GREY_600)
                            ], spacing=6),
                            ft.Text(c['content'], size=12, color=ft.Colors.BLACK87)
                        ], spacing=2),
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.padding.all(10),
                        border_radius=8,
                        border=ft.border.all(1, "#E8B4CB")
                    )
                )
            return lv

        comments_list = build_comments_list(announcement.get('id'))
        input_field = ft.TextField(
            label="Add a comment",
            autofocus=True,
            border_radius=10,
            border_color="#E8B4CB",
            focused_border_color="#D4817A"
        )

        def send_comment(e):
            text = (input_field.value or "").strip()
            if text:
                try:
                    self.db_manager.add_announcement_comment(announcement.get('id'), self.user_data['id'], text)
                    input_field.value = ""
                    # Refresh comments
                    new_lv = build_comments_list(announcement.get('id'))
                    comments_container.content = new_lv
                    self.page.update()
                except Exception as ex:
                    self.show_error(f"Error adding comment: {ex}")

        content = ft.Column([
            # Header
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.CAMPAIGN, size=24, color=ft.Colors.WHITE),
                    width=48,
                    height=48,
                    bgcolor="#D4817A",
                    border_radius=24,
                    alignment=ft.alignment.center
                ),
                ft.Column([
                    ft.Text(
                        announcement.get('title', 'Announcement'),
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="#1F2937"
                    ),
                    ft.Row([
                        ft.Text(
                            f"From: {announcement.get('creator_name', 'Admin')}",
                            size=14,
                            color="#6B7280",
                            weight=ft.FontWeight.W_500
                        ),
                        ft.Text("•", size=14, color="#D1D5DB"),
                        ft.Text(
                            self.format_date(announcement.get('created_at', '')),
                            size=14,
                            color="#6B7280"
                        )
                    ], spacing=8)
                ], spacing=4, expand=True)
            ], spacing=16),
            
            ft.Divider(height=20, color="#fafafa"),
            
            # Content
            ft.Container(
                content=ft.Text(
                    announcement.get('content', ''),
                    size=16,
                    color="#374151",
                    selectable=True
                ),
                padding=ft.padding.all(16),
                bgcolor="#F9FAFB",
                border_radius=12,
                border=ft.border.all(1, "#E5E7EB")
            ),
            ft.Container(height=10),
            ft.Text("Comments", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
            comments_container := ft.Container(content=comments_list, bgcolor="#F5F5F5", border_radius=10, padding=ft.padding.all(6)),
            ft.Container(height=8),
            input_field,
            ft.Row([
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Send",
                    icon=ft.Icons.SEND,
                    style=ft.ButtonStyle(bgcolor="#E8B4CB", color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=20)),
                    on_click=send_comment
                )
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=12, scroll=ft.ScrollMode.AUTO)
        
        # Create modern social media style comment modal
        print("=== CREATING SOCIAL MEDIA STYLE DIALOG ===")
        
        try:
            def close_dialog(e):
                if hasattr(self, 'announcement_dialog'):
                    self.announcement_dialog.open = False
                    self.page.update()
            
            # Get comments for this announcement
            comments = self.db_manager.get_announcement_comments(announcement.get('id'))
            
            # Create comment input field
            comment_input = ft.TextField(
                hint_text="Write a comment...",
                multiline=True,
                min_lines=1,
                max_lines=3,
                border_radius=20,
                filled=True,
                bgcolor="#F5F5F5",
                border_color=ft.Colors.TRANSPARENT,
                focused_border_color="#D4817A",
                content_padding=ft.padding.symmetric(horizontal=15, vertical=10)
            )
            
            # Comments list container
            comments_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=300)
            
            def refresh_comments():
                comments_container.controls.clear()
                updated_comments = self.db_manager.get_announcement_comments(announcement.get('id'))
                
                for comment in updated_comments:
                    # Create profile photo
                    profile_photo = self.create_comment_profile_photo(comment.get('profile_photo'))
                    
                    # Create comment card
                    comment_card = ft.Container(
                        content=ft.Row([
                            profile_photo,
                            ft.Column([
                                ft.Row([
                                    ft.Text(
                                        comment.get('user_name', 'Unknown'),
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color="#1F2937"
                                    ),
                                    ft.Text("•", size=12, color="#9CA3AF"),
                                    ft.Text(
                                        self.format_date(comment.get('created_at', '')),
                                        size=12,
                                        color="#9CA3AF"
                                    )
                                ], spacing=6),
                                ft.Text(
                                    comment.get('content', ''),
                                    size=14,
                                    color="#374151",
                                    selectable=True
                                ),
                                ft.Row([
                                    ft.TextButton(
                                        "Reply",
                                        style=ft.ButtonStyle(
                                            color="#D4817A",
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4)
                                        ),
                                        on_click=lambda e, cid=comment.get('id'): self.show_reply_input(cid)
                                    )
                                ], spacing=10)
                            ], spacing=4, expand=True)
                        ], spacing=12, alignment=ft.CrossAxisAlignment.START),
                        padding=ft.padding.all(12),
                        margin=ft.margin.only(bottom=8),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=12,
                        border=ft.border.all(1, "#F3F4F6")
                    )
                    comments_container.controls.append(comment_card)
                
                if not updated_comments:
                    comments_container.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=48, color="#D1D5DB"),
                                ft.Text(
                                    "No comments yet",
                                    size=16,
                                    color="#9CA3AF",
                                    weight=ft.FontWeight.W_500
                                ),
                                ft.Text(
                                    "Be the first to share your thoughts!",
                                    size=14,
                                    color="#D1D5DB"
                                )
                            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(40)
                        )
                    )
                
                self.page.update()
            
            def send_comment(e):
                text = comment_input.value.strip() if comment_input.value else ""
                if text:
                    try:
                        self.db_manager.add_announcement_comment(
                            announcement.get('id'), 
                            self.user_data['id'], 
                            text
                        )
                        comment_input.value = ""
                        refresh_comments()
                    except Exception as ex:
                        print(f"Error adding comment: {ex}")
            
            # Initial load of comments
            refresh_comments()
            
            # Create the dialog
            self.announcement_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CAMPAIGN, size=24, color=ft.Colors.WHITE),
                        width=40,
                        height=40,
                        bgcolor="#D4817A",
                        border_radius=20,
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(
                            announcement.get('title', 'Announcement'),
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#1F2937"
                        ),
                        ft.Text(
                            f"By {announcement.get('creator_name', 'Admin')}",
                            size=12,
                            color="#9CA3AF"
                        )
                    ], spacing=2, expand=True)
                ], spacing=12),
                content=ft.Container(
                    content=ft.Column([
                        # Announcement content
                        ft.Container(
                            content=ft.Text(
                                announcement.get('content', ''),
                                size=14,
                                color="#374151",
                                selectable=True
                            ),
                            padding=ft.padding.all(16),
                            bgcolor="#F9FAFB",
                            border_radius=12,
                            border=ft.border.all(1, "#E5E7EB")
                        ),
                        ft.Container(height=10),
                        # Comments section
                        ft.Text(
                            f"Comments ({len(comments)})",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="#1F2937"
                        ),
                        comments_container,
                        # Comment input
                        ft.Row([
                            self.create_comment_profile_photo(self.user_data.get('profile_photo')),
                            ft.Container(
                                content=comment_input,
                                expand=True
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SEND,
                                icon_color="#D4817A",
                                bgcolor="#F3F4F6",
                                on_click=send_comment,
                                tooltip="Send comment"
                            )
                        ], spacing=12, alignment=ft.CrossAxisAlignment.END)
                    ], spacing=12),
                    width=500,
                    height=500
                ),
                actions=[
                    ft.TextButton(
                        "Close",
                        style=ft.ButtonStyle(color="#6B7280"),
                        on_click=close_dialog
                    )
                ]
            )
            
            # Add to overlay and show
            if self.announcement_dialog not in self.page.overlay:
                self.page.overlay.append(self.announcement_dialog)
            
            self.page.dialog = self.announcement_dialog
            self.announcement_dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"ERROR creating dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def create_comment_profile_photo(self, profile_photo_path):
        """Create a small profile photo for comments"""
        import os
        
        if profile_photo_path and os.path.exists(profile_photo_path):
            return ft.Container(
                content=ft.Image(
                    src=profile_photo_path,
                    width=32,
                    height=32,
                    fit=ft.ImageFit.COVER,
                    border_radius=16
                ),
                width=32,
                height=32,
                border_radius=16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE
            )
        else:
            return ft.Container(
                content=ft.Icon(ft.Icons.PERSON, size=18, color=ft.Colors.WHITE),
                width=32,
                height=32,
                bgcolor="#D4817A",
                border_radius=16,
                alignment=ft.alignment.center
            )
    
    def show_reply_input(self, comment_id):
        """Show reply input for a specific comment - placeholder for now"""
        print(f"Reply to comment {comment_id} - feature coming soon!")
    
    def download_material(self, file_path):
        """Download a material file"""
        import os
        import shutil
        
        if not file_path or not os.path.exists(file_path):
            self.show_error("File not found or path is invalid")
            return
        
        try:
            # Get the file name
            file_name = os.path.basename(file_path)
            
            # For now, just show a success message
            # In a real implementation, you would trigger a file download
            self.show_success(f"Downloading {file_name}...")
            print(f"Download initiated for: {file_path}")
            
        except Exception as e:
            print(f"Error downloading material: {e}")
            self.show_error("Failed to download material")
    
    def close_announcement_dialog(self):
        """Close the announcement detail dialog"""
        if self.announcement_dialog:
            self.announcement_dialog.open = False
            self.page.update()
    
    def show_all_announcements(self, e):
        """Navigate to posts view (no transition)"""
        # Simply call show_posts which already has the comprehensive UI
        self.show_posts()
    def show_error(self, message: str):
        """Show error message"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_400
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()