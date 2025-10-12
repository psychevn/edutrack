"""
Example showing how to use the theme configuration for easy UI customization
"""

import flet as ft
from config.theme import ThemeConfig

def create_custom_login_page():
    """Example of using theme configuration for consistent styling"""
    
    # Using theme configuration
    username_field = ft.TextField(
        label="Username",
        prefix_icon=ft.icons.PERSON,
        **ThemeConfig.get_text_field_style("admin")  # Uses admin theme
    )
    
    password_field = ft.TextField(
        label="Password",
        prefix_icon=ft.icons.LOCK,
        password=True,
        **ThemeConfig.get_text_field_style("admin")
    )
    
    login_button = ft.ElevatedButton(
        "Login",
        icon=ft.icons.LOGIN,
        style=ThemeConfig.get_primary_button_style("admin"),
        on_click=lambda e: print("Login clicked")
    )
    
    # Using theme colors directly
    header_icon = ft.Icon(
        ft.icons.ADMIN_PANEL_SETTINGS,
        **ThemeConfig.get_icon_style("admin", 60)
    )
    
    # Using theme container style
    form_container = ft.Container(
        content=ft.Column([
            header_icon,
            ft.Text("Admin Login", size=24, color=ThemeConfig.ADMIN_ACCENT),
            username_field,
            password_field,
            login_button
        ]),
        **ThemeConfig.get_card_style("admin")
    )
    
    return form_container

def create_custom_student_page():
    """Example for student theme"""
    
    # Student theme example
    username_field = ft.TextField(
        label="Student Username",
        prefix_icon=ft.icons.SCHOOL,
        **ThemeConfig.get_text_field_style("student")  # Uses student theme
    )
    
    login_button = ft.ElevatedButton(
        "Login as Student",
        icon=ft.icons.LOGIN,
        style=ThemeConfig.get_primary_button_style("student"),
        on_click=lambda e: print("Student login clicked")
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.SCHOOL, **ThemeConfig.get_icon_style("student", 60)),
            ft.Text("Student Login", size=24, color=ThemeConfig.STUDENT_ACCENT),
            username_field,
            login_button
        ]),
        **ThemeConfig.get_card_style("student")
    )

# Example of how to change the entire color scheme
def change_to_purple_theme():
    """Example of changing the admin theme to purple"""
    
    # Override theme colors
    ThemeConfig.ADMIN_PRIMARY = ft.colors.PURPLE_500
    ThemeConfig.ADMIN_SECONDARY = ft.colors.PURPLE_600
    ThemeConfig.ADMIN_ACCENT = ft.colors.PURPLE_700
    ThemeConfig.ADMIN_LIGHT = ft.colors.PURPLE_50
    ThemeConfig.ADMIN_BORDER = ft.colors.PURPLE_200
    ThemeConfig.ADMIN_BACKGROUND = [ft.colors.PURPLE_50, ft.colors.PURPLE_100, ft.colors.PURPLE_200]
    
    print("Theme changed to purple!")

def change_to_dark_theme():
    """Example of changing to dark theme"""
    
    # Dark theme colors
    ThemeConfig.ADMIN_PRIMARY = ft.colors.BLUE_400
    ThemeConfig.ADMIN_SECONDARY = ft.colors.BLUE_300
    ThemeConfig.ADMIN_ACCENT = ft.colors.BLUE_200
    ThemeConfig.ADMIN_LIGHT = ft.colors.GREY_800
    ThemeConfig.ADMIN_BORDER = ft.colors.GREY_700
    ThemeConfig.ADMIN_BACKGROUND = [ft.colors.GREY_900, ft.colors.GREY_800, ft.colors.GREY_700]
    
    print("Theme changed to dark!")

if __name__ == "__main__":
    print("Theme configuration examples:")
    print("1. Use ThemeConfig.get_text_field_style('admin') for consistent text fields")
    print("2. Use ThemeConfig.get_primary_button_style('student') for consistent buttons")
    print("3. Use ThemeConfig.ADMIN_PRIMARY for direct color access")
    print("4. Call change_to_purple_theme() or change_to_dark_theme() to switch themes")
