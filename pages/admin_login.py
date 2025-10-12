import flet as ft
from database.database_manager import DatabaseManager

class AdminLoginPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.username_field = ft.TextField(
            label="Admin Username",
            prefix_icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            border_radius=15,
            border_color="#cfc6b5",
            focused_border_color="#bb5862",
            width=350
        )
        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=15,
            border_color="#cfc6b5",
            focused_border_color="#bb5862",
            width=350
        )
        self.error_message = ft.Text(
            "",
            color=ft.Colors.RED_400,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )
        self.login_button = ft.ElevatedButton(
            "Login",
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                bgcolor="#bb5862",
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=25),
                padding=ft.padding.symmetric(horizontal=30, vertical=14)
            ),
            on_click=self.handle_login,
            width=350
        )
        self.register_button = ft.TextButton(
            "Create Admin Account",
            icon=ft.Icons.ADD_CIRCLE,
            style=ft.ButtonStyle(color="#bb5862"),
            on_click=self.go_to_registration
        )
        
        self.forgot_password_button = ft.TextButton(
            "Forgot Password?",
            icon=ft.Icons.LOCK_RESET,
            style=ft.ButtonStyle(color="#bb5862"),
            on_click=self.go_to_password_recovery
            
        )
        self.centered_buttons = ft.Column(
            [
                self.register_button,
                self.forgot_password_button
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )
        
        self.back_button = ft.TextButton(
            "Back to Role Selection",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(color="#bb5862"),
            on_click=self.go_back
        )
    
    def handle_login(self, e):
        """Handle admin login"""
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        # Authenticate user
        user = self.db_manager.authenticate_user(username, password)
        
        if user and user['role'] == 'admin':
            # Store user data in page data
            self.page.data = user
            self.page.go("/admin")
        else:
            self.show_error("Invalid admin credentials")
    
    def go_to_registration(self, e):
        """Go to admin registration"""
        self.page.go("/admin-registration")
    
    def go_to_password_recovery(self, e):
        """Go to password recovery"""
        self.page.go("/password-recovery")
    
    def go_back(self, e):
        """Go back to role selection"""
        self.page.go("/")
    
    def show_error(self, message: str):
        """Show error message"""
        self.error_message.value = message
        self.error_message.visible = True
        self.page.update()
    
    def get_view(self):
        """Return the admin login view"""
        return ft.View(
            "/admin-login",
            [
                ft.Stack(
                    controls=[
                        # Background layer
                        ft.Container(
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=["#efaaaa", "#f4f1ec"]
                            ),
                            width=self.page.window.width,
                            height=self.page.window.height
                        ),
                        # Foreground content
                        ft.Container(
                            content=ft.Column(
                        [
                            # Header
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(
                                            ft.Icons.ADMIN_PANEL_SETTINGS,
                                            size=70,
                                            color="#bb5862"
                                        ),
                                        ft.Text(
                                            "Admin Login",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color="#bb5862",
                                            text_align=ft.TextAlign.CENTER
                                        ),
                                        ft.Text(
                                            "Sign in to manage assessments and view results",
                                            size=16,
                                            color="#6b6b6b",
                                            text_align=ft.TextAlign.CENTER
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10
                                ),
                                padding=ft.padding.only(bottom=40)
                            ),
                            
                            # Login Form
                            ft.Container(
                                content=ft.Column(
                                    [
                                        self.username_field,
                                        self.password_field,
                                        self.error_message,
                                        ft.Container(height=20),
                                        self.login_button,
                                        ft.Container(height=20),
                                        self.centered_buttons,
                                        ft.Container(height=20),
                                        self.back_button
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=15
                                ),
                                bgcolor="#f4f1ec",
                                width=400,
                                padding=40,
                                border_radius=25,
                                border=ft.border.all(2, "#cfc6b5"),
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=18,
                                    color="#eadfd0",
                                    offset=ft.Offset(0, 6)
                                )
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    ),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(40)
                        )
                    ],
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#f4f1ec"
        )
