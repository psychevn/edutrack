import flet as ft
from datetime import datetime
from database.database_manager import DatabaseManager
from pages.create_announcement import show_create_announcement_dialog
import json
import os
import shutil

class ClassfeedPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data
        self.announcements = []
        self.materials = []
        
        # Initialize file picker for material uploads
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        self.selected_file_path = None
        
        # Load data
        self.load_announcements()
        self.load_materials()
    

    
    def load_announcements(self):
        """Load all announcements"""
        try:
            self.announcements = self.db_manager.get_announcements()
            print(f"📢 Loaded {len(self.announcements)} announcements")
        except Exception as e:
            print(f"❌ Error loading announcements: {e}")
            self.announcements = []
    
    def load_materials(self):
        """Load all uploaded materials"""
        try:
            # Get materials from posts table where post_type is 'file'
            self.materials = self.db_manager.get_materials()
            print(f"📁 Loaded {len(self.materials)} materials")
        except Exception as e:
            print(f"❌ Error loading materials: {e}")
            self.materials = []
    
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
        """Create page header with buttons positioned under main header"""
        return ft.Container(
            content=ft.Column([
                # Main header row
                ft.Row([
                    ft.Icon(ft.Icons.CAMPAIGN, size=28, color="#D4817A"),
                    ft.Text("Classfeed", size=24, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    ft.Container(expand=True),
                    ft.Text(datetime.now().strftime("%B %d, %Y"), size=14, color="#D4817A")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=15),  # Spacing
                
                # Button row positioned under the main header
                ft.Row([
                    ft.ElevatedButton(
                        "Create Announcement",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=30, vertical=15)
                        ),
                        on_click=self.show_create_announcement_dialog,
                        width=200,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Upload Material",
                        icon=ft.Icons.UPLOAD_FILE,
                        style=ft.ButtonStyle(
                            bgcolor="#D4817A",
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(horizontal=30, vertical=15)
                        ),
                        on_click=self.show_upload_material_dialog,
                        width=200,
                        height=50
                    )
                ], spacing=15)
            ], spacing=0),
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
                            icon=ft.Icons.COMMENT,
                            icon_color="#D4817A",
                            tooltip="View Comments",
                            on_click=lambda e, ann=announcement: self.show_admin_comment_dialog(ann)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color="#D4817A",
                            tooltip="Edit Announcement",
                            on_click=lambda e, aid=announcement['id']: self.edit_announcement(aid, e)
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
    
    def create_material_card(self, material):
        """Create a material card similar to announcement cards"""
        # Get file name from path
        file_name = os.path.basename(material.get('file_path', 'Unknown File'))
        file_size = self.get_file_size(material.get('file_path', ''))
        
        return ft.Container(
            content=ft.Column([
                # Header row
                ft.Row([
                    ft.Column([
                        ft.Text(
                            material['title'],
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#D4817A"
                        ),
                        ft.Text(
                            f"Uploaded: {self.format_date(material['created_at'])}",
                            size=12,
                            color=ft.Colors.GREY_600
                        )
                    ], expand=True),
                    ft.Container(
                        content=ft.Text("Material", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.BLUE,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=15
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=10),
                
                # Content
                ft.Text(
                    material.get('description', 'No description provided'),
                    size=14,
                    color=ft.Colors.BLACK87
                ),
                
                ft.Container(height=10),
                
                # File info and actions row
                ft.Row([
                    ft.Column([
                        ft.Text(
                            f"File: {file_name}",
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True
                        ),
                        ft.Text(
                            f"Size: {file_size}",
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True
                        )
                    ], expand=True),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD,
                            icon_color=ft.Colors.GREEN,
                            tooltip="Download Material",
                            on_click=lambda e, mid=material['id']: self.download_material(mid, e)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color="#D4817A",
                            tooltip="Edit Material",
                            on_click=lambda e, mid=material['id']: self.edit_material(mid, e)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            tooltip="Delete Material",
                            on_click=lambda e, mid=material['id']: self.delete_material(mid, e)
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
    
    def get_file_size(self, file_path):
        """Get human readable file size"""
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            return "Unknown"
        except:
            return "Unknown"
    
    def show_create_announcement_dialog(self, e):
        """Show create announcement dialog using overlay"""
        print("🔄 Create Announcement button clicked!")
        try:
            # Create title and content fields
            title_field = ft.TextField(
                label="Announcement Title",
                hint_text="Enter announcement title",
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            content_field = ft.TextField(
                label="Announcement Content",
                hint_text="Enter announcement content",
                multiline=True,
                min_lines=4,
                max_lines=8,
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            def close_overlay():
                # Remove only the dialog overlay, keep file picker
                if len(self.page.overlay) > 1:
                    self.page.overlay.pop()  # Remove the dialog overlay
                else:
                    self.page.overlay.clear()
                    # Re-add file picker
                    self.page.overlay.append(self.file_picker)
                self.page.update()
            
            # Section selection for announcements
            sections = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
            announcement_section_checkboxes = []
            
            announcement_all_sections_checkbox = ft.Checkbox(
                label="All Students",
                value=True,
                on_change=lambda e: self.toggle_all_sections(e, announcement_section_checkboxes)
            )
            
            for section in sections:
                checkbox = ft.Checkbox(label=f"Section {section}", value=False)
                announcement_section_checkboxes.append(checkbox)
            
            def create_announcement():
                if not title_field.value or not content_field.value:
                    self.show_snack_bar("Please fill in all fields", ft.Colors.ORANGE)
                    return
                
                # Get selected sections
                target_sections = None
                if not announcement_all_sections_checkbox.value:
                    target_sections = [cb.label.replace("Section ", "") for cb in announcement_section_checkboxes if cb.value]
                    if not target_sections:
                        self.show_snack_bar("Please select at least one section or choose 'All Students'", ft.Colors.ORANGE)
                        return
                
                # Create announcement in database
                success = self.db_manager.create_announcement(
                    title=title_field.value.strip(),
                    content=content_field.value.strip(),
                    created_by=self.user_data['id'],
                    target_sections=str(target_sections) if target_sections else None
                )
                
                if success:
                    self.refresh_content()
                    self.show_snack_bar(f"Announcement '{title_field.value}' created successfully!", ft.Colors.GREEN)
                    close_overlay()
                else:
                    self.show_snack_bar("Failed to create announcement", ft.Colors.RED)
            
            # Create overlay dialog
            overlay_dialog = ft.Container(
                content=ft.Container(
                    content=ft.Column([
                        # Header
                        ft.Row([
                            ft.Icon(ft.Icons.CAMPAIGN, color="#D4817A", size=24),
                            ft.Text("Create Announcement", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: close_overlay())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Divider(),
                        
                        # Form fields
                        title_field,
                        ft.Container(height=10),
                        content_field,
                        ft.Container(height=15),
                        
                        # Target audience
                        ft.Text("Target Audience:", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        announcement_all_sections_checkbox,
                        ft.Container(height=5),
                        ft.Text("Or select specific sections:", size=12, color=ft.Colors.GREY_600),
                        ft.Container(height=5),
                        ft.Column([
                            ft.Row(announcement_section_checkboxes[:4], spacing=10),
                            ft.Row(announcement_section_checkboxes[4:], spacing=10)
                        ], spacing=5),
                        ft.Container(height=20),
                        
                        # Action buttons
                        ft.Row([
                            ft.TextButton("Cancel", on_click=lambda e: close_overlay()),
                            ft.ElevatedButton(
                                "Create Announcement",
                                icon=ft.Icons.SEND,
                                style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE),
                                on_click=lambda e: create_announcement()
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=15, scroll=ft.ScrollMode.AUTO),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    padding=30,
                    width=500,
                    shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
                ),
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                alignment=ft.alignment.center,
                expand=True
            )
            
            self.page.overlay.append(overlay_dialog)
            self.page.update()
            print("✅ Overlay dialog should be showing")
            
        except Exception as ex:
            print(f"❌ Error showing create announcement dialog: {ex}")
            import traceback
            traceback.print_exc()
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
    
    def show_upload_material_dialog(self, e):
        """Show upload material dialog using overlay"""
        print("🔄 Upload Material button clicked!")
        print("🔄 Opening upload material dialog...")
        
        try:
            # Create form fields
            title_field = ft.TextField(
                label="Material Title",
                hint_text="Enter material title",
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            description_field = ft.TextField(
                label="Description",
                hint_text="Enter description",
                multiline=True,
                min_lines=3,
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            file_info_text = ft.Text("No file selected", size=12, color=ft.Colors.GREY_600)
            
            def close_overlay():
                self.page.overlay.clear()
                self.page.update()
            
            def pick_file(e):
                self.file_picker.pick_files(
                    dialog_title="Select Material to Upload",
                    allow_multiple=False,
                    allowed_extensions=["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "jpg", "jpeg", "png", "gif"]
                )
            
            def update_file_info():
                if self.selected_file_path:
                    filename = os.path.basename(self.selected_file_path)
                    file_size = self.get_file_size(self.selected_file_path)
                    file_info_text.value = f"Selected: {filename} ({file_size})"
                    file_info_text.color = "#D4817A"
                else:
                    file_info_text.value = "No file selected"
                    file_info_text.color = ft.Colors.GREY_600
                self.page.update()
            
            # Store original file picker result handler
            original_handler = self.file_picker.on_result
            
            def temp_file_handler(e):
                if e.files and len(e.files) > 0:
                    self.selected_file_path = e.files[0].path
                else:
                    self.selected_file_path = None
                update_file_info()
            
            self.file_picker.on_result = temp_file_handler
            
            # Section selection
            sections = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
            section_checkboxes = []
            
            all_sections_checkbox = ft.Checkbox(
                label="All Students",
                value=True,
                on_change=lambda e: self.toggle_all_sections(e, section_checkboxes)
            )
            
            for section in sections:
                checkbox = ft.Checkbox(label=f"Section {section}", value=False)
                section_checkboxes.append(checkbox)
            
            def close_overlay_with_cleanup():
                # Remove only the dialog overlay, keep file picker
                if len(self.page.overlay) > 1:
                    self.page.overlay.pop()  # Remove the dialog overlay
                else:
                    self.page.overlay.clear()
                    # Re-add file picker
                    self.page.overlay.append(self.file_picker)
                # Restore original file picker handler
                self.file_picker.on_result = original_handler
                self.page.update()
            
            def upload_material():
                if not title_field.value:
                    self.show_snack_bar("Please enter a title", ft.Colors.ORANGE)
                    return
                
                if not self.selected_file_path:
                    self.show_snack_bar("Please select a file to upload", ft.Colors.ORANGE)
                    return
                
                # Get selected sections
                target_sections = None
                if not all_sections_checkbox.value:
                    target_sections = [cb.label.replace("Section ", "") for cb in section_checkboxes if cb.value]
                    if not target_sections:
                        self.show_snack_bar("Please select at least one section or choose 'All Students'", ft.Colors.ORANGE)
                        return
                
                # Copy file to uploads directory
                uploads_dir = os.path.join(os.getcwd(), "uploads", "materials")
                os.makedirs(uploads_dir, exist_ok=True)
                
                filename = os.path.basename(self.selected_file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                dest_path = os.path.join(uploads_dir, unique_filename)
                
                shutil.copy2(self.selected_file_path, dest_path)
                
                # Create material record in database
                success = self.db_manager.create_material(
                    title=title_field.value.strip(),
                    description=description_field.value.strip() or None,
                    file_path=dest_path,
                    created_by=self.user_data['id'],
                    target_sections=str(target_sections) if target_sections else None
                )
                
                if success:
                    self.refresh_content()
                    self.show_snack_bar(f"Material '{title_field.value}' uploaded successfully!", ft.Colors.GREEN)
                    close_overlay_with_cleanup()
                else:
                    self.show_snack_bar("Failed to upload material", ft.Colors.RED)
            
            # Create overlay dialog
            overlay_dialog = ft.Container(
                content=ft.Container(
                    content=ft.Column([
                        # Header
                        ft.Row([
                            ft.Icon(ft.Icons.UPLOAD_FILE, color="#D4817A", size=24),
                            ft.Text("Upload Material", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: close_overlay_with_cleanup())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Divider(),
                        
                        # Form fields
                        title_field,
                        ft.Container(height=10),
                        description_field,
                        ft.Container(height=15),
                        
                        # File selection
                        ft.Text("Select File:", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Row([
                            ft.ElevatedButton(
                                "Choose File",
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=pick_file,
                                style=ft.ButtonStyle(bgcolor="#F5E6E4", color="#D4817A")
                            ),
                            file_info_text
                        ], spacing=10),
                        ft.Container(height=15),
                        
                        # Target audience
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
                            ft.TextButton("Cancel", on_click=lambda e: close_overlay_with_cleanup()),
                            ft.ElevatedButton(
                                "Upload Material",
                                icon=ft.Icons.CLOUD_UPLOAD,
                                style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE),
                                on_click=lambda e: upload_material()
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=15, scroll=ft.ScrollMode.AUTO),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    padding=30,
                    width=500,
                    shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
                ),
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                alignment=ft.alignment.center,
                expand=True
            )
            
            self.page.overlay.append(overlay_dialog)
            self.page.update()
            print("✅ Upload overlay dialog should be showing")
            return
            
        except Exception as ex:
            print(f"❌ Error showing upload material dialog: {ex}")
            import traceback
            traceback.print_exc()
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
            return
    
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files and len(e.files) > 0:
            self.selected_file_path = e.files[0].path
            print(f"📁 File selected: {self.selected_file_path}")
        else:
            self.selected_file_path = None
            print("📁 No file selected")
    
    def toggle_all_sections(self, e, section_checkboxes):
        """Toggle all section checkboxes when 'All Students' is selected"""
        if e.control.value:
            # If "All Students" is checked, uncheck all section checkboxes
            for checkbox in section_checkboxes:
                checkbox.value = False
        self.page.update()
    
    def edit_announcement(self, announcement_id, e=None):
        """Edit an announcement using overlay dialog"""
        print(f"🔄 Edit Announcement button clicked for announcement {announcement_id}!")
        
        try:
            # Find the announcement
            announcement = next((a for a in self.announcements if a['id'] == announcement_id), None)
            if not announcement:
                print(f"❌ Announcement {announcement_id} not found")
                self.show_snack_bar(f"Announcement {announcement_id} not found", ft.Colors.RED)
                return
            
            print(f"✅ Opening edit form for: {announcement['title']}")
            
            # Create form fields pre-filled with existing data
            title_field = ft.TextField(
                label="Announcement Title",
                value=announcement['title'],
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            content_field = ft.TextField(
                label="Announcement Content",
                value=announcement.get('content', ''),
                multiline=True,
                min_lines=4,
                max_lines=8,
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            def close_overlay():
                # Remove only the dialog overlay, keep file picker
                if len(self.page.overlay) > 1:
                    self.page.overlay.pop()  # Remove the dialog overlay
                else:
                    self.page.overlay.clear()
                    # Re-add file picker
                    self.page.overlay.append(self.file_picker)
                self.page.update()
            
            def update_announcement():
                if not title_field.value or not content_field.value:
                    self.show_snack_bar("Please fill in all fields", ft.Colors.ORANGE)
                    return
                
                # Update announcement in database
                success = self.db_manager.update_announcement(
                    announcement_id=announcement_id,
                    title=title_field.value.strip(),
                    content=content_field.value.strip()
                )
                
                if success:
                    self.refresh_content()
                    self.show_snack_bar("Announcement updated successfully!", ft.Colors.GREEN)
                    close_overlay()
                else:
                    self.show_snack_bar("Failed to update announcement", ft.Colors.RED)
            
            # Create overlay dialog
            overlay_dialog = ft.Container(
                content=ft.Container(
                    content=ft.Column([
                        # Header
                        ft.Row([
                            ft.Icon(ft.Icons.EDIT, color="#D4817A", size=24),
                            ft.Text("Edit Announcement", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: close_overlay())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Divider(),
                        
                        # Form fields
                        title_field,
                        ft.Container(height=10),
                        content_field,
                        ft.Container(height=20),
                        
                        # Action buttons
                        ft.Row([
                            ft.TextButton("Cancel", on_click=lambda e: close_overlay()),
                            ft.ElevatedButton(
                                "Update Announcement",
                                icon=ft.Icons.SAVE,
                                style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE),
                                on_click=lambda e: update_announcement()
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=15, scroll=ft.ScrollMode.AUTO),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    padding=30,
                    width=500,
                    shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
                ),
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                alignment=ft.alignment.center,
                expand=True
            )
            
            self.page.overlay.append(overlay_dialog)
            self.page.update()
            print("✅ Edit announcement overlay dialog should be showing")
            
        except Exception as ex:
            print(f"❌ Error showing edit announcement dialog: {ex}")
            import traceback
            traceback.print_exc()
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
    
    def view_announcement(self, announcement_id, e=None):
        """View announcement details"""
        self.show_snack_bar(f"View announcement {announcement_id} - Feature to be implemented", ft.Colors.BLUE)
    
    def toggle_announcement_status(self, announcement_id, e=None):
        """Toggle announcement active status"""
        try:
            success = self.db_manager.toggle_announcement_status(announcement_id)
            if success:
                self.refresh_content()
                self.show_snack_bar("Announcement status updated!", ft.Colors.GREEN)
            else:
                self.show_snack_bar("Failed to update status", ft.Colors.RED)
        except Exception as ex:
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
    
    def delete_announcement(self, announcement_id, e=None):
        """Delete an announcement"""
        try:
            success = self.db_manager.delete_announcement(announcement_id)
            if success:
                self.refresh_content()
                self.show_snack_bar("Announcement deleted!", ft.Colors.GREEN)
            else:
                self.show_snack_bar("Failed to delete announcement", ft.Colors.RED)
        except Exception as ex:
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
    
    def download_material(self, material_id, e=None):
        """Download material"""
        self.show_snack_bar(f"Download material {material_id} - Feature to be implemented", ft.Colors.BLUE)
    
    def edit_material(self, material_id, e=None):
        """Edit material - show edit dialog with current data using overlay"""
        print(f"🔄 Edit Material button clicked for material {material_id}!")
        print(f"🔄 Edit material {material_id} clicked")
        
        try:
            # Find the material
            material = next((m for m in self.materials if m['id'] == material_id), None)
            if not material:
                print(f"❌ Material {material_id} not found")
                self.show_snack_bar(f"Material {material_id} not found", ft.Colors.RED)
                return
            
            print(f"✅ Opening edit form for: {material['title']}")
            
            # Create form fields pre-filled with existing data
            title_field = ft.TextField(
                label="Material Title",
                value=material['title'],
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            description_field = ft.TextField(
                label="Description",
                value=material.get('description', ''),
                multiline=True,
                min_lines=3,
                border_color="#D4817A",
                focused_border_color="#D4817A"
            )
            
            # Get file info
            file_name = os.path.basename(material.get('file_path', 'Unknown File'))
            file_size = self.get_file_size(material.get('file_path', ''))
            
            def close_overlay():
                # Remove only the dialog overlay, keep file picker
                if len(self.page.overlay) > 1:
                    self.page.overlay.pop()  # Remove the dialog overlay
                else:
                    self.page.overlay.clear()
                    # Re-add file picker
                    self.page.overlay.append(self.file_picker)
                self.page.update()
            
            def update_material():
                if not title_field.value:
                    self.show_snack_bar("Please enter a title", ft.Colors.ORANGE)
                    return
                
                # Update material in database
                success = self.db_manager.update_material(
                    material_id=material_id,
                    title=title_field.value.strip(),
                    description=description_field.value.strip() or None
                )
                
                if success:
                    self.refresh_content()
                    self.show_snack_bar("Material updated successfully!", ft.Colors.GREEN)
                    close_overlay()
                else:
                    self.show_snack_bar("Failed to update material", ft.Colors.RED)
            
            # Create overlay dialog
            overlay_dialog = ft.Container(
                content=ft.Container(
                    content=ft.Column([
                        # Header
                        ft.Row([
                            ft.Icon(ft.Icons.EDIT, color="#D4817A", size=24),
                            ft.Text("Edit Material", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: close_overlay())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Divider(),
                        
                        # Form fields
                        title_field,
                        ft.Container(height=10),
                        description_field,
                        ft.Container(height=15),
                        
                        # Current file info
                        ft.Text("Current File:", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Text(f"{file_name} ({file_size})", size=12, color="#D4817A"),
                        ft.Container(height=20),
                        
                        # Action buttons
                        ft.Row([
                            ft.TextButton("Cancel", on_click=lambda e: close_overlay()),
                            ft.ElevatedButton(
                                "Update Material",
                                icon=ft.Icons.SAVE,
                                style=ft.ButtonStyle(bgcolor="#D4817A", color=ft.Colors.WHITE),
                                on_click=lambda e: update_material()
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=15, scroll=ft.ScrollMode.AUTO),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    padding=30,
                    width=500,
                    shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
                ),
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                alignment=ft.alignment.center,
                expand=True
            )
            
            self.page.overlay.append(overlay_dialog)
            self.page.update()
            print("✅ Edit overlay dialog should be showing")
            return
            
        except Exception as ex:
            print(f"❌ Error showing edit dialog: {ex}")
            import traceback
            traceback.print_exc()
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
            return
    
    def delete_material(self, material_id, e=None):
        """Delete material"""
        try:
            success = self.db_manager.delete_material(material_id)
            if success:
                self.refresh_content()
                self.show_snack_bar("Material deleted!", ft.Colors.GREEN)
            else:
                self.show_snack_bar("Failed to delete material", ft.Colors.RED)
        except Exception as ex:
            self.show_snack_bar(f"Error: {ex}", ft.Colors.RED)
    
    def refresh_content(self):
        """Refresh the content and reload data"""
        self.load_announcements()
        self.load_materials()
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
        content_sections = []
        
        # Announcements section
        if self.announcements:
            announcement_cards = [self.create_announcement_card(announcement) for announcement in self.announcements]
            announcements_section = ft.Container(
                content=ft.Column([
                    ft.Text("Announcements", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    ft.Container(height=10),
                    ft.Column(announcement_cards, spacing=0)
                ], spacing=0),
                margin=ft.margin.only(bottom=30)
            )
            content_sections.append(announcements_section)
        
        # Materials section
        if self.materials:
            material_cards = [self.create_material_card(material) for material in self.materials]
            materials_section = ft.Container(
                content=ft.Column([
                    ft.Text("Uploaded Materials", size=20, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    ft.Container(height=10),
                    ft.Column(material_cards, spacing=0)
                ], spacing=0),
                margin=ft.margin.only(bottom=30)
            )
            content_sections.append(materials_section)
        
        # Empty state if no content
        if not self.announcements and not self.materials:
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CAMPAIGN, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No announcements or materials yet", size=18, color=ft.Colors.GREY_600),
                    ft.Text("Create your first announcement or upload materials to get started", size=14, color=ft.Colors.GREY_500),
                    ft.Container(height=20),
                    ft.Row([
                        ft.ElevatedButton(
                            "Create Announcement",
                            icon=ft.Icons.ADD,
                            style=ft.ButtonStyle(
                                bgcolor="#D4817A",
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(horizontal=20, vertical=10)
                            ),
                            on_click=self.show_create_announcement_dialog
                        ),
                        ft.ElevatedButton(
                            "Upload Material",
                            icon=ft.Icons.UPLOAD_FILE,
                            style=ft.ButtonStyle(
                                bgcolor="#D4817A",
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(horizontal=20, vertical=10)
                            ),
                            on_click=self.show_upload_material_dialog
                        )
                    ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                height=400
            )
            content_sections.append(empty_state)
        
        return ft.Column([
            self.create_header(),
            ft.Container(
                content=ft.Column(
                    content_sections,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO
                ),
                height=500,
                expand=True
            )
        ], spacing=20)
    
    def show_admin_comment_dialog(self, announcement):
        """Show admin comment dialog with social media style UI"""
        try:
            def close_dialog(e):
                if hasattr(self, 'admin_comment_dialog'):
                    self.admin_comment_dialog.open = False
                    self.page.update()
            
            # Get comments for this announcement
            comments = self.db_manager.get_announcement_comments(announcement.get('id'))
            
            # Create admin comment input field
            admin_comment_input = ft.TextField(
                hint_text="Reply as admin...",
                multiline=True,
                min_lines=1,
                max_lines=3,
                border_radius=20,
                filled=True,
                bgcolor="#FFF5F5",
                border_color=ft.Colors.TRANSPARENT,
                focused_border_color="#D4817A",
                content_padding=ft.padding.symmetric(horizontal=15, vertical=10)
            )
            
            # Comments list container
            comments_container = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, height=350)
            
            def refresh_comments():
                comments_container.controls.clear()
                updated_comments = self.db_manager.get_announcement_comments(announcement.get('id'))
                
                for comment in updated_comments:
                    # Determine if this is an admin comment
                    is_admin = comment.get('user_id') == self.user_data.get('id')
                    
                    # Create profile photo
                    profile_photo = self.create_admin_comment_profile_photo(
                        comment.get('profile_photo'), 
                        is_admin
                    )
                    
                    # Create comment card with admin styling
                    comment_card = ft.Container(
                        content=ft.Row([
                            profile_photo,
                            ft.Column([
                                ft.Row([
                                    ft.Text(
                                        comment.get('user_name', 'Unknown'),
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color="#D4817A" if is_admin else "#1F2937"
                                    ),
                                    ft.Container(
                                        content=ft.Text("ADMIN", size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                        bgcolor="#D4817A",
                                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                        border_radius=8
                                    ) if is_admin else ft.Container(),
                                    ft.Text("•", size=12, color="#9CA3AF"),
                                    ft.Text(
                                        self.format_date(comment.get('created_at', '')),
                                        size=12,
                                        color="#9CA3AF"
                                    )
                                ], spacing=6),
                                ft.Container(
                                    content=ft.Text(
                                        comment.get('content', ''),
                                        size=14,
                                        color="#374151",
                                        selectable=True
                                    ),
                                    padding=ft.padding.all(12),
                                    bgcolor="#FFF5F5" if is_admin else "#F9FAFB",
                                    border_radius=12,
                                    border=ft.border.all(1, "#F3C9C0" if is_admin else "#E5E7EB")
                                ),
                                ft.Row([
                                    ft.TextButton(
                                        "Reply",
                                        style=ft.ButtonStyle(
                                            color="#D4817A",
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4)
                                        ),
                                        on_click=lambda e, cid=comment.get('id'): self.show_admin_reply_input(cid)
                                    ),
                                    ft.TextButton(
                                        "Delete",
                                        style=ft.ButtonStyle(
                                            color=ft.Colors.RED_400,
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4)
                                        ),
                                        on_click=lambda e, cid=comment.get('id'): self.delete_comment(cid)
                                    ) if is_admin else ft.Container()
                                ], spacing=10)
                            ], spacing=6, expand=True)
                        ], spacing=12, alignment=ft.CrossAxisAlignment.START),
                        padding=ft.padding.all(16),
                        margin=ft.margin.only(bottom=12),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        border=ft.border.all(1, "#F3F4F6"),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                            offset=ft.Offset(0, 2)
                        )
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
                                    "Students haven't commented on this announcement yet.",
                                    size=14,
                                    color="#D1D5DB"
                                )
                            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(40)
                        )
                    )
                
                self.page.update()
            
            def send_admin_comment(e):
                text = admin_comment_input.value.strip() if admin_comment_input.value else ""
                if text:
                    try:
                        self.db_manager.add_announcement_comment(
                            announcement.get('id'), 
                            self.user_data['id'], 
                            text
                        )
                        admin_comment_input.value = ""
                        refresh_comments()
                    except Exception as ex:
                        print(f"Error adding admin comment: {ex}")
            
            # Initial load of comments
            refresh_comments()
            
            # Create the admin dialog
            self.admin_comment_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=24, color=ft.Colors.WHITE),
                        width=40,
                        height=40,
                        bgcolor="#D4817A",
                        border_radius=20,
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(
                            f"Comments: {announcement.get('title', 'Announcement')}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#1F2937"
                        ),
                        ft.Text(
                            "Admin View - You can reply and moderate comments",
                            size=12,
                            color="#9CA3AF"
                        )
                    ], spacing=2, expand=True)
                ], spacing=12),
                content=ft.Container(
                    content=ft.Column([
                        # Announcement preview
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    announcement.get('title', ''),
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color="#1F2937"
                                ),
                                ft.Text(
                                    announcement.get('content', ''),
                                    size=14,
                                    color="#374151",
                                    max_lines=2
                                )
                            ], spacing=4),
                            padding=ft.padding.all(16),
                            bgcolor="#F9FAFB",
                            border_radius=12,
                            border=ft.border.all(1, "#E5E7EB")
                        ),
                        ft.Container(height=10),
                        # Comments section
                        ft.Row([
                            ft.Text(
                                f"Comments ({len(comments)})",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color="#1F2937"
                            ),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=16, color="#D4817A")
                        ]),
                        comments_container,
                        # Admin comment input
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=18, color=ft.Colors.WHITE),
                                width=32,
                                height=32,
                                bgcolor="#D4817A",
                                border_radius=16,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(
                                content=admin_comment_input,
                                expand=True
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SEND,
                                icon_color="#D4817A",
                                bgcolor="#F3F4F6",
                                on_click=send_admin_comment,
                                tooltip="Send admin reply"
                            )
                        ], spacing=12, alignment=ft.CrossAxisAlignment.END)
                    ], spacing=12),
                    width=600,
                    height=550
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
            if self.admin_comment_dialog not in self.page.overlay:
                self.page.overlay.append(self.admin_comment_dialog)
            
            self.page.dialog = self.admin_comment_dialog
            self.admin_comment_dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"ERROR creating admin comment dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def create_admin_comment_profile_photo(self, profile_photo_path, is_admin=False):
        """Create a profile photo for admin comment view"""
        import os
        
        if profile_photo_path and os.path.exists(profile_photo_path):
            return ft.Container(
                content=ft.Image(
                    src=profile_photo_path,
                    width=36,
                    height=36,
                    fit=ft.ImageFit.COVER,
                    border_radius=18
                ),
                width=36,
                height=36,
                border_radius=18,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                border=ft.border.all(2, "#D4817A" if is_admin else ft.Colors.TRANSPARENT)
            )
        else:
            return ft.Container(
                content=ft.Icon(
                    ft.Icons.ADMIN_PANEL_SETTINGS if is_admin else ft.Icons.PERSON, 
                    size=20, 
                    color=ft.Colors.WHITE
                ),
                width=36,
                height=36,
                bgcolor="#D4817A" if is_admin else "#9CA3AF",
                border_radius=18,
                alignment=ft.alignment.center
            )
    
    def show_admin_reply_input(self, comment_id):
        """Show reply input for admin - placeholder for now"""
        print(f"Admin reply to comment {comment_id} - feature coming soon!")
    
    def delete_comment(self, comment_id):
        """Delete a comment - placeholder for now"""
        print(f"Delete comment {comment_id} - feature coming soon!")
    
    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return ""
        try:
            from datetime import datetime
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime("%b %d, %Y at %I:%M %p")
            return str(date_str)
        except:
            return str(date_str)
