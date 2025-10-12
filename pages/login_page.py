import flet as ft
from database.database_manager import DatabaseManager

class LoginPage:
    def __init__(self, page: ft.Page, db_manager: DatabaseManager):
        self.page = page
        self.db_manager = db_manager
        self.username_field = ft.TextField(
            label="Username",
            prefix_icon=ft.Icons.PERSON,
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
        )
        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            border_color=ft.Colors.BLUE_300,
            focused_border_color=ft.Colors.BLUE_500,
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
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.handle_login
        )
    
    def handle_login(self, e):
        """Handle login button click"""
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        # Authenticate user
        user = self.db_manager.authenticate_user(username, password)
        
        if user:
            # Store user data in page data
            self.page.data = user
            
            # Redirect based on role
            if user['role'] == 'admin':
                self.page.go("/admin")
            else:
                self.page.go("/student")
        else:
            self.show_error("Invalid username or password")
    
    def show_error(self, message: str):
        """Show error message"""
        self.error_message.value = message
        self.error_message.visible = True
        self.page.update()
    
    def get_view(self):
        """Return the login page view"""
        return ft.View(
            "/login",
            [
                ft.Stack(
                    controls=[
                        # Background
                        ft.Container(
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=[ft.Colors.BLUE_50, ft.Colors.BLUE_100, ft.Colors.BLUE_200]
                            ),
                            expand=True
                        ),
                        # Foreground
                        ft.Container(
                            alignment=ft.alignment.center,
                            content=ft.Column(
                        [
                            # Header
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(
                                            ft.Icons.ASSIGNMENT,
                                            size=60,
                                            color=ft.Colors.BLUE_500
                                        ),
                                        ft.Text(
                                            "Assessment Management System",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700,
                                            text_align=ft.TextAlign.CENTER
                                        ),
                                        ft.Text(
                                            "Please sign in to continue",
                                            size=16,
                                            color=ft.Colors.BLUE_600,
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
                                        ft.Container(height=20)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=15,
                                    scroll=ft.ScrollMode.ADAPTIVE
                                ),
                                bgcolor=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(horizontal=40, vertical=30),
                                width=min(400, self.page.window.width * 0.9) if self.page.window.width else 400,
                                border_radius=20,
                                border=ft.border.all(1, ft.Colors.BLUE_200),
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color=ft.Colors.BLUE_100,
                                    offset=ft.Offset(0, 5)
                                )
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    ),
                            padding=ft.padding.all(20)
                        )
                    ],
                    expand=True
                )
            ],
            padding=0,
            bgcolor=ft.Colors.BLUE_50,
            scroll=ft.ScrollMode.ADAPTIVE
        )
