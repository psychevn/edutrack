import sqlite3
import re
import flet as ft
import os
import shutil
from datetime import datetime
from db import DB_PATH


def input_field(label: str, password: bool = False):
    return ft.TextField(
        label=label,
        height=48,
        border_radius=12,
        border_color="#D9A6A0",
        password=password,
        can_reveal_password=password,
        expand=True,
    )


def view(route: str, page: ft.Page, goto):
    first = input_field("First Name")
    middle = input_field("Middle Name")
    last = input_field("Last Name")
    email = input_field("EMAIL ADDRESS")
    stud_no = input_field("STUDENT NUMBER")
    sex = ft.Dropdown(options=[ft.dropdown.Option("Male"), ft.dropdown.Option("Female")], label="SEX", border_color="#D9A6A0", border_radius=12)
    username = input_field("USER NAME")
    pwd = input_field("PASSWORD (min 8, 1 uppercase, 1 number, 1 special)", password=True)
    confirm = input_field("CONFIRM PASSWORD", password=True)
    # Photo upload functionality
    photo = ft.FilePicker()
    page.overlay.append(photo)
    photo_path_text = ft.Text("No file selected", size=12, color="#7C6E66")
    photo_preview = ft.Image(width=100, height=100, fit=ft.ImageFit.COVER, visible=False, border_radius=10)
    selected_photo_path = None
    
    def pick_photo(e):
        photo.pick_files(
            allow_multiple=False, 
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp"]
        )
    
    def on_photo_result(e: ft.FilePickerResultEvent):
        nonlocal selected_photo_path
        if e.files and len(e.files) > 0:
            selected_photo_path = e.files[0].path
            photo_path_text.value = e.files[0].name
            photo_preview.src = selected_photo_path
            photo_preview.visible = True
            page.update()
    
    photo.on_result = on_photo_result
    
    def save_photo(username):
        """Save uploaded photo with unique filename"""
        if not selected_photo_path:
            return None
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads/profile_photos"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Get file extension
        file_extension = os.path.splitext(selected_photo_path)[1]
        
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"student_{username}_{timestamp}{file_extension}"
        new_path = os.path.join(uploads_dir, new_filename)
        
        try:
            # Copy file to uploads directory
            shutil.copy2(selected_photo_path, new_path)
            return new_path
        except Exception as ex:
            print(f"Error saving photo: {ex}")
            return None
    recovery_q = ft.Dropdown(
        label="SELECT SECURITY QUESTION",
        options=[
            ft.dropdown.Option("Your birthplace?"),
            ft.dropdown.Option("First pet's name?"),
            ft.dropdown.Option("Mother's maiden name?"),
            ft.dropdown.Option("Favorite teacher's last name?"),
            ft.dropdown.Option("Elementary school name?"),
        ],
        border_color="#D9A6A0",
        border_radius=12,
    )
    recovery_ans = input_field("SECURITY ANSWER")

    def open_snack(msg: str):
        sb = ft.SnackBar(ft.Text(msg))
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def is_strong_password(p: str) -> bool:
        # At least 8 chars, one uppercase, one number, one special char
        return bool(re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$", p or ""))

    def do_register(e):
        # Validate required fields (everything except suffix and middle optional)
        required_values = [first.value, last.value, email.value, stud_no.value, sex.value, username.value, pwd.value, confirm.value, recovery_q.value, recovery_ans.value]
        if not all(required_values):
            open_snack("Please fill out all required fields.")
            return
        if not is_strong_password(pwd.value):
            open_snack("Password must be 8+ chars, include 1 uppercase, 1 number, 1 special.")
            return
        if pwd.value != confirm.value:
            open_snack("Passwords do not match")
            return
        # Save photo first
        photo_path = save_photo(username.value)
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO students (first_name, middle_name, last_name, email, student_number, sex, username, password, recovery_question, recovery_answer, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    first.value,
                    middle.value,
                    last.value,
                    email.value,
                    stud_no.value,
                    sex.value,
                    username.value,
                    pwd.value,
                    recovery_q.value,
                    recovery_ans.value,
                    photo_path,
                ),
            )
            conn.commit()
            conn.close()
            open_snack("Registered. You can login now.")
            goto("/student/login")
        except sqlite3.IntegrityError as ex:
            open_snack(f"Error: {ex}")

    grid = ft.Container(
        width=min(980, page.window.width * 0.9) if page.window.width else 980,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(2, color="#E2C9C2"),
        border_radius=30,
        padding=24,
        expand=True,
        content=ft.Column(
            [
                ft.Row([ft.Text("STUDENT SIGN UP", size=24, weight=ft.FontWeight.W_800)],),
                ft.ResponsiveRow([
                    ft.Container(first, col={"sm": 12, "md": 4, "lg": 4}),
                    ft.Container(middle, col={"sm": 12, "md": 4, "lg": 4}),
                    ft.Container(last, col={"sm": 12, "md": 4, "lg": 4})
                ], spacing=10),
                ft.ResponsiveRow([
                    ft.Container(stud_no, col={"sm": 12, "md": 6, "lg": 6}),
                    ft.Container(sex, col={"sm": 12, "md": 6, "lg": 6})
                ], spacing=10),
                ft.Container(height=8),
                ft.ResponsiveRow([
                    ft.Container(username, col={"sm": 12, "md": 4, "lg": 4}),
                    ft.Container(pwd, col={"sm": 12, "md": 4, "lg": 4}),
                    ft.Container(confirm, col={"sm": 12, "md": 4, "lg": 4})
                ], spacing=10),
                ft.ResponsiveRow([
                    ft.Container(
                        ft.Column([
                            email,
                            ft.Container(height=10),
                            ft.ElevatedButton(
                                "Upload Profile Picture", 
                                icon=ft.Icons.UPLOAD_FILE, 
                                on_click=pick_photo, 
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    bgcolor="#E2C9C2",
                                    color=ft.Colors.BLACK
                                )
                            ),
                            photo_path_text,
                            ft.Container(height=5),
                            photo_preview,
                        ], spacing=5),
                        col={"sm": 12, "md": 6, "lg": 6}
                    ),
                    ft.Container(
                        ft.Column([
                            recovery_q,
                            recovery_ans,
                        ], spacing=10),
                        col={"sm": 12, "md": 6, "lg": 6}
                    )
                ], spacing=10),
                ft.Row([
                    ft.ElevatedButton(
                        "SIGN UP",
                        on_click=do_register,
                        height=48,
                        style=ft.ButtonStyle(
                            bgcolor="#CFA8A1",
                            color=ft.Colors.BLACK,
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),
                    ft.TextButton("Already have an account? Log in", on_click=lambda _: goto("/student/login")),
                ], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE
        ),
    )

    return ft.View(
        route,
        bgcolor="#F5F2ED",
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                content=ft.Column(
                    [
                        ft.Text(
                            "EDUTRACK", 
                            size=min(56, page.window.width * 0.05) if page.window.width else 56, 
                            weight=ft.FontWeight.W_800, 
                            color="#B56464"
                        ),
                        ft.Container(height=16),
                        grid,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    scroll=ft.ScrollMode.ADAPTIVE
                ),
            )
        ],
        scroll=ft.ScrollMode.ADAPTIVE,
    )


