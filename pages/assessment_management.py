import flet as ft
from datetime import datetime, timedelta
import json
from database.database_manager import DatabaseManager

class AssessmentManagementPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        self.assessments = []
        self.draft_assessments = []
        self.active_assessments = []
        self.all_assessments = []
        
        # Initialize UI components
        self.init_ui()
        self.load_assessments()
        self.load_stats()
    
    def init_ui(self):
        """Initialize UI components matching the screenshot design"""
        # Left sidebar navigation
        self.sidebar = ft.Container(
            content=ft.Column([
                # Profile section
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Stack([
                                ft.Container(
                                    width=80,
                                    height=80,
                                    border_radius=40,
                                    bgcolor="#E8F4FD"
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.LANDSCAPE, size=40, color="#87CEEB"),
                                    alignment=ft.alignment.center,
                                    width=80,
                                    height=80
                                )
                            ]),
                            alignment=ft.alignment.center
                        ),
                        ft.Text(
                            "Surname,",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "firstname",
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
                        self.create_nav_item(ft.Icons.HOME, "Dashboard", False),
                        self.create_nav_item(ft.Icons.ASSIGNMENT, "Assessments", True),  # Active
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
                    ),
                    alignment=ft.alignment.center,
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
        
        # Main content area
        self.main_content = ft.Container(
            expand=True,
            bgcolor="#f4f1ec",  # Light beige background
            padding=ft.padding.all(30)
        )
    
    def create_nav_item(self, icon, text, is_active):
        """Create a navigation item matching the screenshot style"""
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
                on_click=lambda e, nav_text=text: self.navigate_to(nav_text),
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    overlay_color=ft.Colors.WHITE10,
                    shape=ft.RoundedRectangleBorder(radius=0)
                )
            ),
            bgcolor="#bb5862" if is_active else ft.Colors.TRANSPARENT,  # Active background
            border_radius=0
        )
    
    def navigate_to(self, nav_text):
        """Handle navigation"""
        if nav_text == "Dashboard":
            self.page.go("/admin")
        elif nav_text == "User":
            # Navigate to user management (if implemented)
            pass
        elif nav_text == "Scores":
            # Navigate to scores (if implemented)
            pass
        # Stay on assessments page for "Assessments"
    
    def load_stats(self):
        """Load assessment statistics"""
        self.total_assessments = len(self.all_assessments)
        self.active_assessments_count = len(self.active_assessments)
        self.draft_assessments_count = len(self.draft_assessments)
    
    def load_assessments(self):
        """Load assessments from database"""
        try:
            # First, fix any assessments with missing status values
            self.db_manager.fix_assessment_status_values()
            
            self.all_assessments = self.db_manager.get_assessments(user_id=self.user_data['id'], role='admin')
            self.draft_assessments = [a for a in self.all_assessments if a.get('status') == 'draft']
            self.active_assessments = [a for a in self.all_assessments if a.get('status') == 'published']
            print(f"Loaded assessments: Total={len(self.all_assessments)}, Draft={len(self.draft_assessments)}, Active={len(self.active_assessments)}")
                
        except Exception as e:
            print(f"Error loading assessments: {e}")
            self.all_assessments = []
            self.draft_assessments = []
            self.active_assessments = []
    
    def create_metrics_section(self):
        """Create the key metrics section with three boxes"""
        return ft.Row([
            self.create_metric_box(str(len(self.all_assessments)), "Total Assessment", "#bb5862"),
            self.create_metric_box(str(len(self.active_assessments)), "Active Assessment", "#bb5862"),
            self.create_metric_box(str(len(self.draft_assessments)), "Draft Assessment", "#bb5862")
        ], spacing=30)
    
    def create_metric_box(self, value, title, color):
        """Create a metric box matching the screenshot"""
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
            border_radius=15,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, "#efb6aa"),
    )
    
    def create_assessment_containers(self):
        """Create the three assessment containers"""
        return ft.Row([
            # Draft Assessments
            self.create_assessment_container(
                "Draft Assessments",
                ft.Icons.REFRESH,
                self.draft_assessments,
                "Assessments currently being prepared and not yet published to students.",
                "#E8B4CB"
            ),
            # Active Assessments
            self.create_assessment_container(
                "Active Assessments",
                ft.Icons.CLOUD,
                self.active_assessments,
                "Assessments currently available for students to take.",
                "#E8B4CB"
            ),
            # All Assessments
            self.create_assessment_container(
                "All Assessments",
                ft.Icons.LIST,
                self.all_assessments,
                "Complete list of all assessments in the system.",
                "#E8B4CB"
            )
        ], spacing=20)
    
    def create_assessment_container(self, title, icon, assessments, description, border_color):
        """Create an assessment container"""
        # Determine card type for button configuration
        card_type = "draft" if "Draft" in title else ("active" if "Active" in title else "all")
        
        # Create assessment cards - show all assessments, not just first 3
        assessment_cards = []
        for assessment in assessments:
            assessment_cards.append(self.create_assessment_card(assessment, card_type))
        
        # Add empty state if no assessments
        if not assessment_cards:
            assessment_cards.append(
                ft.Container(
                    content=ft.Text(
                        "No assessments available",
                        color=ft.Colors.BLACK54,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    height=100
                )
            )
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Icon(icon, color="#D4817A", size=20),
                    ft.Text(
                        title,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Text(
                            str(len(assessments)),
                            color=ft.Colors.WHITE,
                            size=12,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor="#D4817A",
                        width=24,
                        height=24,
                        border_radius=12,
                        alignment=ft.alignment.center
                    ) if assessments else ft.Container()
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Text(
                    description,
                    size=12,
                    color=ft.Colors.BLACK54
                ),
                
                ft.Container(height=15),
                
                # Assessment cards - Make scrollable
                ft.Container(
                    content=ft.ListView(
                        controls=assessment_cards,
                        spacing=10,
                        expand=True
                    ),
                    height=250,  # Fixed height to enable scrolling
                    expand=True
                )
                
            ], spacing=10),
            width=300,
            height=400,
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, border_color),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_assessment_card(self, assessment, card_type="all"):
        """Create an individual assessment card with appropriate buttons based on type"""
        # Get question count from database
        try:
            questions = self.db_manager.get_questions(assessment['id'])
            question_count = len(questions)
        except:
            question_count = 0
        
        # Format date
        try:
            from datetime import datetime
            date_str = assessment.get('created_at', '')
            if date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%b %d")
            else:
                formatted_date = "Dec 12"
        except:
            formatted_date = "Dec 12"
        
        # Create buttons based on card type and status
        buttons = []
        status = assessment.get('status', 'draft')
        
        # View button (always present)
        buttons.append(
            ft.IconButton(
                ft.Icons.VISIBILITY,
                icon_color="#4285f4",  # Blue color matching the image
                icon_size=16,
                tooltip="View",
                on_click=lambda e, aid=assessment['id']: (print(f"BUTTON: View button clicked for assessment ID: {aid}"), self.view_assessment(aid))[1]
            )
        )
        
        # Conditional buttons based on status and card type
        if status == 'draft':
            # Draft: view, publish, delete, edit
            buttons.extend([
                ft.IconButton(
                    ft.Icons.CHECK_CIRCLE,
                    icon_color="#34a853",  # Green color matching the image
                    icon_size=16,
                    tooltip="Publish",
                    on_click=lambda e, aid=assessment['id']: self.publish_assessment(aid)
                ),
                ft.IconButton(
                    ft.Icons.DELETE,
                    icon_color="#ea4335",  # Red color matching the image
                    icon_size=16,
                    tooltip="Delete",
                    on_click=lambda e, aid=assessment['id']: self.delete_assessment(aid)
                ),
                ft.IconButton(
                    ft.Icons.EDIT,
                    icon_color="#fbbc04",  # Orange/yellow color matching the image
                    icon_size=16,
                    tooltip="Edit",
                    on_click=lambda e, aid=assessment['id']: (print(f"BUTTON: Edit button (draft) clicked for assessment ID: {aid}"), self.edit_assessment(aid))[1]
                )
            ])
        else:
            # Active/Published: view, unpublish, delete, edit
            buttons.extend([
                ft.IconButton(
                    ft.Icons.UNPUBLISHED,
                    icon_color="#ff9800",  # Orange color
                    icon_size=16,
                    tooltip="Unpublish",
                    on_click=lambda e, aid=assessment['id']: self.unpublish_assessment(aid)
                ),
                ft.IconButton(
                    ft.Icons.DELETE,
                    icon_color="#ea4335",  # Red color
                    icon_size=16,
                    tooltip="Delete",
                    on_click=lambda e, aid=assessment['id']: self.delete_assessment(aid)
                ),
                ft.IconButton(
                    ft.Icons.EDIT,
                    icon_color="#fbbc04",  # Orange/yellow color
                    icon_size=16,
                    tooltip="Edit",
                    on_click=lambda e, aid=assessment['id']: (print(f"BUTTON: Edit button (published) clicked for assessment ID: {aid}"), self.edit_assessment(aid))[1]
                )
            ])
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        assessment.get('title', 'Untitled Assessment'),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                        expand=True
                    )
                ]),
                ft.Text(
                    f"{formatted_date} - {question_count} Questions",
                    size=12,
                    color=ft.Colors.BLACK54
                ),
                ft.Text(
                    assessment.get('description', 'No description available')[:50] + "...",
                    size=11,
                    color=ft.Colors.BLACK45
                ),
                ft.Container(height=8),
                ft.Row(
                    buttons,
                    alignment=ft.MainAxisAlignment.START,
                    spacing=5
                )
            ], spacing=4),
            padding=ft.padding.all(12),
            bgcolor="#f8f9fa",
            border_radius=8,
            border=ft.border.all(1, "#E8B4CB")
        )
    
    def create_header(self):
        """Create the page header (aligned with Admin Dashboard header spacing)."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, size=28, color="#D4817A"),
                ft.Text(
                    "Assessment Management",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color="#D4817A"
                ),
                ft.Container(expand=True),
                ft.Text(
                    datetime.now().strftime("%B %d, %Y"),
                    size=14,
                    color="#D4817A"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=30)
        )
    
    def create_assessment_button(self):
        """Create the Create Assessment button"""
        return ft.ElevatedButton(
            "Create Assessment",
            icon=ft.Icons.EDIT,
            style=ft.ButtonStyle(
                bgcolor="#bb5862",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=24, vertical=12)
            ),
            on_click=self.create_assessment
        )
    
    def navigate_to_create_assessment(self, assessment_id=None):
        """Navigate to create assessment page with optional assessment ID for editing"""
        try:
            print(f"NAVIGATE: Called with assessment_id: {assessment_id}")
            print(f"NAVIGATE: Type of assessment_id: {type(assessment_id)}")
            
            # Import here to avoid circular imports
            from pages.create_assessment import CreateAssessmentPage
            
            # Clear current views
            self.page.views.clear()
            
            # Create the assessment page with optional assessment ID
            sections = ["1A", "2A", "3A", "4A", "1B", "2B", "3B", "4B"]  # Default sections
            print(f"NAVIGATE: About to create CreateAssessmentPage with assessment_id: {assessment_id}")
            create_page = CreateAssessmentPage(self.page, self.db_manager, sections, assessment_id)
            
            # Add the view
            print(f"NAVIGATE: Adding view to page...")
            self.page.views.append(create_page.get_view())
            self.page.update()
            
            # Load data after view is created and added to page
            if assessment_id is not None:
                print(f"NAVIGATE: Loading data after view creation for ID: {assessment_id}")
                create_page.load_data_after_view_created()
            else:
                print(f"NAVIGATE: No assessment_id provided, skipping data loading")
            
            print(f"NAVIGATE: Navigation completed")
            
        except Exception as e:
            print(f"NAVIGATE ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    def create_assessment(self, e):
        """Handle create assessment button click"""
        # Navigate to assessment creation (no assessment_id for new assessment)
        print(f"CREATE: Create assessment button clicked")
        self.navigate_to_create_assessment(None)
    
    def view_assessment(self, assessment_id):
        """Navigate to create assessment page in view/edit mode"""
        try:
            print(f"🔍 View assessment clicked for ID: {assessment_id}")
            # Navigate to create assessment page with the assessment ID for viewing/editing
            self.navigate_to_create_assessment(assessment_id)
            
        except Exception as e:
            print(f"❌ Error navigating to view assessment: {e}")
            import traceback
            traceback.print_exc()
    
    def publish_assessment(self, assessment_id):
        """Publish a draft assessment"""
        try:
            # Update assessment status to published
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE assessments SET status = 'published' WHERE id = ?",
                (assessment_id,)
            )
            conn.commit()
            conn.close()
            
            # Reload assessments and refresh UI
            self.load_assessments()
            self.load_stats()
            self._refresh_content()
            
            self.page.show_snackbar(
                ft.SnackBar(content=ft.Text("Assessment published successfully!"), bgcolor=ft.Colors.GREEN)
            )
        except Exception as e:
            self.page.show_snackbar(
                ft.SnackBar(content=ft.Text(f"Error publishing assessment: {e}"), bgcolor=ft.Colors.RED)
            )
    
    def unpublish_assessment(self, assessment_id):
        """Unpublish a published assessment"""
        try:
            # Update assessment status to draft
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE assessments SET status = 'draft' WHERE id = ?",
                (assessment_id,)
            )
            conn.commit()
            conn.close()
            
            # Reload assessments and refresh UI
            self.load_assessments()
            self.load_stats()
            self._refresh_content()
            
            self.page.show_snackbar(
                ft.SnackBar(content=ft.Text("Assessment unpublished successfully!"), bgcolor=ft.Colors.GREEN)
            )
        except Exception as e:
            self.page.show_snackbar(
                ft.SnackBar(content=ft.Text(f"Error unpublishing assessment: {e}"), bgcolor=ft.Colors.RED)
            )
    
    def delete_assessment(self, assessment_id):
        """Delete an assessment"""
        def confirm_delete(e):
            try:
                # Delete from database
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                
                # Delete questions first (foreign key constraint)
                cursor.execute("DELETE FROM questions WHERE assessment_id = ?", (assessment_id,))
                # Delete assessment
                cursor.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,))
                
                conn.commit()
                conn.close()
                
                # Reload assessments and refresh UI
                self.load_assessments()
                self.load_stats()
                self._refresh_content()
                
                self.page.show_snackbar(
                    ft.SnackBar(content=ft.Text("Assessment deleted successfully!"), bgcolor=ft.Colors.GREEN)
                )
                
                # Close dialog
                dialog.open = False
                self.page.update()
                
            except Exception as ex:
                self.page.show_snackbar(
                    ft.SnackBar(content=ft.Text(f"Error deleting assessment: {ex}"), bgcolor=ft.Colors.RED)
                )
        
        def cancel_delete(e):
            dialog.open = False
            self.page.update()
        
        # Show confirmation dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this assessment? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def edit_assessment(self, assessment_id):
        """Navigate to create assessment page in edit mode"""
        try:
            # Navigate to create assessment page with the assessment ID for editing
            self.navigate_to_create_assessment(assessment_id)
            
        except Exception as e:
            print(f"Error navigating to edit assessment: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_content(self):
        """Refresh the page content"""
        # Recreate the main content
        content = ft.Column([
            self.create_header(),
            ft.Container(height=20),
            self.create_metrics_section(),
            ft.Container(height=20),
            self.create_assessment_button(),
            ft.Container(height=20),
            self.create_assessment_containers()
        ], spacing=0)
        
        self.main_content.content = content
        self.page.update()

    def logout(self, e):
        """Handle logout"""
        self.page.data = None
        self.page.go("/")
    
    def get_view(self):
        """Return the assessment management view"""
        # Create the main content
        content = ft.Column([
            # Header
            self.create_header(),
            ft.Container(height=20),
            
            # Metrics section
            self.create_metrics_section(),
            ft.Container(height=20),
            
            # Create Assessment button
            self.create_assessment_button(),
            ft.Container(height=20),
            
            # Assessment containers
            self.create_assessment_containers()
        ], spacing=0)
        
        self.main_content.content = content
        
        return ft.View(
            "/assessment-management",
            [
                ft.Container(
                    content=ft.Row([
                        self.sidebar,
                        self.main_content
                    ], expand=True, spacing=0),
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )

    def get_content_only(self):
        """Return only the Assessment Management main content (no sidebar, no View).
        This is used by AdminDashboard to embed Assessments inline for smooth navigation.
        """
        # Build the same content used in get_view()
        content = ft.Column([
            self.create_header(),
            ft.Container(height=20),
            self.create_metrics_section(),
            ft.Container(height=20),
            self.create_assessment_button(),
            ft.Container(height=20),
            self.create_assessment_containers()
        ], spacing=0)
        return content