import flet as ft
from datetime import datetime
from database.database_manager import DatabaseManager
from pages.create_announcement import show_create_announcement_dialog
import json

class AnnouncementPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        self.announcements = []
        
        # Load announcements
        self.load_announcements()
    
    def go_back_to_dashboard(self, e):
        """Go back to admin dashboard"""
        try:
            print("🔙 Going back to admin dashboard...")
            self.page.go("/admin")
            print("✅ Successfully navigated back to admin dashboard")
        except Exception as ex:
            print(f"❌ Error going back: {ex}")
            import traceback
            traceback.print_exc()
    
    def load_announcements(self):
        """Load all announcements"""
        try:
            self.announcements = self.db_manager.get_announcements()
            print(f"📢 Loaded {len(self.announcements)} announcements")
        except Exception as e:
            print(f"❌ Error loading announcements: {e}")
            self.announcements = []
    
    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%B %d, %Y at %I:%M %p")
        except:
            return date_str
    
    def create_header(self):
        """Create page header"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#D4817A",
                    icon_size=24,
                    tooltip="Back to Dashboard",
                    on_click=self.go_back_to_dashboard
                ),
                ft.Icon(ft.Icons.CAMPAIGN, size=28, color="#D4817A"),
                ft.Text("Announcement Management", size=24, weight=ft.FontWeight.BOLD, color="#D4817A"),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Create New Announcement",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor="#D4817A",
                        color=ft.Colors.WHITE,
                        padding=ft.padding.symmetric(horizontal=20, vertical=10)
                    ),
                    on_click=self.show_create_announcement_dialog
                ),
                ft.Text(datetime.now().strftime("%B %d, %Y"), size=14, color="#D4817A")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=20)
        )
    
    def create_announcement_card(self, announcement):
        """Create an announcement card"""
        # Parse target sections
        target_sections = "All Students"
        if announcement['target_sections']:
            try:
                sections = eval(announcement['target_sections'])  # Convert string back to list
                if sections:
                    target_sections = f"Sections: {', '.join(sections)}"
            except:
                target_sections = "All Students"
        
        # Status indicator
        status_color = ft.Colors.GREEN if announcement['is_active'] else ft.Colors.GREY
        status_text = "Active" if announcement['is_active'] else "Inactive"
        
        return ft.Container(
            content=ft.Column([
                # Header row
                ft.Row([
                    ft.Column([
                        ft.Text(
                            announcement['title'],
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#D4817A"
                        ),
                        ft.Text(
                            f"Created: {self.format_date(announcement['created_at'])}",
                            size=12,
                            color=ft.Colors.GREY_600
                        )
                    ], expand=True),
                    ft.Container(
                        content=ft.Text(status_text, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=15
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=10),
                
                # Content
                ft.Text(
                    announcement['content'],
                    size=14,
                    color=ft.Colors.BLACK87
                ),
                
                ft.Container(height=10),
                
                # Target and actions row
                ft.Row([
                    ft.Text(
                        target_sections,
                        size=12,
                        color=ft.Colors.GREY_600,
                        italic=True
                    ),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color="#D4817A",
                            tooltip="Edit Announcement",
                            on_click=lambda e, aid=announcement['id']: self.edit_announcement(aid, e)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_RED_EYE,
                            icon_color=ft.Colors.BLUE,
                            tooltip="View Details",
                            on_click=lambda e, aid=announcement['id']: self.view_announcement(aid, e)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.TOGGLE_ON if announcement['is_active'] else ft.Icons.TOGGLE_OFF,
                            icon_color=ft.Colors.GREEN if announcement['is_active'] else ft.Colors.GREY,
                            tooltip="Toggle Active Status",
                            on_click=lambda e, aid=announcement['id']: self.toggle_announcement_status(aid, e)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            tooltip="Delete Announcement",
                            on_click=lambda e, aid=announcement['id']: self.delete_announcement(aid, e)
                        )
                    ], spacing=5)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            margin=ft.margin.only(bottom=15)
        )
    
    def show_create_announcement_dialog(self, e):
        """Show create announcement dialog using the modular create_announcement module"""
        show_create_announcement_dialog(
            page=self.page,
            user_data=self.user_data,
            refresh_callback=self.refresh_content
        )
    
    def edit_announcement(self, announcement_id, e=None):
        """Edit an announcement"""
        print(f"🔄 Edit announcement {announcement_id} clicked")
        
        # Find the announcement
        announcement = next((a for a in self.announcements if a['id'] == announcement_id), None)
        if not announcement:
            print(f"❌ Announcement {announcement_id} not found")
            self.show_snack_bar(f"Announcement {announcement_id} not found", ft.Colors.RED)
            return
        
        print(f"✅ Opening edit form for: {announcement['title']}")
        
        # Pre-fill fields with existing data
        title_field = ft.TextField(
            label="Announcement Title",
            border_radius=10,
            prefix_icon=ft.Icons.TITLE,
            value=announcement['title']
        )
        
        content_field = ft.TextField(
            label="Announcement Content",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=10,
            prefix_icon=ft.Icons.MESSAGE,
            value=announcement['content']
        )
        
        # Section selection with current values
        section_checkboxes = []
        sections = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
        
        # Parse current target sections
        current_sections = []
        if announcement['target_sections']:
            try:
                current_sections = eval(announcement['target_sections'])
            except:
                current_sections = []
        
        all_sections_checkbox = ft.Checkbox(
            label="All Students",
            value=not current_sections,  # True if no specific sections
            on_change=lambda e: self.toggle_all_sections(e, section_checkboxes)
        )
        
        for section in sections:
            checkbox = ft.Checkbox(
                label=f"Section {section}", 
                value=section in current_sections
            )
            section_checkboxes.append(checkbox)
        
        def update_announcement(e):
            try:
                if not title_field.value.strip() or not content_field.value.strip():
                    self.show_snack_bar("Please fill in both title and content", ft.Colors.ORANGE)
                    return
                
                # Get selected sections
                target_sections = None
                if not all_sections_checkbox.value:
                    target_sections = [cb.label.replace("Section ", "") for cb in section_checkboxes if cb.value]
                    if not target_sections:
                        self.show_snack_bar("Please select at least one section or choose 'All Students'", ft.Colors.ORANGE)
                        return
                
                # Update announcement
                success = self.db_manager.update_announcement(
                    announcement_id=announcement_id,
                    title=title_field.value.strip(),
                    content=content_field.value.strip(),
                    target_sections=str(target_sections) if target_sections else None
                )
                
                if success:
                    edit_bottom_sheet.open = False
                    self.refresh_content()
                    self.show_snack_bar("Announcement updated successfully!", ft.Colors.GREEN)
                    print(f"✅ Updated announcement {announcement_id}")
                else:
                    self.show_snack_bar("Failed to update announcement", ft.Colors.RED)
                    print(f"❌ Failed to update announcement {announcement_id}")
                    
            except Exception as ex:
                print(f"❌ Error updating announcement: {ex}")
                self.show_snack_bar(f"Error updating announcement: {ex}", ft.Colors.RED)
        
        # Create edit bottom sheet
        edit_bottom_sheet = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    # Header
                    ft.Row([
                        ft.Text("Edit Announcement", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=lambda e: setattr(edit_bottom_sheet, 'open', False)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(),
                    
                    # Form fields
                    title_field,
                    ft.Container(height=10),
                    content_field,
                    ft.Container(height=15),
                    ft.Text("Target Audience:", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    all_sections_checkbox,
                    ft.Container(height=5),
                    ft.Text("Or select specific sections:", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=5),
                    ft.Column([
                        ft.Row(section_checkboxes[:4], spacing=10),
                        ft.Row(section_checkboxes[4:], spacing=10)
                    ], spacing=5),
                    
                    ft.Container(height=20),
                    
                    # Action buttons
                    ft.Row([
                        ft.TextButton("Cancel", on_click=lambda e: setattr(edit_bottom_sheet, 'open', False)),
                        ft.ElevatedButton(
                            "Update Announcement",
                            on_click=update_announcement,
                            style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE)
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.all(20),
                height=600
            ),
            open=True
        )
        
        self.page.bottom_sheet = edit_bottom_sheet
        edit_bottom_sheet.open = True
        self.page.update()
        print(f"✅ Edit bottom sheet should be visible now")
    
    def view_announcement(self, announcement_id, e=None):
        """View announcement in a modal with comments and reply capability"""
        print(f"👁️ View announcement {announcement_id} clicked")
        
        # Find the announcement
        announcement = next((a for a in self.announcements if a['id'] == announcement_id), None)
        if not announcement:
            print(f"❌ Announcement {announcement_id} not found")
            self.show_snack_bar(f"Announcement {announcement_id} not found", ft.Colors.RED)
            return

        def build_comments_list(aid):
            comments = self.db_manager.get_announcement_comments(aid)
            list_view = ft.ListView(spacing=8, padding=ft.padding.all(8), height=260)
            for c in comments:
                name = c.get('user_name') or 'User'
                when = self.format_date(c.get('created_at'))
                content_txt = c.get('content') or ''

                def make_reply_handler(target_name=name):
                    def _handler(ev):
                        reply_input.value = f"@{target_name} "
                        try:
                            reply_input.focus()
                        except Exception:
                            pass
                        self.page.update()
                    return _handler

                list_view.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(name, size=12, weight=ft.FontWeight.BOLD, color="#D4817A"),
                                ft.Container(expand=True),
                                ft.Text(when, size=11, color=ft.Colors.GREY_600)
                            ], spacing=6),
                            ft.Text(content_txt, size=12, color=ft.Colors.BLACK87),
                            ft.Row([
                                ft.Container(expand=True),
                                ft.TextButton(
                                    "Reply",
                                    icon=ft.Icons.REPLY,
                                    style=ft.ButtonStyle(color="#D4817A"),
                                    on_click=make_reply_handler()
                                )
                            ], alignment=ft.MainAxisAlignment.END)
                        ], spacing=4),
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.padding.all(10),
                        border_radius=8,
                        border=ft.border.all(1, "#E8B4CB")
                    )
                )
            return list_view

        comments_container = ft.Container()
        comments_container.content = build_comments_list(announcement_id)

        reply_input = ft.TextField(
            label="Write a reply",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=10,
            border_color="#E8B4CB",
            focused_border_color="#D4817A"
        )

        def send_reply(_):
            text = (reply_input.value or "").strip()
            if not text:
                return
            try:
                self.db_manager.add_announcement_comment(announcement_id, self.user_data['id'], text)
                reply_input.value = ""
                # refresh
                comments_container.content = build_comments_list(announcement_id)
                self.page.update()
            except Exception as ex:
                self.show_snack_bar(f"Error sending reply: {ex}", ft.Colors.RED)

        dialog_content = ft.Column([
            # Header
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.CAMPAIGN, size=22, color=ft.Colors.WHITE),
                    width=42,
                    height=42,
                    bgcolor="#D4817A",
                    border_radius=21,
                    alignment=ft.alignment.center
                ),
                ft.Column([
                    ft.Text(announcement['title'], size=18, weight=ft.FontWeight.BOLD, color="#1F2937"),
                    ft.Text(self.format_date(announcement['created_at']), size=12, color="#9CA3AF")
                ], spacing=2, expand=True),
            ], spacing=10),
            ft.Container(height=10),
            # Content
            ft.Container(
                content=ft.Text(announcement['content'], size=14, color="#374151", selectable=True),
                padding=ft.padding.all(12),
                bgcolor="#F9FAFB",
                border_radius=10,
                border=ft.border.all(1, "#E5E7EB")
            ),
            ft.Container(height=10),
            ft.Text("Comments", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
            comments_container,
            ft.Container(height=8),
            reply_input,
            ft.Row([
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Reply",
                    icon=ft.Icons.SEND,
                    on_click=send_reply,
                    style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))
                )
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=8, width=520, scroll=ft.ScrollMode.AUTO)

        def close_dialog(_=None):
            try:
                dialog.open = False
                self.page.update()
            except Exception:
                pass

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Announcement Details", color="#D4817A"),
            content=dialog_content,
            actions=[
                ft.TextButton("Close", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        print(f"✅ Announcement modal opened: {announcement['title']}")
        return
    
    def toggle_announcement_status(self, announcement_id, e=None):
        """Toggle announcement active status"""
        try:
            print(f"🔄 Toggling status for announcement {announcement_id}")
            
            # Use the database method to toggle status
            success = self.db_manager.toggle_announcement_status(announcement_id)
            
            if success:
                self.refresh_content()
                self.show_snack_bar("Announcement status updated successfully!", ft.Colors.GREEN)
                print(f"✅ Toggled status for announcement {announcement_id}")
            else:
                self.show_snack_bar("Failed to update announcement status", ft.Colors.RED)
                print(f"❌ Failed to toggle status for announcement {announcement_id}")
                    
        except Exception as ex:
            print(f"❌ Error toggling announcement status: {ex}")
            self.show_snack_bar(f"Error toggling announcement status: {ex}", ft.Colors.RED)
    
    def delete_announcement(self, announcement_id, e=None):
        """Delete an announcement with confirmation"""
        print(f"🔄 Delete announcement {announcement_id} clicked")
        
        # Find the announcement
        announcement = next((a for a in self.announcements if a['id'] == announcement_id), None)
        if not announcement:
            print(f"❌ Announcement {announcement_id} not found")
            self.show_snack_bar(f"Announcement {announcement_id} not found", ft.Colors.RED)
            return
        
        # Actually delete the announcement
        try:
            success = self.db_manager.delete_announcement(announcement_id)
            if success:
                self.refresh_content()
                self.show_snack_bar(f"DELETED: {announcement['title']}", ft.Colors.GREEN)
                print(f"✅ Deleted announcement: {announcement['title']}")
            else:
                self.show_snack_bar("Failed to delete announcement", ft.Colors.RED)
        except Exception as ex:
            self.show_snack_bar(f"Error deleting announcement: {ex}", ft.Colors.RED)
        return
        
        def confirm_delete(e):
            try:
                success = self.db_manager.delete_announcement(announcement_id)
                if success:
                    dialog.open = False
                    self.refresh_content()
                    self.show_snack_bar("Announcement deleted successfully!", ft.Colors.GREEN)
                else:
                    self.show_snack_bar("Failed to delete announcement", ft.Colors.RED)
            except Exception as ex:
                self.show_snack_bar(f"Error deleting announcement: {ex}", ft.Colors.RED)
        
        # Get announcement title for confirmation
        announcement = next((a for a in self.announcements if a['id'] == announcement_id), None)
        title = announcement['title'] if announcement else 'this announcement'
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=24),
                ft.Text("Confirm Delete", color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Text(f"Are you sure you want to delete '{title}'? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton(
                    "Yes, Delete",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    icon=ft.Icons.DELETE_FOREVER
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
        print(f"✅ Delete dialog should be visible now for announcement {announcement_id}")
        # Force dialog to show
        if not dialog.open:
            dialog.open = True
            self.page.update()
    
    def refresh_content(self):
        """Refresh the content and reload announcements"""
        # This method should be overridden by the parent container
        # For now, just update the page
        self.page.update()
    
    def show_snack_bar(self, message: str, color=ft.Colors.GREEN):
        """Helper method to show snack bar messages"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()
    
    def get_content_only(self):
        """Get the main content for inline display"""
        if not self.announcements:
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CAMPAIGN, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No announcements yet", size=18, color=ft.Colors.GREY_600),
                    ft.Text("Create your first announcement to communicate with students", size=14, color=ft.Colors.GREY_500),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Create First Announcement",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=20, vertical=10)
                        ),
                        on_click=self.show_create_announcement_dialog
                    )
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                height=400
            )
            
            return ft.Column([
                self.create_header(),
                empty_state
            ], spacing=20)
        
        # Create announcement cards
        announcement_cards = [self.create_announcement_card(announcement) for announcement in self.announcements]
        
        return ft.Column([
            self.create_header(),
            ft.Container(
                content=ft.Column(
                    announcement_cards,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO
                ),
                height=500,
                expand=True
            )
        ], spacing=20)
