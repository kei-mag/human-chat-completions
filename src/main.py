import logging

import flet as ft

from view.chat import ChatView
from view.console import ConsoleView

logging.basicConfig(level=logging.INFO)

def main(page: ft.Page):
    page.title = "Human Chat Completions v0.1.0"
    page.description = "Operator Dashboard for WoZ experiments"
    page.window.icon = "icon.png" 

    # Theme Configuration
    page.theme = ft.Theme(
        color_scheme_seed="#086fad",
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed="#086fad",
    )
    page.theme_mode = ft.ThemeMode.SYSTEM
    
    # Initialize Views
    chat_view = ChatView(page)
    console_view = ConsoleView(page)

    # Layout Containers
    # We will use these to organize the layout dynamically
    
    def handle_resize(e):
        """
        Switch between Row (Side-by-Side) and Column (Stacked) layout
        based on window width.
        Threshold set to 900px.
        """
        page.clean()
        
        if page.width > 900:
            # Wide mode: Side-by-side
            page.add(
                ft.Row(
                    [
                        chat_view,
                        ft.VerticalDivider(width=1, color="outlineVariant"),
                        console_view
                    ],
                    expand=True,
                    spacing=0,
                )
            )
        else:
            # Narrow mode: Stacked
            page.add(
                ft.Column(
                    [
                        ft.Container(chat_view, height=600), # Fixed height for chat in mobile view or flex
                        ft.Divider(height=1),
                        ft.Container(console_view, expand=True)
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO
                )
            )
        page.update()

    # Initial Layout
    page.on_resized = handle_resize
    
    # Trigger initial layout
    handle_resize(None)


ft.app(target=main, assets_dir="assets")
