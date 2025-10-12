import flet as ft

class ThemeConfig:
    """Centralized theme configuration for easy customization"""
    
    # Admin Theme Colors
    ADMIN_PRIMARY = ft.Colors.BLUE_500
    ADMIN_SECONDARY = ft.Colors.BLUE_600
    ADMIN_ACCENT = ft.Colors.BLUE_700
    ADMIN_LIGHT = ft.Colors.BLUE_50
    ADMIN_BORDER = ft.Colors.BLUE_200
    ADMIN_BACKGROUND = [ft.Colors.BLUE_50, ft.Colors.BLUE_100, ft.Colors.BLUE_200]
    
    # Student Theme Colors
    STUDENT_PRIMARY = ft.Colors.GREEN_500
    STUDENT_SECONDARY = ft.Colors.GREEN_600
    STUDENT_ACCENT = ft.Colors.GREEN_700
    STUDENT_LIGHT = ft.Colors.GREEN_50
    STUDENT_BORDER = ft.Colors.GREEN_200
    STUDENT_BACKGROUND = [ft.Colors.GREEN_50, ft.Colors.GREEN_100, ft.Colors.GREEN_200]
    
    # Common Colors
    SUCCESS = ft.Colors.GREEN_500
    ERROR = ft.Colors.RED_500
    WARNING = ft.Colors.ORANGE_500
    INFO = ft.Colors.BLUE_500
    
    # Button Styles
    @staticmethod
    def get_primary_button_style(theme="admin"):
        color = ThemeConfig.ADMIN_PRIMARY if theme == "admin" else ThemeConfig.STUDENT_PRIMARY
        return ft.ButtonStyle(
            bgcolor=color,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=15),
            padding=ft.padding.symmetric(horizontal=30, vertical=15)
        )
    
    @staticmethod
    def get_secondary_button_style():
        return ft.ButtonStyle(
            bgcolor=ft.Colors.WHITE,
            color=ft.Colors.BLUE_600,
            shape=ft.RoundedRectangleBorder(radius=15),
            border=ft.border.all(1, ft.Colors.BLUE_300)
        )
    
    # Text Field Styles
    @staticmethod
    def get_text_field_style(theme="admin"):
        border_color = ThemeConfig.ADMIN_BORDER if theme == "admin" else ThemeConfig.STUDENT_BORDER
        focused_color = ThemeConfig.ADMIN_PRIMARY if theme == "admin" else ThemeConfig.STUDENT_PRIMARY
        return {
            "border_radius": 15,
            "border_color": border_color,
            "focused_border_color": focused_color,
            "width": 350
        }
    
    # Container Styles
    @staticmethod
    def get_card_style(theme="admin"):
        bg_color = ThemeConfig.ADMIN_LIGHT if theme == "admin" else ThemeConfig.STUDENT_LIGHT
        border_color = ThemeConfig.ADMIN_BORDER if theme == "admin" else ThemeConfig.STUDENT_BORDER
        return {
            "bgcolor": bg_color,
            "padding": 20,
            "border_radius": 15,
            "border": ft.border.all(1, border_color),
            "shadow": ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        }
    
    # Icon Styles
    @staticmethod
    def get_icon_style(theme="admin", size=30):
        # Use theme-appropriate colors instead of default blue
        if theme == "admin":
            color = "#D4817A"  # Pink/coral color for admin
        else:
            color = "#D4817A"  # Same color for student for consistency
        return {
            "size": size,
            "color": color
        }
