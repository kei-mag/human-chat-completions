"""
メイン画面右側のレスポンス構築
"""
import flet as ft
import flet.core.webview


class ConsoleView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.page = page
        # 1. Error Display Area (Hidden by default)
        self.error_container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_700),
                    ft.Text("API Key is missing (Auto-injected in runtime). Mocking response for demo.", 
                            color=ft.Colors.RED_700, size=12, expand=True),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=ft.Colors.RED_50,
            border=ft.border.all(1, ft.Colors.RED_200),
            border_radius=5,
            padding=10,
            visible=False, # Initially hidden
        )

        # 2. Controls & Mode Switch
        self.settings_button = ft.IconButton(ft.Icons.SETTINGS, tooltip="Settings", disabled=True)

        self.theme_switch = ft.SegmentedButton(
            selected={ft.ThemeMode.SYSTEM.value},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value=ft.ThemeMode.LIGHT.value,
                    label=ft.Text("Light Mode"),
                    icon=ft.Icon(ft.Icons.LIGHT_MODE),
                ),
                ft.Segment(
                    value=ft.ThemeMode.SYSTEM.value,
                    label=ft.Text("System Mode"),
                    icon=ft.Icon(ft.Icons.BRIGHTNESS_6),
                ),
                ft.Segment(
                    value=ft.ThemeMode.DARK.value,
                    label=ft.Text("Dark Mode"),
                    icon=ft.Icon(ft.Icons.DARK_MODE),
                ),
            ],
            show_selected_icon=False,
            on_change=self.set_theme,
            width=400, # Approximate width to match image
        )

        self.mode_segment = ft.SegmentedButton(
            selected={"manual"},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value="manual",
                    label=ft.Text("Manual"),
                    icon=ft.Icon(ft.Icons.PERSON),
                ),
                ft.Segment(
                    value="llm_draft",
                    label=ft.Text("LLM Draft"),
                    icon=ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE),
                ),
                ft.Segment(
                    value="full_llm",
                    label=ft.Text("Full LLM"),
                    icon=ft.Icon(ft.Icons.SMART_TOY),
                ),
            ],
            show_selected_icon=False,
            disabled=True, # 実装するまで使用不可
            width=400, # Approximate width to match image
        )

        # 3. System Prompt
        self.system_prompt = ft.TextField(
            label="> Draft Generation Prompt (SYSTEM)",
            value="あなたは親切なAIアシスタントです。ユーザーの質問に対して、簡潔かつ丁寧に回答してください。",
            multiline=True,
            min_lines=3,
            max_lines=5,
            text_size=13,
            border_radius=5,
            disabled=True,
        )

        # 4. Drafts Area
        self.drafts_column = ft.Column(spacing=10)
        # Dummy drafts for visualization
        self.drafts_column.controls = [
            self._create_draft_card("1", "To be implemented"),
            self._create_draft_card("2", "To be implemented"),
            self._create_draft_card("3", "To be implemented"),
        ]
        
        self.regenerate_button = ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.REFRESH, size=16), ft.Text("Regenerate")]),
            style=ft.ButtonStyle(color=ft.Colors.BLUE),
        )

        self.content = ft.Column(
            [
                self.error_container,
                ft.Divider(color=ft.Colors.TRANSPARENT, height=10),

                ft.Row([ft.Text("Settings", weight=ft.FontWeight.BOLD), self.theme_switch, self.settings_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Row(
                    [
                        ft.Text("Response Mode", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(self.mode_segment, padding=ft.padding.only(bottom=20)),

                self.system_prompt,
                
                ft.Row([ft.Icon(ft.Icons.ARROW_DOWNWARD, color=ft.Colors.GREY_400)], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Row(
                    [
                        ft.Text("COPILOT Draft Candidates", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        self.regenerate_button
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                
                self.drafts_column,
            ],
            scroll=ft.ScrollMode.AUTO, # Enable scrolling for console view
        )

    def _create_draft_card(self, index: str, text: str):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(index, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600),
                        bgcolor=ft.Colors.GREY_200,
                        padding=5,
                        border_radius=5,
                    ),
                    ft.Text(text, expand=True, size=13),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=10,
            border=ft.border.all(1, "outlineVariant"),
            border_radius=8,
            ink=True,
            disabled=True,
        )

    def set_theme(self, e):
        # This will be handled by the main app, but we need to expose the event or callback
        if e.control.page:
            e.control.page.theme_mode = e.control.selected.pop()
            e.control.page.update()
