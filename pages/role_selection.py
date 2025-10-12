import flet as ft

class RoleSelectionPage:
    def __init__(self, page: ft.Page, db_manager):
        self.page = page
        self.db_manager = db_manager
    
    def select_admin_role(self, e):
        """Navigate to admin login"""
        self.page.go("/admin-login")
    
    def select_student_role(self, e):
        """Navigate to student login"""
        self.page.go("/student-login")
    
    def get_view(self):
        """Return the role selection view"""
        
        # Get page dimensions
        page_width = self.page.window.width or 1350
        page_height = self.page.window.height or 900
        
        # Calculate positions for centering elements on the right side
        left_bg_width = 450
        right_area_width = page_width - left_bg_width
        right_area_start_x = left_bg_width
        right_area_center_x = right_area_start_x + (right_area_width / 2)
        
        return ft.View(
            "/",
            [
                ft.Stack(
                    controls=[
                        # Background with white to light pink/orange gradient
                        ft.Container(
                            width=page_width,
                            height=page_height,
                            gradient=ft.LinearGradient(
                                colors=["#FFFFFF", "#FFE5E1", "#FFD4CC"],
                                begin=ft.alignment.top_center,
                                end=ft.alignment.bottom_center
                            )
                        ),
                        
                        # Left curved background with warm gradient
                        ft.Container(
                            width=left_bg_width,
                            height=page_height,
                            bgcolor="#CFA8A1",
                            top=0,
                            left=0,
                            border_radius=ft.border_radius.only(
                                top_right=120,
                                bottom_right=120
                            ),
                            gradient=ft.LinearGradient(
                                colors=["#CFA8A1", "#B56464"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            )
                        ),
                        
                        # Left side text content
                        ft.Container(
                            top=60,
                            left=40,
                            width=300,
                            content=ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Image(
                                            src="uploads/submissions/6_URS Logo.jpg",
                                            width=50,
                                            height=50,
                                            fit=ft.ImageFit.CONTAIN
                                        ),
                                        bgcolor="#FFFFFF",
                                        width=65,
                                        height=65,
                                        border_radius=32.5,
                                        alignment=ft.alignment.center,
                                        shadow=ft.BoxShadow(
                                            spread_radius=0,
                                            blur_radius=10,
                                            color=ft.Colors.BLACK26,
                                            offset=ft.Offset(0, 3)
                                        ),
                                        padding=ft.padding.all(7)
                                    ),
                                    ft.Container(height=20),
                                    ft.Text(
                                        "BUILT FOR\nLEARNING,\nDESIGNED FOR\nSUCCESS.",
                                        size=22,
                                        weight=ft.FontWeight.W_700,
                                        color="#FFFFFF",
                                        text_align=ft.TextAlign.LEFT,
                                        font_family="Poppins",
                                        style=ft.TextStyle(
                                            shadow=ft.BoxShadow(
                                                blur_radius=5,
                                                color=ft.Colors.BLACK26,
                                                offset=ft.Offset(1, 1)
                                            )
                                        )
                                    )
                                ],
                                spacing=0
                            )
                        ),
                        
                        # Geometric shapes on left side
                        # Brown hexagon with gradient
                        ft.Container(
                            top=180,
                            left=120,
                            width=80,
                            height=80,
                            bgcolor="#B56464",
                            border_radius=12,
                            rotate=ft.Rotate(0.3),
                            gradient=ft.LinearGradient(
                                colors=["#B56464", "#9A5555"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=8,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(2, 2)
                            )
                        ),
                        
                        # Warm beige square with gradient
                        ft.Container(
                            top=220,
                            left=200,
                            width=40,
                            height=40,
                            bgcolor="#E2C9C2",
                            border_radius=8,
                            gradient=ft.LinearGradient(
                                colors=["#E2C9C2", "#D9A6A0"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=6,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(2, 2)
                            )
                        ),
                        
                        # Warm brown diamond with gradient
                        ft.Container(
                            top=160,
                            left=250,
                            width=35,
                            height=35,
                            bgcolor="#CFA8A1",
                            border_radius=8,
                            rotate=ft.Rotate(0.785),  # 45 degrees in radians
                            gradient=ft.LinearGradient(
                                colors=["#CFA8A1", "#B56464"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=6,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(2, 2)
                            )
                        ),
                        
                        # Warm cream circle with gradient
                        ft.Container(
                            top=300,
                            left=80,
                            width=30,
                            height=30,
                            bgcolor="#FEFEFE",
                            border_radius=15,
                            gradient=ft.LinearGradient(
                                colors=["#FEFEFE", "#E2C9C2"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=5,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(1, 1)
                            )
                        ),
                        
                        # Dusty rose circle with gradient
                        ft.Container(
                            top=320,
                            left=150,
                            width=25,
                            height=25,
                            bgcolor="#D9A6A0",
                            border_radius=12.5,
                            gradient=ft.LinearGradient(
                                colors=["#D9A6A0", "#CFA8A1"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=5,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(1, 1)
                            )
                        ),
                        
                        # Deep brown circle with gradient
                        ft.Container(
                            top=280,
                            left=200,
                            width=20,
                            height=20,
                            bgcolor="#9A5555",
                            border_radius=10,
                            gradient=ft.LinearGradient(
                                colors=["#9A5555", "#7C4444"],
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=5,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(1, 1)
                            )
                        ),
                        
                        # Brown square outline with enhanced styling
                        ft.Container(
                            top=350,
                            left=250,
                            width=50,
                            height=50,
                            border=ft.border.all(3, "#B56464"),
                            border_radius=8,
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=6,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(2, 2)
                            )
                        ),
                        
                        # Dusty rose square outline with enhanced styling
                        ft.Container(
                            top=380,
                            left=180,
                            width=35,
                            height=35,
                            border=ft.border.all(3, "#D9A6A0"),
                            border_radius=8,
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=6,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(2, 2)
                            )
                        ),
                        
                        # EDUTRACK title - positioned above the role selection box
                        ft.Container(
                            top=page_height * 0.5 - 220,  # Position above the role selection card
                            left=right_area_center_x - 150,  # Center the title (approx title width / 2)
                            content=ft.Text(
                                "EDUTRACK",
                                size=52,
                                weight=ft.FontWeight.W_800,
                                color="#B56464",
                                font_family="Poppins",
                                style=ft.TextStyle(
                                    shadow=ft.BoxShadow(
                                        blur_radius=8,
                                        color=ft.Colors.BLACK26,
                                        offset=ft.Offset(2, 2)
                                    )
                                )
                            )
                        ),
                        
                        # Decorative plus signs around the title
                        ft.Container(
                            top=page_height * 0.15,
                            left=right_area_center_x + 100,
                            content=ft.Text("+", size=32, color="#CFA8A1", weight=ft.FontWeight.W_900, font_family="Poppins")
                        ),
                        ft.Container(
                            top=page_height * 0.20,
                            left=right_area_center_x - 150,
                            content=ft.Text("+", size=28, color="#B56464", weight=ft.FontWeight.W_900, font_family="Poppins")
                        ),
                        ft.Container(
                            top=page_height * 0.18,
                            left=right_area_center_x + 150,
                            content=ft.Text("+", size=38, color="#D9A6A0", weight=ft.FontWeight.W_900, font_family="Poppins")
                        ),
                        ft.Container(
                            top=page_height * 0.22,
                            left=right_area_center_x + 50,
                            content=ft.Text("+", size=24, color="#9A5555", weight=ft.FontWeight.W_900, font_family="Poppins")
                        ),
                        
                        # Role selection card - centered in right area with warm styling
                        ft.Container(
                            top=page_height * 0.5 - 140,  # Center vertically (card height = 280)
                            left=right_area_center_x - 160,  # Center horizontally (card width = 320)
                            width=320,
                            height=280,
                            bgcolor="#FFFFFF",
                            border_radius=24,
                            border=ft.border.all(2, "#E2C9C2"),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=25,
                                color=ft.Colors.BLACK26,
                                offset=ft.Offset(0, 8)
                            ),
                            content=ft.Container(
                                padding=ft.padding.all(30),
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            "PICK YOUR ROLE",
                                            size=20,
                                            weight=ft.FontWeight.W_700,
                                            color="#7C4444",
                                            text_align=ft.TextAlign.CENTER,
                                            font_family="Poppins"
                                        ),
                                        ft.Container(height=40),
                                        
                                        # Student button
                                        ft.Container(
                                            content=ft.ElevatedButton(
                                                text="STUDENT",
                                                style=ft.ButtonStyle(
                                                    bgcolor="#FEFEFE",
                                                    color="#7C4444",
                                                    shape=ft.RoundedRectangleBorder(radius=28),
                                                    side=ft.BorderSide(width=2, color="#E2C9C2"),
                                                    padding=ft.padding.symmetric(horizontal=50, vertical=18),
                                                    text_style=ft.TextStyle(
                                                        size=15,
                                                        weight=ft.FontWeight.W_600,
                                                        font_family="Poppins"
                                                    ),
                                                    shadow_color=ft.Colors.BLACK26,
                                                    elevation=3
                                                ),
                                                on_click=self.select_student_role,
                                                width=250,
                                                height=55
                                            ),
                                            alignment=ft.alignment.center
                                        ),
                                        
                                        ft.Container(height=20),
                                        
                                        # Admin button
                                        ft.Container(
                                            content=ft.ElevatedButton(
                                                text="ADMIN",
                                                style=ft.ButtonStyle(
                                                    bgcolor="#CFA8A1",
                                                    color="#FFFFFF",
                                                    shape=ft.RoundedRectangleBorder(radius=28),
                                                    padding=ft.padding.symmetric(horizontal=50, vertical=18),
                                                    text_style=ft.TextStyle(
                                                        size=15,
                                                        weight=ft.FontWeight.W_600,
                                                        font_family="Poppins"
                                                    ),
                                                    shadow_color=ft.Colors.BLACK26,
                                                    elevation=5
                                                ),
                                                on_click=self.select_admin_role,
                                                width=250,
                                                height=55
                                            ),
                                            alignment=ft.alignment.center
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=0
                                )
                            )
                        )
                    ],
                    expand=True
                )
            ],
            padding=0,
            bgcolor="#FEFEFE"
        )
