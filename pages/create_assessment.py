import flet as ft
import json
from datetime import datetime, timedelta
from database.database_manager import DatabaseManager

class CreateAssessmentPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager, sections: list[str], assessment_id=None):
        print(f" CreateAssessmentPage constructor called with assessment_id: {assessment_id}")
        self.page = page
        self.db_manager = db_manager
        self.user_data = page.data or {}
        self.sections = sections or ["1A", "2A", "3A", "4A", "1B", "2B", "3B", "4B"]
        self.questions_data = []  # Store question data
        self.selected_section = None
        self.assessment_id = assessment_id  # For editing existing assessments
        self.is_editing = assessment_id is not None
        print(f" Is editing mode: {self.is_editing}")
        
        # Initialize components
        self.init_sidebar()
        self.init_form_controls()
        self.init_section_selection()
        self.init_questions_section()
        self.init_action_buttons()
        
        # Note: Data loading is now done after view creation via load_data_after_view_created()
        # This ensures all UI components are fully ready before populating them
    
    def load_assessment_data(self):
        """Load existing assessment data for editing"""
        try:
            print(f"🚀 LOAD_ASSESSMENT_DATA: STARTING for ID: {self.assessment_id}")
            print(f"🔍 LOAD_ASSESSMENT_DATA: Is editing mode: {self.is_editing}")
            
            # Get assessment details
            assessment = self.db_manager.get_assessment_by_id(self.assessment_id)
            if not assessment:
                print(f"❌ Assessment with ID {self.assessment_id} not found in database")
                return
            
            print(f" Found assessment in database: {assessment}")
            print(f" Assessment title: '{assessment.get('title', 'NO TITLE')}'")
            print(f" Assessment description: '{assessment.get('description', 'NO DESCRIPTION')}'")
            print(f" Duration minutes: {assessment.get('duration_minutes', 'NO DURATION')}")
            
            # Load basic assessment info
            title = assessment.get('title', '')
            description = assessment.get('description', '')
            duration_minutes = assessment.get('duration_minutes', 60)
            
            print(f" Setting title field to: '{title}'")
            self.assessment_title.content.controls[1].value = title
            
            print(f" Setting description field to: '{description}'")
            self.assessment_description.content.controls[1].value = description
            
            print(f" Setting duration field to: '{duration_minutes}'")
            self.duration_value.value = str(duration_minutes)
            
            # Set duration unit (default to Minutes)
            if hasattr(self, 'duration_unit'):
                # Determine if it should be hours or minutes
                if duration_minutes >= 60 and duration_minutes % 60 == 0:
                    # If it's a whole number of hours, show in hours
                    self.duration_unit.value = "Hours"
                    self.duration_value.value = str(duration_minutes // 60)
                else:
                    self.duration_unit.value = "Minutes"
                print(f" Setting duration unit to: '{self.duration_unit.value}'")
                try:
                    # Ensure visual dropdown shows the selected value
                    self.duration_unit.update()
                except Exception as e:
                    print(f"Error updating duration unit dropdown: {e}")
            
            # Verify the fields were set and force UI update for basic fields
            print(f" Title field now contains: '{self.assessment_title.content.controls[1].value}'")
            print(f" Description field now contains: '{self.assessment_description.content.controls[1].value}'")
            print(f" Duration field now contains: '{self.duration_value.value}'")
            if hasattr(self, 'duration_unit'):
                print(f" Duration unit now contains: '{self.duration_unit.value}'")
            
            # Force update of basic form fields
            print(f"🔄 Forcing update of basic form fields...")
            self.page.update()
            print(f"✅ Basic form fields updated")
            
            # Load start and end times if they exist
            if hasattr(self, 'start_datetime_field') and assessment.get('start_time'):
                self.start_datetime_field.value = assessment.get('start_time', '')
            if hasattr(self, 'end_datetime_field') and assessment.get('end_time'):
                self.end_datetime_field.value = assessment.get('end_time', '')
            
            # Load questions
            print(f" Loading questions for assessment ID: {self.assessment_id}")
            questions = self.db_manager.get_questions(self.assessment_id)
            self.questions_data = []
            
            print(f" Found {len(questions)} questions in database")
            if questions:
                for i, q in enumerate(questions):
                    print(f"  Question {i+1}: {q.get('question_text', 'NO TEXT')[:50]}...")
            else:
                print("  No questions found for this assessment")
            
            for question in questions:
                # Map database question types to UI question types
                db_type = question.get('question_type', 'short_answer')
                if db_type in ['mcq', 'multiple_choice']:
                    ui_type = 'mcq'
                else:
                    ui_type = 'short_answer'
                
                question_data = {
                    'question_text': question.get('question_text', ''),
                    'question_type': ui_type,
                    'score': str(question.get('points', 1)),
                    'correct_answer': question.get('correct_answer', ''),
                    'options': []
                }
                
                # Handle options for MCQ questions
                if question.get('options'):
                    try:
                        if isinstance(question['options'], str):
                            # Parse JSON string to get the list
                            options = json.loads(question['options'])
                            # Ensure we have a flat list of strings
                            if isinstance(options, list):
                                # Clean each option to remove extra quotes/brackets
                                clean_options = []
                                for opt in options:
                                    if isinstance(opt, str):
                                        # Remove any extra quotes or brackets
                                        clean_opt = opt.strip().strip('"').strip("'").strip('[]')
                                        clean_options.append(clean_opt)
                                    else:
                                        clean_options.append(str(opt))
                                question_data['options'] = clean_options
                            else:
                                question_data['options'] = [str(options)]
                        elif isinstance(question['options'], list):
                            # Already a list, just clean each option
                            clean_options = []
                            for opt in question['options']:
                                if isinstance(opt, str):
                                    clean_opt = opt.strip().strip('"').strip("'").strip('[]')
                                    clean_options.append(clean_opt)
                                else:
                                    clean_options.append(str(opt))
                            question_data['options'] = clean_options
                        else:
                            question_data['options'] = [str(question['options'])]
                        
                        print(f"Loaded options for question: {question_data['options']}")
                    except Exception as opt_error:
                        print(f"Error parsing options: {opt_error}")
                        question_data['options'] = []
                
                self.questions_data.append(question_data)
            
            # Refresh the questions display
            print(f" About to refresh questions display with {len(self.questions_data)} questions")
            self.refresh_questions_display()
            
            # Load section assignments if published
            if assessment.get('status') == 'published':
                try:
                    post_sections = self.db_manager.get_post_sections(self.assessment_id)
                    if post_sections:
                        self.selected_sections = post_sections
                        # Update section selection UI
                        for section in self.sections:
                            if hasattr(self, f'section_{section}'):
                                checkbox = getattr(self, f'section_{section}')
                                checkbox.value = section in post_sections
                        print(f"Loaded sections: {post_sections}")
                        self.refresh_section_display()
                    else:
                        print("No sections found for this assessment")
                except Exception as section_error:
                    print(f"Error loading sections: {section_error}")
            
            print(f"Successfully loaded assessment: {assessment.get('title')} with {len(self.questions_data)} questions")
            
            # Final verification - check if data is actually in the UI fields
            print(f"🔍 FINAL_CHECK: Verifying UI field values...")
            try:
                title_in_ui = self.assessment_title.content.controls[1].value
                desc_in_ui = self.assessment_description.content.controls[1].value
                duration_in_ui = self.duration_value.value
                print(f"🔍 UI Title: '{title_in_ui}'")
                print(f"🔍 UI Description: '{desc_in_ui}'")
                print(f"🔍 UI Duration: '{duration_in_ui}'")
                
                if title_in_ui and desc_in_ui and duration_in_ui:
                    print(f"✅ FINAL_CHECK: All basic fields have data!")
                else:
                    print(f"❌ FINAL_CHECK: Some fields are empty!")
            except Exception as check_error:
                print(f"❌ FINAL_CHECK: Error checking UI fields: {check_error}")
            
            # Force page update to show loaded data
            print(f"🔄 FINAL: Force page update...")
            self.page.update()
            print(f"✅ FINAL: Page update completed")
            
        except Exception as e:
            print(f"Error loading assessment data: {e}")
            import traceback
            traceback.print_exc()
    
    def load_data_after_view_created(self):
        """Load data after the view has been fully created and added to the page"""
        if self.is_editing:
            print(f"🔄 LOAD_DATA_AFTER_VIEW: Starting for assessment ID: {self.assessment_id}")
            self.load_assessment_data()
            print(f"✅ LOAD_DATA_AFTER_VIEW: Completed for assessment ID: {self.assessment_id}")
        else:
            print(f"❌ LOAD_DATA_AFTER_VIEW: Not in editing mode, skipping data load")
    
    def refresh_questions_display(self):
        """Rebuild the question cards from self.questions_data without changing the UI design."""
        try:
            if not hasattr(self, 'questions_container'):
                print("❌ REFRESH: questions_container is missing")
                return
            print(f"🔄 REFRESH: rebuilding {len(self.questions_data)} question cards")
            # Clear current cards only (questions_data already contains loaded data)
            self.questions_container.controls.clear()
            
            # Create cards for each existing question using enhanced add_question
            for i, q in enumerate(self.questions_data):
                # Normalize loaded data into UI format expected by the card
                loaded_q = {
                    'question_text': q.get('question_text', ''),
                    'question_type': ('Multiple Choices' if str(q.get('question_type', '')).lower() in ['mcq', 'multiple choices', 'multiple_choices'] else 'Answer Type'),
                    'score': str(q.get('score', q.get('points', '') or '')),
                    'options': q.get('options', []) or [],
                    'correct_answer': q.get('correct_answer')
                }
                # Use suppress_append so questions_data isn't mutated/grown
                self.add_question(None, pre_data=loaded_q, index=i, suppress_append=True)
            
            self.page.update()
            print("✅ REFRESH: question cards rebuilt")
        except Exception as e:
            print(f"❌ REFRESH error: {e}")
            import traceback; traceback.print_exc()
    
    
    def refresh_section_display(self):
        """Refresh the section selection display"""
        try:
            # This would update the section selection UI if needed
            # For now, just update the page
            self.page.update()
        except Exception as e:
            print(f"Error refreshing section display: {e}")
    
    def init_sidebar(self):
        """Initialize the left sidebar navigation matching the prototype"""
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
                        ft.Text("Surname,", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Firstname", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Admin", size=12, color=ft.Colors.WHITE70)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    padding=20
                ),
                
                ft.Divider(color="#fafafa", height=20),
                
                # Navigation items
                ft.Container(
                    content=ft.Column([
                        self.create_nav_item(ft.Icons.PERSON, "User", False),
                        self.create_nav_item(ft.Icons.HOME, "Dashboard", False),
                        self.create_nav_item(ft.Icons.ASSIGNMENT, "Assessments", True),  # Active
                        self.create_nav_item(ft.Icons.STAR, "Scores", False)
                    ], spacing=5),
                    padding=ft.padding.symmetric(horizontal=10, vertical=20)
                ),
                
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
                            overlay_color=ft.Colors.WHITE10
                        )
                    ),
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
    
    def create_nav_item(self, icon, text, is_active):
        """Create a navigation item"""
        return ft.Container(
            content=ft.TextButton(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70, size=20),
                    ft.Text(text, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70, size=14,
                           weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL)
                ], alignment=ft.MainAxisAlignment.START),
                on_click=lambda e, nav_text=text: self.navigate_to(nav_text),
                style=ft.ButtonStyle(
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    overlay_color=ft.Colors.WHITE10,
                    shape=ft.RoundedRectangleBorder(radius=0)
                )
            ),
            bgcolor="#bb5862" if is_active else ft.Colors.TRANSPARENT,
            border_radius=0
        )
    
    def navigate_to(self, nav_text):
        """Handle navigation"""
        if nav_text == "Dashboard":
            self.page.go("/admin")
        elif nav_text == "Assessments":
            self.page.go("/admin")  # Go back to admin dashboard
    
    def logout(self, e):
        """Handle logout"""
        self.page.data = None
        self.page.go("/")
    
    def go_back(self, e):
        """Handle back button click"""
        # This method will be overridden by the admin dashboard when using inline view
        # For standalone use, navigate back to admin dashboard
        self.page.go("/admin")
    
    def init_form_controls(self):
        """Initialize the main form controls with proper icons"""
        # Assessment Title with T icon
        self.assessment_title = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("T", size=18, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    width=40,
                    alignment=ft.alignment.center
                ),
                ft.TextField(
                    hint_text="Assessment Title",
                    border=ft.InputBorder.NONE,
                    expand=True,
                    text_style=ft.TextStyle(size=14)
                )
            ]),
            bgcolor="#f5f5f5",
            border_radius=15,
            border=ft.border.all(1, "#e0e0e0"),
            padding=ft.padding.symmetric(horizontal=10, vertical=5)
        )
        
        # Assessment Description with description icon
        self.assessment_description = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.DESCRIPTION, size=20, color="#D4817A"),
                    width=40,
                    alignment=ft.alignment.center
                ),
                ft.TextField(
                    hint_text="Assessment Description",
                    border=ft.InputBorder.NONE,
                    expand=True,
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    text_style=ft.TextStyle(size=14)
                )
            ]),
            bgcolor="#f5f5f5",
            border_radius=15,
            border=ft.border.all(1, "#e0e0e0"),
            padding=ft.padding.symmetric(horizontal=10, vertical=5)
        )
        
        # Duration with hourglass icon and unit selector
        self.duration_value = ft.TextField(
            hint_text="Duration",
            border=ft.InputBorder.NONE,
            expand=True,
            input_filter=ft.NumbersOnlyInputFilter(),
            text_style=ft.TextStyle(size=14)
        )
        self.duration_unit = ft.Dropdown(
            value="minutes",
            options=[
                # text shown, value stored
                ft.dropdown.Option("Mins", "minutes"),
                ft.dropdown.Option("hr", "hours"),
            ],
            width=100,
            bgcolor="#f5f5f5",
            border_color="#e0e0e0",
            focused_border_color="#D4817A",
            border_radius=10,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
            text_style=ft.TextStyle(size=12)
        )
        self.duration = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.HOURGLASS_EMPTY, size=20, color="#D4817A"),
                    width=40,
                    alignment=ft.alignment.center
                ),
                self.duration_value,
                ft.Container(width=10),
                self.duration_unit,
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor="#f5f5f5",
            border_radius=15,
            border=ft.border.all(1, "#e0e0e0"),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            width=270
        )
        
        # Start Date & Time (single field with pickers)
        self.start_datetime_field = ft.TextField(
            hint_text="Start Date & Time",
            border=ft.InputBorder.NONE,
            expand=True,
            read_only=True,
            text_style=ft.TextStyle(size=14)
        )
        _start_inner = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.ACCESS_TIME, size=20, color="#D4817A"),
                    width=40,
                    alignment=ft.alignment.center
                ),
                self.start_datetime_field,
                ft.IconButton(icon=ft.Icons.EVENT, icon_size=18, icon_color="#D4817A", tooltip="Pick date & time", on_click=self.pick_start_datetime),
            ]),
            bgcolor="#f5f5f5",
            border_radius=15,
            border=ft.border.all(1, "#e0e0e0"),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            width=265,
            ink=True,
            on_click=self.pick_start_datetime,
        )
        self.start_date_container = ft.GestureDetector(content=_start_inner, on_tap=self.pick_start_datetime)
        
        # End Date & Time (single field with pickers)
        self.end_datetime_field = ft.TextField(
            hint_text="End Date & Time",
            border=ft.InputBorder.NONE,
            expand=True,
            read_only=True,
            text_style=ft.TextStyle(size=14)
        )
        _end_inner = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.ACCESS_TIME, size=20, color="#D4817A"),
                    width=40,
                    alignment=ft.alignment.center
                ),
                self.end_datetime_field,
                ft.IconButton(icon=ft.Icons.EVENT, icon_size=18, icon_color="#D4817A", tooltip="Pick date & time", on_click=self.pick_end_datetime),
            ]),
            bgcolor="#f5f5f5",
            border_radius=15,
            border=ft.border.all(1, "#e0e0e0"),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            width=265,
            ink=True,
            on_click=self.pick_end_datetime,
        )
        self.end_date_container = ft.GestureDetector(content=_end_inner, on_tap=self.pick_end_datetime)
        
        # Persistent pickers and state
        self._active_dt_target = None  # 'start' or 'end'
        self._picked_date_str = None
        self.date_picker = ft.DatePicker(
            first_date=datetime.now(),
            last_date=datetime.now() + timedelta(days=365),
            on_change=self._on_date_picked
        )
        self.time_picker = ft.TimePicker(on_change=self._on_time_picked)
        # Ensure pickers are in overlay once
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if self.time_picker not in self.page.overlay:
            self.page.overlay.append(self.time_picker)
        # Force a render so pickers are mounted before first use
        self.page.update()

    def _ensure_pickers(self):
        """Make sure pickers are attached to overlay and ready to open."""
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if self.time_picker not in self.page.overlay:
            self.page.overlay.append(self.time_picker)
        self.page.update()
    
    def init_section_selection(self):
        """Initialize section selection with checkboxes for multiple selection"""
        self.selected_sections = []
        self.section_checkboxes = {}  # Use dict to store by section name
        
        # Debug: Print sections to verify they exist
        print(f"DEBUG: Sections available: {self.sections}")
        
        # Create checkboxes for sections - using explicit text labels
        first_row = []
        for section in ["1A", "2A", "3A", "4A"]:
            checkbox = ft.Checkbox(
                value=False,
                active_color="#D4817A",
                data=section,  # Store section name in data
                on_change=self.handle_section_change
            )
            
            # Create explicit text label
            text_label = ft.Text(
                section,
                size=16,
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD
            )
            
            # Combine checkbox and label in a row
            checkbox_with_label = ft.Row([
                checkbox,
                text_label
            ], spacing=8, alignment=ft.MainAxisAlignment.START)
            
            self.section_checkboxes[section] = checkbox
            first_row.append(checkbox_with_label)
        
        # Second row: 1B, 2B, 3B, 4B
        second_row = []
        for section in ["1B", "2B", "3B", "4B"]:
            checkbox = ft.Checkbox(
                value=False,
                active_color="#D4817A",
                data=section,  # Store section name in data
                on_change=self.handle_section_change
            )
            
            # Create explicit text label
            text_label = ft.Text(
                section,
                size=16,
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD
            )
            
            # Combine checkbox and label in a row
            checkbox_with_label = ft.Row([
                checkbox,
                text_label
            ], spacing=8, alignment=ft.MainAxisAlignment.START)
            
            self.section_checkboxes[section] = checkbox
            second_row.append(checkbox_with_label)
        
        # Create the layout
        self.section_checkbox_group = ft.Column([
            ft.Row(first_row, spacing=40, alignment=ft.MainAxisAlignment.START),
            ft.Container(height=10),
            ft.Row(second_row, spacing=40, alignment=ft.MainAxisAlignment.START)
        ], spacing=10)
    
    def init_questions_section(self):
        """Initialize questions section"""
        self.questions_container = ft.Column([], spacing=15)
        
        self.add_question_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, color="#D4817A", size=20),
                ft.Text("Add Question", color="#D4817A", size=14, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#F5E6E8",
            border_radius=25,
            padding=ft.padding.symmetric(horizontal=25, vertical=12),
            on_click=self.add_question,
            ink=True
        )
    
    def init_action_buttons(self):
        """Initialize Draft and Publish buttons"""
        self.draft_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.EDIT, color="#D4817A", size=18),
                ft.Text("Draft", color="#D4817A", size=14, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#F5E6E8",
            border_radius=25,
            padding=ft.padding.symmetric(horizontal=30, vertical=12),
            on_click=self.save_as_draft,
            ink=True
        )
        
        self.publish_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CLOUD_UPLOAD, color="white", size=18),
                ft.Text("Publish", color="white", size=14, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#D4817A",
            border_radius=25,
            padding=ft.padding.symmetric(horizontal=30, vertical=12),
            on_click=self.publish_assessment,
            ink=True
        )

    def add_question(self, e, pre_data=None, index=None, suppress_append=False):
        """Add a new question card matching the prototype design.
        If pre_data is provided, it will be used to populate the card. When suppress_append=True,
        self.questions_data will not be appended to (used for rendering loaded data)."""
        try:
            # Determine target index (0-based) used throughout the card and callbacks
            if index is not None and isinstance(index, int) and index >= 0:
                zero_based_idx = index
                idx = zero_based_idx + 1  # 1-based label for UI
            else:
                zero_based_idx = len(self.questions_container.controls)
                idx = zero_based_idx + 1

            # Prepare question data (normalize incoming pre_data to UI expectations)
            if pre_data is not None:
                qtype_raw = str(pre_data.get('question_type', 'Multiple Choices'))
                qtype_ui = 'Multiple Choices' if qtype_raw in ['Multiple Choices', 'multiple choices', 'multiple_choices', 'mcq', 'MCQ'] else 'Answer Type'
                # Normalize correct answer to index
                ca = pre_data.get('correct_answer')
                ca_idx = None
                if ca is not None:
                    try:
                        if isinstance(ca, str):
                            if ca.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                                ca_idx = ord(ca.upper()) - ord('A')
                            else:
                                ca_idx = int(ca)
                        else:
                            ca_idx = int(ca)
                    except Exception:
                        ca_idx = None
                question_data = {
                    'question_text': pre_data.get('question_text', ''),
                    'question_type': qtype_ui,
                    'score': str(pre_data.get('score', pre_data.get('points', '') or '')),
                    'options': list(pre_data.get('options', []) or []),
                    'correct_answer': ca_idx
                }
            else:
                # Default blank question
                question_data = {
                    'question_text': '',
                    'question_type': 'Multiple Choices',
                    'score': '',
                    'options': ['', ''],  # Start with 2 empty options
                    'correct_answer': None
                }

            # Persist into questions_data only if requested
            if not suppress_append:
                self.questions_data.append(question_data)
            else:
                # Ensure questions_data has a slot and store normalized data
                while len(self.questions_data) <= zero_based_idx:
                    self.questions_data.append({'question_text': '', 'question_type': 'Multiple Choices', 'score': '', 'options': ['', ''], 'correct_answer': None})
                self.questions_data[zero_based_idx] = question_data

            # Question type dropdown
            question_type_dropdown = ft.Dropdown(
                value=question_data['question_type'],
                options=[
                    ft.dropdown.Option("Multiple Choices", "Multiple Choices"),
                    ft.dropdown.Option("Answer Type", "Answer Type")
                ],
                bgcolor="#cfc6b5",
                border_color="#e0e0e0",
                focused_border_color="#D4817A",
                border_radius=10,
                content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
                text_style=ft.TextStyle(size=12),
                width=150,
                on_change=lambda e: self.on_question_type_change(idx-1, e.control.value)
            )

            # Score field
            score_field = ft.TextField(
                hint_text="Score:",
                input_filter=ft.NumbersOnlyInputFilter(),
                border_radius=10,
                bgcolor="#f5f5f5",
                border_color="#e0e0e0",
                focused_border_color="#D4817A",
                content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
                text_style=ft.TextStyle(size=12),
                width=80,
                on_change=lambda e: self.update_question_data(idx-1, 'score', e.control.value),
                value=question_data.get('score', '')
            )

            # Question text field
            question_text_field = ft.TextField(
                hint_text="Question Text",
                multiline=True,
                min_lines=2,
                max_lines=4,
                border_radius=15,
                bgcolor="#f5f5f5",
                border_color="#e0e0e0",
                focused_border_color="#D4817A",
                content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
                text_style=ft.TextStyle(size=14),
                on_change=lambda e: self.update_question_data(idx-1, 'question_text', e.control.value),
                value=question_data.get('question_text', '')
            )

            # Options container (for multiple choice)
            options_container = ft.Column([], spacing=10)

            # Add Option button
            add_option_button = ft.Container(
                content=ft.Text("Add Option", color="white", size=12, weight=ft.FontWeight.BOLD),
                bgcolor="#D4817A",
                border_radius=15,
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
                on_click=lambda e: self.add_option(idx-1, options_container),
                ink=True
            )

            # Correct answer dropdown (UNDER the Add Option button)
            correct_selector = ft.Dropdown(
                width=120,
                options=[],
                hint_text="Pick letter",
                bgcolor="#f5f5f5",
                border_color="#e0e0e0",
                focused_border_color="#D4817A",
                border_radius=10,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
                text_style=ft.TextStyle(size=12),
                on_change=lambda e, q_idx=idx-1: self._on_correct_selector_change(q_idx, e.control.value)
            )
            correct_input_container = ft.Container(
                content=ft.Row([
                    ft.Text("Correct answer:", size=12, color=ft.Colors.GREY),
                    correct_selector
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
                bgcolor="#f5f5f5",
                border=ft.border.all(1, "#e0e0e0"),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=12, vertical=10)
            )

            # Answer field (for Answer Type questions)
            answer_field = ft.TextField(
                hint_text="Question's Answer",
                border_radius=15,
                bgcolor="#f5f5f5",
                border_color="#e0e0e0",
                focused_border_color="#D4817A",
                content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
                text_style=ft.TextStyle(size=14),
                visible=False,  # Hidden by default
                on_change=lambda e: self.update_question_data(idx-1, 'answer', e.control.value)
            )

            # Delete button
            delete_button = ft.IconButton(
                ft.Icons.DELETE,
                icon_color="#D4817A",
                icon_size=20,
                tooltip="Delete Question",
                on_click=lambda e: self.remove_question(idx-1)
            )

            # Correct answer label (only meaningful for Multiple Choices)
            correct_label = ft.Text("Correct: —", size=12, color="#D4817A", italic=True)

            # Question card
            question_card = ft.Container(
                content=ft.Column([
                    # Header with question number, type, score and delete
                    ft.Row([
                        ft.Text(f"Question {idx}", size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Container(expand=True),
                        ft.Text("Score:", size=12, color="#666"),
                        score_field,
                        question_type_dropdown,
                        correct_label,
                        delete_button
                    ],spacing=10,  alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Container(height=10),

                    # Question text
                    question_text_field,

                    ft.Container(height=10),

                    # Options (for multiple choice)
                    options_container,
                    add_option_button,
                    correct_input_container,

                    # Answer field (for answer type)
                    answer_field

                ], spacing=10),
                bgcolor="white",
                border_radius=20,
                border=ft.border.all(2, "#F5E6E8"),
                padding=ft.padding.all(20),
                margin=ft.margin.symmetric(vertical=10)
            )

            # Store references for later access
            question_card.data = {
                'question_text': question_text_field,
                'question_type': question_type_dropdown,
                'score': score_field,
                'options_container': options_container,
                'add_option_button': add_option_button,
                'answer_field': answer_field,
                'correct_label': correct_label,
                'correct_selector': correct_selector,
                'correct_input_container': correct_input_container,
                'question_index': idx-1
            }

            # Append card first, then render options so we can store refs properly
            self.questions_container.controls.append(question_card)
            # If options are present in question_data, use them, else render defaults
            if question_data.get('options') is not None:
                self.update_options_display(options_container, idx-1)
            else:
                # Ensure options at least empty list
                self.questions_data[idx-1]['options'] = []
                self.update_options_display(options_container, idx-1)
            # Sync correct answer selector
            self.update_correct_selector(idx-1)
            self.page.update()
        except Exception as ex:
            # Surface error to the user
            self._toast_error(f"Failed to add question: {ex}")
            try:
                import traceback; print("Add question error:\n", traceback.format_exc())
            except Exception:
                pass
    
    def update_options_display(self, options_container, question_idx):
        """Render options for a multiple choice question (text fields only). Correct answer is set below using chips."""
        options_container.controls.clear()
        if not (0 <= question_idx < len(self.questions_data)):
            return
        question_data = self.questions_data[question_idx]

        # Build rows of (letter badge, option text)
        rows = []
        option_fields = []
        selected_idx = question_data.get('correct_answer')
        for i, option_text in enumerate(question_data.get('options', [])):
            letter_badge = ft.Container(
                content=ft.Text(chr(65 + i), size=12, weight=ft.FontWeight.BOLD, color="#D4817A"),
                bgcolor="#F5E6E8",
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=8, vertical=4)
            )
            is_selected = (selected_idx == i)
            option_field = ft.TextField(
                value=option_text,
                hint_text=f"Option {i+1}",
                border_radius=15,
                bgcolor=("#ECF9F0" if is_selected else "#f5f5f5"),
                border_color=("#4CAF50" if is_selected else "#e0e0e0"),
                focused_border_color=("#4CAF50" if is_selected else "#D4817A"),
                content_padding=ft.padding.symmetric(horizontal=20, vertical=10),
                text_style=ft.TextStyle(size=14),
                expand=True,
                on_change=lambda e, q_idx=question_idx, opt_idx=i: self.update_option_text(q_idx, opt_idx, e.control.value)
            )
            option_fields.append(option_field)
            rows.append(ft.Row([letter_badge, option_field], spacing=10, alignment=ft.MainAxisAlignment.START))

        options_container.controls.append(ft.Column(rows, spacing=10))
        # Update correct answer selector in case count changed and enforce visibility
        self.update_correct_selector(question_idx)
        # Store option field references for styling updates
        if 0 <= question_idx < len(self.questions_container.controls):
            card = self.questions_container.controls[question_idx]
            card.data['option_fields'] = option_fields
        # Ensure current selection styling is applied
        self.update_correct_option_styling(question_idx)
        self.page.update()

    def add_option(self, question_idx, options_container):
        """Add a new empty option and re-render options."""
        if not (0 <= question_idx < len(self.questions_data)):
            return
        self.questions_data[question_idx].setdefault('options', []).append('')
        self.update_options_display(options_container, question_idx)
        self.page.update()

    def update_correct_selector(self, question_idx):
        """Sync the dropdown selector with current options and selected correct answer."""
        if not (0 <= question_idx < len(self.questions_container.controls)):
            return
        card = self.questions_container.controls[question_idx]
        selector = card.data.get('correct_selector')
        if not selector:
            return
        option_count = len(self.questions_data[question_idx].get('options', []))
        ca = self.questions_data[question_idx].get('correct_answer')
        # Build options A, B, C ...
        selector.options = [ft.dropdown.Option(str(i), chr(65 + i)) for i in range(option_count)]
        
        # Handle correct answer - convert to int if it's a string
        ca_int = None
        if ca is not None:
            try:
                if isinstance(ca, str):
                    # If it's a letter like 'A', 'B', convert to index
                    if ca.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                        ca_int = ord(ca.upper()) - ord('A')
                    else:
                        ca_int = int(ca)
                else:
                    ca_int = int(ca)
            except (ValueError, TypeError):
                ca_int = None
        
        selector.value = (str(ca_int) if ca_int is not None and 0 <= ca_int < option_count else None)
        selector.disabled = (option_count == 0)
        # Toggle container visibility: only show when there are at least 2 options
        cic = card.data.get('correct_input_container')
        if cic is not None:
            cic.visible = (option_count >= 2)
        self.page.update()

    def change_question_type(self, question_idx, question_type):
        """Change the question type and update the UI accordingly"""
        try:
            if not (0 <= question_idx < len(self.questions_data)):
                return
            
            # Update the data
            self.questions_data[question_idx]['question_type'] = question_type
            
            # Get the question card
            if question_idx < len(self.questions_container.controls):
                card = self.questions_container.controls[question_idx]
                
                # Update the dropdown value
                type_row = card.content.controls[2]  # The Row with type and score
                if hasattr(type_row, 'controls') and len(type_row.controls) > 0:
                    type_dropdown = type_row.controls[0]
                    if hasattr(type_dropdown, 'value'):
                        type_dropdown.value = question_type
                
                # Update options display based on type
                if question_type == 'mcq':
                    # Show options for MCQ
                    self.update_options_display(card.content.controls[3], question_idx)
                else:
                    # Hide options for short answer
                    options_container = card.content.controls[3]
                    if hasattr(options_container, 'controls'):
                        options_container.controls.clear()
                        options_container.visible = False
            
            self.page.update()
            
        except Exception as e:
            print(f"Error changing question type: {e}")

    def _on_correct_selector_change(self, question_idx, value):
        """Handle selecting correct answer from dropdown (value is index as string)."""
        if not (0 <= question_idx < len(self.questions_data)):
            return
        idx = None
        try:
            idx = int(value) if value is not None and value != "" else None
        except Exception:
            idx = None
        self.update_question_data(question_idx, 'correct_answer', idx)
        self.update_correct_option_styling(question_idx)
        self.page.update()

    def update_correct_option_styling(self, question_idx):
        """Apply green highlight to the selected correct option field."""
        if not (0 <= question_idx < len(self.questions_container.controls)):
            return
        card = self.questions_container.controls[question_idx]
        option_fields = card.data.get('option_fields') or []
        selected_idx = self.questions_data[question_idx].get('correct_answer')
        for i, tf in enumerate(option_fields):
            is_selected = (selected_idx == i)
            tf.border_color = "#4CAF50" if is_selected else "#e0e0e0"
            tf.focused_border_color = "#4CAF50" if is_selected else "#D4817A"
            tf.bgcolor = "#ECF9F0" if is_selected else "#f5f5f5"
        self.page.update()
    
    def update_option_text(self, question_idx, option_idx, text):
        """Update option text with validation"""
        if question_idx < len(self.questions_data):
            if option_idx < len(self.questions_data[question_idx]['options']):
                # Clean the text to prevent issues with commas and special characters
                clean_text = text.strip() if text else ''
                self.questions_data[question_idx]['options'][option_idx] = clean_text
                print(f"Updated option {option_idx + 1} for question {question_idx + 1}: '{clean_text}'")
    
    def update_question_data(self, question_idx, field, value):
        """Update question data"""
        if question_idx < len(self.questions_data):
            self.questions_data[question_idx][field] = value
            # Keep the correct label in sync for MCQ
            if field in ('correct_answer', 'question_type'):
                self.update_correct_label(question_idx)
                if field == 'correct_answer':
                    self.update_correct_option_styling(question_idx)

    def update_correct_label(self, question_idx):
        """Update the 'Correct: X' label in question header for the given question."""
        if not (0 <= question_idx < len(self.questions_container.controls)):
            return
        card = self.questions_container.controls[question_idx]
        label = card.data.get('correct_label')
        if not label:
            return
        qd = self.questions_data[question_idx]
        # Show only for Multiple Choices
        label.visible = (qd.get('question_type') == 'Multiple Choices')
        ca = qd.get('correct_answer')
        if ca is None:
            label.value = "Correct: —"
        else:
            try:
                label.value = f"Correct: {chr(65 + int(ca))}"
            except Exception:
                label.value = "Correct: —"
        self.page.update()
    
    def on_question_type_change(self, question_idx, question_type):
        """Handle question type change"""
        self.update_question_data(question_idx, 'question_type', question_type)
        
        # Find the question card and update visibility
        if question_idx < len(self.questions_container.controls):
            card = self.questions_container.controls[question_idx]
            options_container = card.data['options_container']
            add_option_button = card.data['add_option_button']
            answer_field = card.data['answer_field']
            correct_label = card.data.get('correct_label')
            correct_input_container = card.data.get('correct_input_container')
            
            if question_type == "Multiple Choices":
                options_container.visible = True
                add_option_button.visible = True
                answer_field.visible = False
                if correct_label:
                    correct_label.visible = True
                # Ensure selector reflects current options and enforce visibility by option count
                self.update_correct_selector(question_idx)
            else:  # Answer Type
                options_container.visible = False
                add_option_button.visible = False
                answer_field.visible = True
                if correct_label:
                    correct_label.visible = False
                if correct_input_container:
                    correct_input_container.visible = False
            
            self.page.update()
    
    def remove_question(self, idx: int):
        """Remove a question"""
        if 0 <= idx < len(self.questions_container.controls):
            self.questions_container.controls.pop(idx)
            self.questions_data.pop(idx)
            
            # Re-number questions and update data references
            for i, control in enumerate(self.questions_container.controls):
                # Update question number in header
                header_row = control.content.controls[0]
                header_row.controls[0].value = f"Question {i + 1}"
                # Update data reference
                control.data['question_index'] = i
            
            self.page.update()

    def handle_section_change(self, e):
        """Handle section checkbox change using the data attribute"""
        section = e.control.data
        print(f"DEBUG: Section {section} changed to {e.control.value}")
        if e.control.value:
            if section not in self.selected_sections:
                self.selected_sections.append(section)
        else:
            if section in self.selected_sections:
                self.selected_sections.remove(section)
        print(f"DEBUG: Selected sections: {self.selected_sections}")
    
    def on_section_change(self, e, section):
        """Handle section selection change (legacy method for compatibility)"""
        if e.control.value:
            if section not in self.selected_sections:
                self.selected_sections.append(section)
        else:
            if section in self.selected_sections:
                self.selected_sections.remove(section)
    
    def pick_start_datetime(self, e):
        """Trigger persistent date picker for start field"""
        self._active_dt_target = 'start'
        self._picked_date_str = None
        # Ensure pickers are mounted and try both opening methods for compatibility
        self._ensure_pickers()
        try:
            # Legacy dialog-style open
            self.date_picker.open = True
        except Exception:
            pass
        self.page.update()
        # New API method
        try:
            self.date_picker.pick_date()
        except Exception:
            pass
    
    def pick_end_datetime(self, e):
        """Trigger persistent date picker for end field"""
        self._active_dt_target = 'end'
        self._picked_date_str = None
        # Ensure pickers are mounted and try both opening methods for compatibility
        self._ensure_pickers()
        try:
            # Legacy dialog-style open
            self.date_picker.open = True
        except Exception:
            pass
        self.page.update()
        # New API method
        try:
            self.date_picker.pick_date()
        except Exception:
            pass

    def _format_time_value(self, value):
        """Format TimePicker value to HH:MM handling different value types."""
        try:
            # If tuple like (hour, minute)
            if isinstance(value, tuple) and len(value) >= 2:
                h, m = int(value[0]), int(value[1])
                return f"{h:02d}:{m:02d}"
            # If datetime.time object
            import datetime as _dt
            if isinstance(value, _dt.time):
                return f"{value.hour:02d}:{value.minute:02d}"
            # If string like 'HH:MM' or 'HH:MM:SS'
            if isinstance(value, str):
                parts = value.split(":")
                if len(parts) >= 2:
                    h, m = int(parts[0]), int(parts[1])
                    return f"{h:02d}:{m:02d}"
        except Exception:
            return None

    def _on_date_picked(self, ev):
        """Store picked date then open time picker"""
        if not ev.control.value:
            return
        self._picked_date_str = ev.control.value.strftime("%Y-%m-%d")
        # Ensure time picker present and open using both methods
        self._ensure_pickers()
        try:
            self.time_picker.open = True
        except Exception:
            pass
        self.page.update()
        try:
            self.time_picker.pick_time()
        except Exception:
            pass

    def _on_time_picked(self, tv):
        """Combine stored date and picked time into the active field"""
        if tv.control.value is None or not self._picked_date_str or not self._active_dt_target:
            return
        formatted_time = self._format_time_value(tv.control.value)
        if not formatted_time:
            return
        combined = f"{self._picked_date_str} {formatted_time}"
        if self._active_dt_target == 'start':
            self.start_datetime_field.value = combined
        else:
            self.end_datetime_field.value = combined
        # Reset temp state
        self._active_dt_target = None
        self._picked_date_str = None
        self.page.update()
        return None
    
    def save_as_draft(self, e):
        """Save assessment as draft"""
        self._save_assessment(status='draft')
    
    def publish_assessment(self, e):
        """Publish assessment"""
        self._save_assessment(status='published')
    
    def _save_assessment(self, status='draft'):
        """Save assessment with given status"""
        # Basic validation for all assessments
        if not self.assessment_title.content.controls[1].value:
            self._toast_error("Please enter an assessment title")
            return
        
        # Stricter validation only for published assessments
        if status == 'published':
            if not self.assessment_description.content.controls[1].value:
                self._toast_error("Please enter an assessment description")
                return
                
            if not (self.duration_value.value and self.duration_value.value.strip()):
                self._toast_error("Please enter duration")
                return
            # Start/End required when publishing
            if not (self.start_datetime_field.value and self.start_datetime_field.value.strip()):
                self._toast_error("Please select Start Date & Time")
                return
            if not (self.end_datetime_field.value and self.end_datetime_field.value.strip()):
                self._toast_error("Please select End Date & Time")
                return
            # Validate format and ordering
            try:
                start_dt_check = datetime.strptime(self.start_datetime_field.value.strip(), '%Y-%m-%d %H:%M')
                end_dt_check = datetime.strptime(self.end_datetime_field.value.strip(), '%Y-%m-%d %H:%M')
                if start_dt_check >= end_dt_check:
                    self._toast_error("Start Date & Time must be before End Date & Time")
                    return
            except Exception:
                self._toast_error("Invalid date & time format. Please re-pick Start and End.")
                return
                
            if not self.questions_data:
                self._toast_error("Please add at least one question before publishing")
                return
                
            if not self.selected_sections:
                self._toast_error("Please select at least one section to publish to")
                return
        
        # Validate questions for publishing
        if status == 'published':
            for i, question_data in enumerate(self.questions_data):
                if not question_data.get('question_text', '').strip():
                    self._toast_error(f"Question {i+1} text cannot be empty")
                    return
                
                if question_data['question_type'] == 'Multiple Choices':
                    if not question_data.get('options') or len(question_data['options']) < 2:
                        self._toast_error(f"Question {i+1} must have at least 2 options")
                        return
                    if question_data.get('correct_answer') is None:
                        self._toast_error(f"Question {i+1} must have a correct answer selected")
                        return
                # For Answer Type questions, we allow blank answers (they can be anything)
        
        conn = None
        try:
            # Get a single connection for all operations to prevent database locking
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Use combined date-time fields with sensible defaults
            start_datetime = self.start_datetime_field.value or datetime.now().strftime('%Y-%m-%d %H:%M')
            end_datetime = self.end_datetime_field.value or datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Handle missing fields for draft assessments
            description = self.assessment_description.content.controls[1].value or "Draft assessment - no description yet"
            duration_val = self.duration_value.value
            unit = self.duration_unit.value or "Minutes"
            duration_minutes = int(duration_val) if duration_val else 60
            if unit == "Hours":
                duration_minutes *= 60

            if self.is_editing:
                # Update existing assessment
                cursor.execute('''
                    UPDATE assessments 
                    SET title = ?, description = ?, start_time = ?, end_time = ?, duration_minutes = ?, status = ?
                    WHERE id = ?
                ''', (
                    self.assessment_title.content.controls[1].value,
                    description,
                    start_datetime,
                    end_datetime,
                    duration_minutes,
                    status,
                    self.assessment_id
                ))
                
                # Delete existing questions for this assessment
                cursor.execute('DELETE FROM questions WHERE assessment_id = ?', (self.assessment_id,))
                
                assessment_id = self.assessment_id
            else:
                # Create new assessment
                cursor.execute('''
                    INSERT INTO assessments (title, description, created_by, start_time, end_time, duration_minutes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.assessment_title.content.controls[1].value,
                    description,
                    self.user_data.get('id'),
                    start_datetime,
                    end_datetime,
                    duration_minutes,
                    status
                ))
                
                assessment_id = cursor.lastrowid
            
            # Save questions using the same connection
            for i, question_data in enumerate(self.questions_data):
                if question_data['question_type'] == 'Multiple Choices':
                    # Clean and convert options list to JSON string
                    if question_data.get('options'):
                        # Ensure options are clean strings without extra quotes/brackets
                        clean_options = []
                        for opt in question_data['options']:
                            if isinstance(opt, str) and opt.strip():
                                # Remove any extra quotes or brackets and clean whitespace
                                clean_opt = opt.strip().strip('"').strip("'").strip('[]').strip()
                                if clean_opt:  # Only add non-empty options
                                    clean_options.append(clean_opt)
                        options_text = json.dumps(clean_options) if clean_options else None
                        print(f"Saving clean options for question {i+1}: {clean_options}")
                    else:
                        options_text = None
                    
                    ca_idx = question_data.get('correct_answer')
                    correct_answer = (chr(65 + int(ca_idx)) if ca_idx is not None else None)  # Convert to A, B, C, D; allow None for drafts
                    question_type_db = 'mcq'
                else:
                    options_text = None
                    correct_answer = question_data.get('answer', '') or ''  # Allow empty answers for Answer Type
                    question_type_db = 'short_answer'
                
                cursor.execute('''
                    INSERT INTO questions (assessment_id, question_text, question_type, points, correct_answer, options, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    assessment_id,
                    question_data['question_text'],
                    question_type_db,
                    int(question_data['score']) if question_data.get('score') else 1,
                    correct_answer,
                    options_text,
                    i
                ))
            
            # If publishing, create post and assign to sections using the same connection
            if status == 'published' and self.selected_sections:
                cursor.execute('''
                    INSERT INTO posts (title, description, post_type, created_by, assessment_id, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    self.assessment_title.content.controls[1].value,
                    self.assessment_description.content.controls[1].value,
                    "assessment",
                    self.user_data.get('id'),
                    assessment_id,
                    None
                ))
                
                post_id = cursor.lastrowid
                
                # Assign to sections
                for section in self.selected_sections:
                    cursor.execute('''
                        INSERT OR IGNORE INTO post_sections (post_id, section) VALUES (?, ?)
                    ''', (post_id, section))
            
            # Commit all changes at once
            conn.commit()
            
            action = "published" if status == 'published' else "saved as draft"
            self._toast_success(f"Assessment {action} successfully!")
            
            # Debug output
            print(f"Assessment saved: ID={assessment_id}, Status={status}, Title={self.assessment_title.content.controls[1].value}")
            
            # Navigate back to admin dashboard
            self.page.go("/admin")
            
        except Exception as ex:
            if conn:
                conn.rollback()  # Rollback on error
            self._toast_error(f"Error saving assessment: {str(ex)}")
            print(f"Database error details: {ex}")  # For debugging
        finally:
            if conn:
                conn.close()  # Always close the connection

    def _toast_error(self, msg: str):
        sb = ft.SnackBar(content=ft.Text(msg, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400)
        self.page.overlay.append(sb)
        sb.open = True
        self.page.update()

    def _toast_success(self, msg: str):
        sb = ft.SnackBar(content=ft.Text(msg, color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN_400)
        self.page.overlay.append(sb)
        sb.open = True
        self.page.update()

    def get_view(self):
        """Return the complete assessment creation view with sidebar"""
        # Main content area
        main_content = ft.Container(
            content=ft.Column([
                # Header with back button
                ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.ASSIGNMENT, size=28, color="#D4817A"),
                            ft.Text("Assessment Creation", size=24, weight=ft.FontWeight.BOLD, color="#D4817A")
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.ARROW_BACK, size=20, color="#D4817A"),
                                ft.Text("Back", size=14, weight=ft.FontWeight.BOLD, color="#D4817A")
                            ], spacing=5),
                            bgcolor="#F5E6E8",
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=15, vertical=8),
                            on_click=self.go_back,
                            ink=True
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.only(bottom=30)
                ),
                
                # Main form in rounded container
                ft.Container(
                    content=ft.Column([
                        # Assessment basic info
                        self.assessment_title,
                        ft.Container(height=15),
                        self.assessment_description,
                        ft.Container(height=20),
                        
                        # Duration and date/time fields in a row
                        ft.Row([
                            self.duration,
                            ft.Container(width=20),
                            self.start_date_container,
                            ft.Container(width=20),
                            self.end_date_container
                        ], alignment=ft.MainAxisAlignment.START),
                        
                        ft.Container(height=30),
                        
                        # Section selection - compact layout
                        ft.Row([
                            ft.Text("Section to Publish", size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
                            ft.Container(width=50),
                            self.section_checkbox_group
                        ], alignment=ft.MainAxisAlignment.START),
                        
                        ft.Container(height=30),
                        
                        # Questions section
                        ft.Text("Questions", size=18, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Container(height=15),
                        
                        # Questions container
                        self.questions_container,
                        
                        # Add question button
                        ft.Container(
                            content=self.add_question_button,
                            alignment=ft.alignment.center,
                            padding=ft.padding.symmetric(vertical=20)
                        ),
                        
                        ft.Container(height=30),
                        
                        # Action buttons
                        ft.Row([
                            ft.Container(expand=True),
                            self.draft_button,
                            ft.Container(width=20),
                            self.publish_button
                        ], alignment=ft.MainAxisAlignment.END)
                        
                    ], spacing=0, scroll=ft.ScrollMode.AUTO),
                    bgcolor="white",
                    border_radius=25,
                    border=ft.border.all(2, "#F5E6E8"),
                    padding=ft.padding.all(30),
                    expand=True,
                    margin=ft.margin.all(20)
                )
            ], spacing=0),
            bgcolor="#f4f1ec",
            expand=True,
            padding=ft.padding.all(20)
        )
        
        return ft.View(
            "/create-assessment",
            [
                ft.Container(
                    content=ft.Row([
                        self.sidebar,
                        main_content
                    ], expand=True, spacing=0),
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )
    
    def get_content_only(self):
        """Return only the main content without sidebar for inline use"""
        return ft.Column([
            # Header with back button
            ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.ASSIGNMENT, size=28, color="#D4817A"),
                        ft.Text("Assessment Creation", size=24, weight=ft.FontWeight.BOLD, color="#D4817A")
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK, size=20, color="#D4817A"),
                            ft.Text("Back", size=14, weight=ft.FontWeight.BOLD, color="#D4817A")
                        ], spacing=5),
                        bgcolor="#F5E6E8",
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        on_click=self.go_back,
                        ink=True
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(bottom=30)
            ),
            
            # Main form in rounded container
            ft.Container(
                content=ft.Column([
                    # Assessment basic info
                    self.assessment_title,
                    ft.Container(height=15),
                    self.assessment_description,
                    ft.Container(height=20),
                    
                    # Duration and date/time fields in a row
                    ft.Row([
                        self.duration,
                        ft.Container(width=20),
                        self.start_date_container,
                        ft.Container(width=20),
                        self.end_date_container
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=6),
                    ft.Text("Click a field to pick date & time.", size=11, color=ft.Colors.GREY, italic=True),
                    
                    ft.Container(height=30),
                    
                    # Section selection - compact layout
                    ft.Row([
                        ft.Text("Section to Publish", size=16, weight=ft.FontWeight.BOLD, color="#D4817A"),
                        ft.Container(width=50),
                        self.section_checkbox_group
                    ], alignment=ft.MainAxisAlignment.START),
                    
                    ft.Container(height=30),
                    
                    # Questions section
                    ft.Text("Questions", size=18, weight=ft.FontWeight.BOLD, color="#D4817A"),
                    ft.Container(height=15),
                    
                    # Questions container
                    self.questions_container,
                    
                    # Add question button
                    ft.Container(
                        content=self.add_question_button,
                        alignment=ft.alignment.center,
                        padding=ft.padding.symmetric(vertical=20)
                    ),
                    
                    ft.Container(height=30),
                    
                    # Action buttons
                    ft.Row([
                        ft.Container(expand=True),
                        self.draft_button,
                        ft.Container(width=20),
                        self.publish_button
                    ], alignment=ft.MainAxisAlignment.END)
                    
                ], spacing=0, scroll=ft.ScrollMode.AUTO),
                bgcolor="white",
                border_radius=25,
                border=ft.border.all(2, "#F5E6E8"),
                padding=ft.padding.all(30),
                expand=True
            )
        ], spacing=0)
