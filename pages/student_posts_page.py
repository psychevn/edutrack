import flet as ft
from datetime import datetime, timedelta
import json
from database.database_manager import DatabaseManager

class StudentPostsPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        print("=== STUDENT POSTS PAGE INIT STARTED ===")
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        print(f"User data: {self.user_data}")
        self.posts = []
        self.announcements = []
        self.assessments = []
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        self._pending_upload_post_id = None
        self.current_dialog = None  # Initialize dialog reference
        
        print("=== INITIALIZING UI ===")
        # Initialize UI components
        self.init_ui()
        print("=== LOADING DATA ===")
        self.load_data()
        print("=== STUDENT POSTS PAGE INIT COMPLETED ===")
    
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

    def create_nav_item(self, icon, text, index):
        """Create navigation item matching student dashboard style exactly"""
        is_selected = (index == 2)  # Posts is at index 2
        
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
            border_radius=0
        )

    def init_ui(self):
        """Initialize UI components"""
        # Left sidebar navigation (matching student dashboard)
        self.sidebar = ft.Container(
            content=ft.Column([
                # Profile section
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=self.create_profile_photo(),
                            alignment=ft.alignment.center,
                            width=240,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{self.user_data.get('full_name', 'Student') if self.user_data else 'Student'}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.center,
                            width=240,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "Student",
                                size=12,
                                color=ft.Colors.WHITE70,
                                text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.center,
                            width=240,
                        )
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5),
                    padding=ft.padding.all(20),
                    alignment=ft.alignment.center
                ),
                
                ft.Divider(color="#fafafa", height=20),
                
                # Navigation items
                ft.Container(
                    content=ft.Column([
                        self.create_nav_item(ft.Icons.PERSON_OUTLINED, "User", 0),
                        self.create_nav_item(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", 1),
                        self.create_nav_item(ft.Icons.ARTICLE_OUTLINED, "Posts", 2),
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
            bgcolor="#efaaaa",
            padding=ft.padding.all(0),
            margin=ft.margin.only(top=100),
            border_radius=ft.border_radius.only(
                top_left=0,
                top_right=120,
                bottom_left=0,
                bottom_right=0
            )
        )
        
        # Main content area - changed from white to light background
        self.main_content = ft.Container(
            expand=True,
            bgcolor="#f4f1ec",  # Light beige background instead of white
            padding=ft.padding.all(50)
        )

    def navigate_to(self, index):
        """Navigate to different sections"""
        if index == 0:  # User
            self.page.views.clear()
            from pages.student_user_page import StudentUserPage
            student_user = StudentUserPage(self.page, self.db_manager)
            self.page.views.append(student_user.get_view())
            self.page.update()
        elif index == 1:  # Dashboard
            print("=== NAVIGATING TO DASHBOARD ===")
            self.page.views.clear()
            from pages.student_dashboard import StudentDashboard
            student_dashboard = StudentDashboard(self.page, self.db_manager)
            self.page.views.append(student_dashboard.get_view())
            self.page.update()
        elif index == 2:  # Posts (current page - reload)
            print("=== NAVIGATING TO POSTS - RELOADING DATA ===")
            self.load_data()
        elif index == 3:  # Assessments
            self.page.views.clear()
            from pages.student_dashboard import StudentDashboard
            student_dashboard = StudentDashboard(self.page, self.db_manager)
            student_dashboard.selected_nav = 3
            self.page.views.append(student_dashboard.get_view())
            student_dashboard.show_available_exams()
            self.page.update()
        elif index == 4:  # Scores
            self.page.views.clear()
            from pages.student_dashboard import StudentDashboard
            student_dashboard = StudentDashboard(self.page, self.db_manager)
            student_dashboard.selected_nav = 4
            self.page.views.append(student_dashboard.get_view())
            student_dashboard.show_results()
            self.page.update()

    def logout(self, e):
        """Handle logout"""
        self.page.data = None
        self.page.go("/")
    
    def load_data(self):
        """Load posts, announcements, and assessments"""
        self.load_posts()
        self.load_announcements()
        self.load_assessments()
        self.show_posts_content()
    
    def load_posts(self):
        """Load posts filtered by student's section"""
        try:
            self.posts = self.db_manager.get_posts_for_student_section(self.user_data['id'])
            print(f"=== LOADED {len(self.posts)} POSTS ===")
            for i, post in enumerate(self.posts):
                print(f"Post {i}: ID={post.get('id')}, Title={post.get('title')}")
        except Exception as e:
            print(f"Error loading posts: {e}")
            self.posts = []
    
    def load_announcements(self):
        """Load active announcements only"""
        try:
            self.announcements = self.db_manager.get_active_announcements()
        except Exception as e:
            print(f"Error loading announcements: {e}")
            self.announcements = []
    
    def load_assessments(self):
        """Load assessments for student"""
        try:
            self.assessments = self.db_manager.get_assessments(user_id=self.user_data['id'], role='student')
        except Exception as e:
            print(f"Error loading assessments: {e}")
            self.assessments = []
    
    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return ""
        try:
            from datetime import datetime
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime("%b %d, %Y")
            return str(date_str)
        except:
            return str(date_str)
    
    def _build_section_header(self, icon, title):
        """Build standardized header"""
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
            padding=ft.padding.symmetric(horizontal=0, vertical=15),
            height=60,
            bgcolor="#f4f1ec",
            margin=ft.margin.only(bottom=20)
        )

    def show_posts_content(self):
        """Show comprehensive posts content with all three sections"""
        print(f"=== SHOW_POSTS_CONTENT CALLED ===")
        print(f"Posts: {len(self.posts)}")
        print(f"Announcements: {len(self.announcements)}")
        print(f"Assessments: {len(self.assessments)}")
        
        # Header with test button
        def test_button_click(e):
            print("=== TEST BUTTON CLICKED ===")
            test_dialog = ft.AlertDialog(
                title=ft.Text("Test Button Works!"),
                content=ft.Text("This confirms that buttons and dialogs are working."),
                actions=[ft.TextButton("OK", on_click=lambda e: self.page.close(test_dialog))]
            )
            self.page.dialog = test_dialog
            test_dialog.open = True
            self.page.update()
            print("Test dialog should be visible")
        
        header = ft.Column([
            self._build_section_header(ft.Icons.ARTICLE, "Posts & Announcements"),
            ft.Container(
                content=ft.ElevatedButton(
                    "TEST DIALOG BUTTON",
                    icon=ft.Icons.BUG_REPORT,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    on_click=test_button_click
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.all(10)
            )
        ], spacing=0)
        
        # Create content sections
        content_sections = []

        # 1. Announcements Section
        if self.announcements:
            announcement_cards = []
            for announcement in self.announcements:
                announcement_cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Icon(ft.Icons.CAMPAIGN, size=20, color=ft.Colors.WHITE),
                                    width=40,
                                    height=40,
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
                                    ft.Text(
                                        self.format_date(announcement.get('created_at', '')),
                                        size=12,
                                        color="#9CA3AF"
                                    )
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
                                ft.ElevatedButton(
                                    "Comments",
                                    icon=ft.Icons.COMMENT,
                                    style=ft.ButtonStyle(
                                        bgcolor="#D4817A",
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=8)
                                    ),
                                    on_click=lambda e, aid=announcement.get('id'), title=announcement.get('title', 'Announcement'): self.handle_comment_click(aid, title)
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
                ft.Column([
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

        # 2. Available Assessments Section
        if self.assessments:
            assessment_cards = []
            for assessment in self.assessments:
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
                                on_click=lambda e, aid=assessment['id']: self.handle_assessment_action(aid, is_submitted)
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
                ft.Column([
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

        # Assessment Posts Section - REMOVED as requested

        # If no content, show empty state
        if not content_sections:
            content_sections.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, size=64, color="#D1D5DB"),
                        ft.Container(height=16),
                        ft.Text(
                            "No announcements or assessments yet",
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

        # Scrollable content body
        content_body = ft.Column(
            content_sections, 
            spacing=25, 
            scroll=ft.ScrollMode.AUTO
        )

        # Standardized layout: header + scrollable content
        combined_content = ft.Column([
            header,
            ft.Container(
                content=content_body,
                expand=True,
                padding=ft.padding.all(0)
            )
        ], spacing=0, expand=True)
        

        self.main_content.content = combined_content
        self.page.update()
    
    def create_post_card_modern(self, post):
        """Create a modern post card"""
        print(f"=== CREATING CARD FOR POST {post.get('id')} ===")
        is_assessment = post.get('post_type') == 'assessment'
        
        primary_btn = None
        if is_assessment and post.get('assessment_id'):
            primary_btn = ft.ElevatedButton(
                "Take Assessment",
                icon=ft.Icons.PLAY_ARROW,
                style=ft.ButtonStyle(
                    bgcolor="#D4817A",
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    padding=ft.padding.symmetric(horizontal=20, vertical=10)
                ),
                on_click=lambda e, aid=post['assessment_id']: self.handle_assessment_action(aid, False)
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

        # Create comments button with direct lambda and explicit parameters
        print(f"Creating comments button for post {post['id']}")
        comments_btn = ft.ElevatedButton(
            "Comments",
            icon=ft.Icons.COMMENT,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TRANSPARENT,
                color="#D4817A",
                elevation=0,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=lambda e, pid=post['id'], title=post.get('title', 'Post'): self.handle_comment_click(pid, title)
        )
        print(f"Comments button created successfully")

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.Icons.ASSIGNMENT if is_assessment else ft.Icons.ARTICLE,
                        color="#D4817A",
                        size=20
                    ),
                    ft.Text(
                        post.get('title', 'Post'),
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                        size=16,
                        expand=True
                    ),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Text(
                    post.get('description') or post.get('content') or "No description available",
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
    
    def handle_assessment_action(self, assessment_id, is_submitted):
        """Handle assessment button click"""
        if is_submitted:
            from pages.student_results_page import StudentResultsPage
            self.page.views.clear()
            results_page = StudentResultsPage(self.page, self.db_manager, self.user_data, assessment_id)
            self.page.views.append(results_page.get_view())
            self.page.update()
        else:
            # Navigate back to dashboard to take assessment
            self.page.views.clear()
            from pages.student_dashboard import StudentDashboard
            student_dashboard = StudentDashboard(self.page, self.db_manager)
            self.page.views.append(student_dashboard.get_view())
            student_dashboard.take_exam(assessment_id)
            self.page.update()
    
    def choose_file_for_submission(self, post_id):
        """Choose file for submission"""
        self._pending_upload_post_id = post_id
        self.file_picker.pick_files(allow_multiple=False)
    
    def on_file_picked(self, e):
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
    
    def handle_comment_click(self, post_id, post_title):
        """Handle comment button click - separate method for better debugging"""
        print(f"=== COMMENT BUTTON CLICKED ===")
        print(f"Post ID: {post_id}")
        print(f"Post Title: {post_title}")
        print(f"User Data: {self.user_data}")
        print(f"Page: {self.page}")
        
        try:
            self.open_comments_dialog(post_id, post_title)
        except Exception as e:
            print(f"ERROR in handle_comment_click: {e}")
            import traceback
            traceback.print_exc()
    
    def open_comments_dialog(self, post_id, post_title):
        """Open comments dialog - using working pattern from student_dashboard"""
        print(f"Opening comments dialog for post {post_id}: {post_title}")
        
        comments = self.db_manager.get_comments(post_id)
        print(f"Found {len(comments)} comments")
        
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
                new_comments = self.db_manager.get_comments(post_id)
                comments_list.controls.clear()
                for c in new_comments:
                    comment_card = ft.Container(
                        content=ft.Column([
                            ft.Text(c['user_name'], size=12, weight=ft.FontWeight.BOLD, color="#D4817A"),
                            ft.Text(c['content'], size=12, color=ft.Colors.BLACK87)
                        ], spacing=4),
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.padding.all(10),
                        border_radius=8,
                        border=ft.border.all(1, "#E8B4CB")
                    )
                    comments_list.controls.append(comment_card)
                self.page.update()
        
        # Use the exact same pattern as working student_dashboard dialog
        dialog = ft.AlertDialog(
            title=ft.Text(f"Comments - {post_title}", color="#D4817A"),
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
                    on_click=lambda e: self.page.close(dialog)  # Use page.close like working example
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
        # Use the exact same pattern as working student_dashboard dialog
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        print("Dialog opened using working pattern")
    
    def close_dialog(self):
        """Close the dialog properly"""
        if hasattr(self, 'current_dialog') and self.current_dialog:
            self.current_dialog.open = False
            self.page.dialog = None
            self.current_dialog = None
            self.page.update()
    
    def show_success(self, message):
        """Show success message"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_400
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def show_error(self, message):
        """Show error message"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_400
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def get_view(self):
        """Get the main view for this page"""
        return ft.View(
            "/student-posts",
            [
                ft.Container(
                    content=ft.Row([
                        self.sidebar,
                        ft.Container(
                            content=self.main_content, 
                            expand=True,
                            margin=ft.margin.all(10),  # Add margin to show border radius
                            border_radius=20,  # Move border radius here
                            bgcolor="#e8e0d5"  # Ensure background color
                        )
                    ], expand=True, spacing=0),
                    expand=True,
                    bgcolor="#e8e0d5"  # Slightly darker background to show contrast
                )
            ],
            padding=0,           
            bgcolor="#e8e0d5",
        )