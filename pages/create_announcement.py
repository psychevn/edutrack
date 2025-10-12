import flet as ft
from database.database_manager import DatabaseManager


class CreateAnnouncementDialog:
    def __init__(self, page: ft.Page, user_data: dict, refresh_callback=None):
        """
        Initialize the Create Announcement Dialog
        
        Args:
            page: Flet page object
            user_data: Dictionary containing user information (id, username, etc.)
            refresh_callback: Function to call after successful announcement creation
        """
        self.page = page
        self.user_data = user_data
        self.refresh_callback = refresh_callback
        self.db_manager = DatabaseManager()
        
        # Initialize form fields
        self.title_field = None
        self.content_field = None
        self.section_checkboxes = []
        self.all_sections_checkbox = None
        self.bottom_sheet = None
        
    def show_snack_bar(self, message: str, color: str = ft.Colors.GREEN):
        """Show a snack bar with the given message"""
        snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000
        )
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()
        
    def toggle_all_sections(self, e, section_checkboxes):
        """Toggle all section checkboxes when 'All Students' is selected"""
        if e.control.value:  # If "All Students" is checked
            # Uncheck all individual sections
            for checkbox in section_checkboxes:
                checkbox.value = False
                checkbox.update()
        self.page.update()
    
    def create_form_fields(self):
        """Create and return the form fields for announcement creation"""
        # Title field
        self.title_field = ft.TextField(
            label="Announcement Title",
            border_radius=10,
            prefix_icon=ft.Icons.TITLE,
            hint_text="Enter a clear, descriptive title",
            max_length=100
        )
        
        # Content field
        self.content_field = ft.TextField(
            label="Announcement Content",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=10,
            prefix_icon=ft.Icons.MESSAGE,
            hint_text="Write your announcement content here...",
            max_length=1000
        )
        
        # Section selection
        self.section_checkboxes = []
        sections = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B"]
        
        self.all_sections_checkbox = ft.Checkbox(
            label="All Students",
            value=True,  # Default to all students
            on_change=lambda e: self.toggle_all_sections(e, self.section_checkboxes)
        )
        
        for section in sections:
            checkbox = ft.Checkbox(
                label=f"Section {section}",
                value=False
            )
            self.section_checkboxes.append(checkbox)
        
        return {
            'title_field': self.title_field,
            'content_field': self.content_field,
            'all_sections_checkbox': self.all_sections_checkbox,
            'section_checkboxes': self.section_checkboxes
        }
    
    def validate_form(self):
        """Validate the form fields"""
        if not self.title_field.value or not self.title_field.value.strip():
            self.show_snack_bar("Please enter an announcement title", ft.Colors.ORANGE)
            return False
            
        if not self.content_field.value or not self.content_field.value.strip():
            self.show_snack_bar("Please enter announcement content", ft.Colors.ORANGE)
            return False
            
        # Check if at least one target is selected
        if not self.all_sections_checkbox.value:
            selected_sections = [cb for cb in self.section_checkboxes if cb.value]
            if not selected_sections:
                self.show_snack_bar("Please select at least one section or choose 'All Students'", ft.Colors.ORANGE)
                return False
                
        return True
    
    def get_target_sections(self):
        """Get the selected target sections"""
        if self.all_sections_checkbox.value:
            return None  # None means all students
        else:
            selected_sections = []
            for checkbox in self.section_checkboxes:
                if checkbox.value:
                    section_name = checkbox.label.replace("Section ", "")
                    selected_sections.append(section_name)
            return selected_sections if selected_sections else None
    
    def create_announcement(self, e):
        """Handle the create announcement button click"""
        try:
            print("🚀 CREATE ANNOUNCEMENT BUTTON CLICKED!")
            print(f"🚀 Event received: {e}")
            
            # Validate form
            if not self.validate_form():
                return
            
            # Get form data
            title = self.title_field.value.strip()
            content = self.content_field.value.strip()
            target_sections = self.get_target_sections()
            user_id = self.user_data.get('id')
            
            print(f"📝 Title: '{title}'")
            print(f"📝 Content: '{content}'")
            print(f"👤 User ID: {user_id}")
            print(f"🎯 Target sections: {target_sections}")
            
            # Create announcement in database
            print("💾 Creating announcement in database...")
            announcement_id = self.db_manager.create_announcement(
                title=title,
                content=content,
                created_by=user_id,
                target_sections=str(target_sections) if target_sections else None
            )
            
            print(f"💾 Database returned announcement ID: {announcement_id}")
            
            if announcement_id:
                # Close the bottom sheet
                self.bottom_sheet.open = False
                self.page.update()
                
                # Clear form fields
                self.clear_form()
                
                # Show success message
                target_text = f"sections {', '.join(target_sections)}" if target_sections else "all students"
                self.show_snack_bar(f"✅ Announcement created successfully for {target_text}!", ft.Colors.GREEN)
                print(f"✅ SUCCESS: Announcement created successfully!")
                print(f"🎉 Announcement #{announcement_id} is now live for {target_text}!")
                
                # Refresh the announcements list if callback provided
                if self.refresh_callback:
                    self.refresh_callback()
                    
            else:
                self.show_snack_bar("❌ Failed to create announcement. Please try again.", ft.Colors.RED)
                print("❌ FAILED: Database returned None/False")
                
        except Exception as ex:
            error_msg = f"Error creating announcement: {ex}"
            print(f"❌ EXCEPTION: {error_msg}")
            import traceback
            traceback.print_exc()
            self.show_snack_bar(error_msg, ft.Colors.RED)
    
    def clear_form(self):
        """Clear all form fields"""
        if self.title_field:
            self.title_field.value = ""
        if self.content_field:
            self.content_field.value = ""
        if self.all_sections_checkbox:
            self.all_sections_checkbox.value = True
        for checkbox in self.section_checkboxes:
            checkbox.value = False
    
    def close_dialog(self, e):
        """Close the create announcement dialog"""
        print("Closing create announcement dialog")
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.open = False
        elif hasattr(self, 'bottom_sheet') and self.bottom_sheet:
            self.bottom_sheet.open = False
        self.page.update()
        print("Create announcement dialog closed")
    
    def show_create_dialog(self):
        """Show the create announcement dialog"""
        print("✅ Create announcement clicked - Opening dialog")
        
        # Create form fields
        fields = self.create_form_fields()
        
        # Create the dialog
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CAMPAIGN, color="#D4817A", size=24),
                ft.Text("Create New Announcement", size=20, weight=ft.FontWeight.BOLD, color="#D4817A")
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    # Form fields
                    self.title_field,
                    ft.Container(height=10),
                    self.content_field,
                    ft.Container(height=15),
                    
                    # Target audience section
                    ft.Text("Target Audience:", size=14, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    self.all_sections_checkbox,
                    ft.Container(height=5),
                    ft.Text("Or select specific sections:", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=5),
                    
                    # Section checkboxes in rows
                    ft.Column([
                        ft.Row(self.section_checkboxes[:4], spacing=10),
                        ft.Row(self.section_checkboxes[4:], spacing=10)
                    ], spacing=5),
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=400,
                padding=ft.padding.all(20)
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self.close_dialog,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_600)
                ),
                ft.ElevatedButton(
                    "Create Announcement",
                    icon=ft.Icons.SEND,
                    on_click=self.create_announcement,
                    style=ft.ButtonStyle(
                        bgcolor="#D4817A",
                        color=ft.Colors.WHITE,
                        elevation=2
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        # Show the dialog
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()
        print("✅ Create dialog should be visible now")


# Utility function to create and show the dialog
def show_create_announcement_dialog(page: ft.Page, user_data: dict, refresh_callback=None):
    """
    Utility function to quickly show the create announcement dialog
    
    Args:
        page: Flet page object
        user_data: Dictionary containing user information
        refresh_callback: Function to call after successful creation
    """
    dialog = CreateAnnouncementDialog(page, user_data, refresh_callback)
    dialog.show_create_dialog()
    return dialog
