import sqlite3
import flet as ft
from db import DB_PATH


def _sidebar_item(icon: ft.Icon, label: str, selected: bool):
    return ft.Container(
        bgcolor="#F4D5CF" if selected else "#E9B7AF",
        border_radius=12,
        padding=10,
        border=ft.border.all(1, color="#D9A6A0") if selected else None,
        content=ft.Row([icon, ft.Text(label, weight=ft.FontWeight.W_600)], spacing=10),
    )


def _user_page(page: ft.Page):
    student_id = page.session.get("student_id")
    first = ft.TextField(label="First Name", border_radius=10, border_color="#C9B8AA", height=44)
    middle = ft.TextField(label="Middle Name", border_radius=10, border_color="#C9B8AA", height=44)
    last = ft.TextField(label="Last Name", border_radius=10, border_color="#C9B8AA", height=44)
    sfx = ft.TextField(label="Sfx", border_radius=10, width=120, border_color="#C9B8AA", height=44)
    email = ft.TextField(label="Email Address", border_radius=10, border_color="#C9B8AA", height=44)
    num = ft.TextField(label="Student Number", border_radius=10, border_color="#C9B8AA", height=44)
    sex = ft.Dropdown(label="Sex", options=[ft.dropdown.Option("Male"), ft.dropdown.Option("Female")], border_color="#C9B8AA", border_radius=10)
    username = ft.TextField(label="Username", border_radius=10, border_color="#C9B8AA", height=44)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, border_radius=10, border_color="#C9B8AA", height=44)
    recovery_q = ft.Dropdown(label="SELECT SECURITY QUESTION", options=[ft.dropdown.Option("Your birthplace?"), ft.dropdown.Option("First pet's name?")], border_color="#C9B8AA", border_radius=10)
    recovery_ans = ft.TextField(label="Security Answer", border_radius=10, border_color="#C9B8AA", height=44)

    # Profile photo controls
    photo_path = None
    avatar = ft.CircleAvatar(radius=30, bgcolor="#D9D0C7")
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    def on_photo_result(e: ft.FilePickerResultEvent):
        nonlocal photo_path
        if e.files and len(e.files) > 0:
            photo_path = e.files[0].path or e.files[0].name
            avatar.foreground_image_url = photo_path
            page.update()
    file_picker.on_result = on_photo_result
    def pick_photo(_: ft.ControlEvent):
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    # load current values (including saved photo and recovery answer)
    if student_id:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT first_name, middle_name, last_name, suffix, email, student_number, sex, username, password, recovery_question, recovery_answer, photo_path FROM students WHERE id = ?",
            (student_id,),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            first.value, middle.value, last.value, sfx.value, email.value, num.value, sex.value, username.value, password.value, recovery_q.value, recovery_ans.value, existing_photo = row
            if existing_photo:
                avatar.foreground_image_url = existing_photo

    def save_changes(e):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE students SET first_name=?, middle_name=?, last_name=?, suffix=?, email=?, student_number=?, sex=?, username=?, password=?, recovery_question=?, recovery_answer=?, photo_path=COALESCE(?, photo_path)
            WHERE id=?
            """,
            (
                first.value,
                middle.value,
                last.value,
                sfx.value,
                email.value,
                num.value,
                sex.value,
                username.value,
                password.value,
                recovery_q.value,
                recovery_ans.value,
                photo_path,
                student_id,
            ),
        )
        conn.commit()
        conn.close()
        sb = ft.SnackBar(ft.Text("Saved"))
        page.overlay.append(sb)
        sb.open = True
        page.update()

    header = ft.Text("Student Information", size=32, weight=ft.FontWeight.W_800, color="#B55C5C")
    form = ft.Column(
        [
            ft.Row([
                ft.Row([avatar, ft.TextButton("Change Photo", icon=ft.icons.UPLOAD_FILE, on_click=pick_photo)], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(expand=True),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Row([first, middle, last, sfx], spacing=10),
            ft.Row([email, num, sex], spacing=10),
            ft.Divider(height=20, color="#E6D6CC"),
            ft.Row([username, recovery_q], spacing=10),
            ft.Row([password, recovery_ans], spacing=10),
            ft.Row([
                ft.ElevatedButton(
                    "SAVE CHANGES",
                    on_click=save_changes,
                    style=ft.ButtonStyle(bgcolor="#C29A6B", color=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=12)),
                )
            ], alignment=ft.MainAxisAlignment.END),
        ],
        spacing=10,
    )
    card = ft.Container(
        bgcolor=ft.colors.WHITE,
        border_radius=24,
        border=ft.border.all(1, color="#E6D6CC"),
        padding=20,
        content=ft.Column([header, form], spacing=12),
    )
    return card


def _dashboard_page():
    def stat_card(title: str):
        return ft.Container(
            width=220,
            height=120,
            border=ft.border.all(1, color="#E6D6CC"),
            border_radius=20,
            padding=16,
            content=ft.Column([ft.Text("0", size=36, weight=ft.FontWeight.W_800), ft.Text(title)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

    recent = ft.Container(
        border=ft.border.all(1, color="#E6D6CC"),
        border_radius=20,
        padding=16,
        content=ft.Column([ft.Text("Recent Post", size=22, weight=ft.FontWeight.W_700), ft.Container(height=10), ft.Container(bgcolor="#E9B7AF", border_radius=16, padding=16, content=ft.Column([ft.Text("Assessment", weight=ft.FontWeight.W_800, color=ft.colors.WHITE), ft.Text("Description........", color=ft.colors.WHITE)], spacing=4))]),
        expand=True,
    )
    calendar = ft.Container(width=260, border=ft.border.all(1, color="#C9B8AA"), border_radius=16, padding=16, content=ft.Text("Calendar"))
    return ft.Column([
        ft.Text("Dashboard", size=28, weight=ft.FontWeight.W_800, color="#B55C5C"),
        ft.Row([stat_card("Pending Assessment"), stat_card("Completed Assessment"), calendar], spacing=16),
        recent,
    ], spacing=16)


def _assessments_page():
    def item(status: str, button_text: str):
        return ft.Container(
            border=ft.border.all(1, color="#E6D6CC"),
            border_radius=20,
            padding=16,
            content=ft.Column([
                ft.Text("Assessment", weight=ft.FontWeight.W_800),
                ft.Container(height=8),
                ft.Row([
                    ft.Container(bgcolor="#C2B16B" if status=="PENDING" else "#7AA36C", padding=6, border_radius=8, content=ft.Text(status, color=ft.colors.WHITE)),
                    ft.Container(expand=True),
                    ft.ElevatedButton(button_text, style=ft.ButtonStyle(bgcolor="#B55C5C", color=ft.colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))),
                ])
            ])
        )

    return ft.Column([
        ft.Text("Manage Assessment", size=28, weight=ft.FontWeight.W_800, color="#B55C5C"),
        item("PENDING", "TAKE"),
        item("COMPLETED", "RESULT"),
    ], spacing=12)


def _scores_page():
    def score_row(idx: int, status: str, score: str):
        return ft.Container(
            border=ft.border.all(1, color="#E6D6CC"),
            border_radius=20,
            padding=16,
            content=ft.Row([
                ft.Column([ft.Text(f"Assessment # {idx}", weight=ft.FontWeight.W_800), ft.Text(status), ft.Text("09/15/2025", size=12, color="#9B8F86")]),
                ft.Container(expand=True),
                ft.Text(score, weight=ft.FontWeight.W_800),
                ft.TextButton("Check Answers", icon=ft.icons.REMOVE_RED_EYE_OUTLINED),
            ])
        )

    search = ft.TextField(prefix_icon=ft.icons.SEARCH, border_radius=20, height=44, hint_text="Search")
    sort = ft.Dropdown(value="earliest to oldest", options=[ft.dropdown.Option("earliest to oldest"), ft.dropdown.Option("latest to earliest")], width=220, border_radius=20)

    return ft.Column([
        ft.Text("Scores", size=28, weight=ft.FontWeight.W_800, color="#B55C5C"),
        ft.Row([sort, search], spacing=10),
        score_row(1, "PASSED", "10/25"),
        score_row(2, "FAILED", "1/18"),
        score_row(3, "PASANG AWA", "22/40"),
    ], spacing=12)


def _get_sidebar_profile(page: ft.Page):
    student_id = page.session.get("student_id")
    display_name = "Student"
    photo_path = None
    if student_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT first_name, last_name, photo_path FROM students WHERE id=?", (student_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                first_name, last_name, photo_path = row
                if last_name or first_name:
                    display_name = f"{last_name or ''}, {first_name or ''}".strip(', ')
        except Exception:
            pass
    return display_name, photo_path


def view(route: str, page: ft.Page, goto=None):
    selected_index = 0

    content = ft.Container(expand=True)

    display_name, saved_photo_path = _get_sidebar_profile(page)

    avatar_sidebar = ft.CircleAvatar(radius=28, bgcolor="#D9D0C7")
    if saved_photo_path:
        avatar_sidebar.foreground_image_url = saved_photo_path

    sidebar = ft.Container(
        width=240,
        bgcolor="#E9B7AF",
        padding=16,
        border_radius=ft.border_radius.only(top_right=60, bottom_right=60),
        content=ft.Column(
            [
                ft.Container(
                    height=90,
                    content=ft.Row(
                        [
                            avatar_sidebar,
                            ft.Column(
                                [ft.Text(display_name, weight=ft.FontWeight.W_800), ft.Text("Student")],
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=6),
                # Sidebar items; selected styles update dynamically via rebuild
                ft.Container(key="nav-items"),
                ft.Container(expand=True),
                ft.TextButton("Logout", icon=ft.icons.LOGOUT, on_click=lambda e: _confirm_logout(page, goto)),
            ],
            spacing=10,
        ),
    )

    def build_nav_items():
        return ft.Column([
            ft.GestureDetector(on_tap=lambda e: set_page(0), content=_sidebar_item(ft.Icon(ft.icons.PERSON_OUTLINE), "User", selected_index == 0)),
            ft.GestureDetector(on_tap=lambda e: set_page(1), content=_sidebar_item(ft.Icon(ft.icons.HOME_OUTLINED), "Dashboard", selected_index == 1)),
            ft.GestureDetector(on_tap=lambda e: set_page(2), content=_sidebar_item(ft.Icon(ft.icons.DESCRIPTION_OUTLINED), "Assessments", selected_index == 2)),
            ft.GestureDetector(on_tap=lambda e: set_page(3), content=_sidebar_item(ft.Icon(ft.icons.STAR_BORDER), "Scores", selected_index == 3)),
        ], spacing=10)

    def set_page(idx: int):
        nonlocal selected_index
        selected_index = idx
        if idx == 0:
            content.content = _user_page(page)
            if goto:
                goto("/student/home/user")
        elif idx == 1:
            content.content = _dashboard_page()
            if goto:
                goto("/student/home/dashboard")
        elif idx == 2:
            content.content = _assessments_page()
            if goto:
                goto("/student/home/assessments")
        else:
            content.content = _scores_page()
            if goto:
                goto("/student/home/scores")
        # rebuild nav to reflect active item
        sidebar.content.controls[2] = build_nav_items()
        page.update()

    # Initial content based on route
    if route.endswith("/dashboard"):
        set_page(1)
    elif route.endswith("/assessments"):
        set_page(2)
    elif route.endswith("/scores"):
        set_page(3)
    else:
        set_page(0)

    shell = ft.Row([
        sidebar,
        ft.Container(width=12),
        ft.Container(expand=True, padding=16, content=content, border=ft.border.all(1, color="#E6D6CC"), border_radius=24, bgcolor=ft.colors.WHITE),
    ], expand=True)

    return ft.View(route, controls=[shell], bgcolor="#F5F2ED")


def _confirm_logout(page: ft.Page, goto):
    def do_logout(e):
        try:
            page.session.remove("student_id")
        except Exception:
            page.session.set("student_id", None)
        dialog.open = False
        page.update()
        if goto:
            goto("/")

    dialog = ft.AlertDialog(
        title=ft.Text("Logout"),
        content=ft.Text("Are you sure you want to log out?"),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
            ft.ElevatedButton("Log out", on_click=do_logout, style=ft.ButtonStyle(bgcolor="#B56464", color=ft.colors.WHITE)),
        ],
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


