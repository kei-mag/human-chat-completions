"""
メイン画面右側のレスポンス構築
"""
import flet as ft


class ConsoleView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.page = page
        # 1. Error Display Area (Hidden by default)
        self.error_container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE.value, color=ft.Colors.RED_700.value),
                    ft.Text("API Key is missing (Auto-injected in runtime). Mocking response for demo.", 
                            color=ft.Colors.RED_700.value, size=12, expand=True),
                ],
                alignment=ft.MainAxisAlignment.START.value,
            ),
            bgcolor=ft.Colors.RED_50.value,
            border=ft.border.all(1, ft.Colors.RED_200.value),
            border_radius=5,
            padding=10,
            visible=False, # Initially hidden
        )

        # 2. Controls & Mode Switch
        self.settings_button = ft.IconButton(ft.Icons.SETTINGS.value, tooltip="Settings")
        self.theme_icon = ft.Icon(ft.Icons.DARK_MODE.value) # Default icon
        self.theme_switch = ft.Switch(label="Dark Mode", on_change=self.toggle_theme)

        self.mode_segment = ft.SegmentedButton(
            selected={"llm_draft"},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value="manual",
                    label=ft.Text("Manual"),
                    icon=ft.Icon(ft.Icons.PERSON.value),
                ),
                ft.Segment(
                    value="llm_draft",
                    label=ft.Text("LLM Draft"),
                    icon=ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE.value),
                ),
                ft.Segment(
                    value="full_llm",
                    label=ft.Text("Full LLM"),
                    icon=ft.Icon(ft.Icons.SMART_TOY.value),
                ),
            ],
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
        )

        # 4. Drafts Area
        self.drafts_column = ft.Column(spacing=10)
        # Dummy drafts for visualization
        self.drafts_column.controls = [
            self._create_draft_card("1", "はい、デザインの相談ですね。具体的にどのようなテイストをご希望でしょうか？"),
            self._create_draft_card("2", "承知いたしました。参考となる画像やサイトなどはありますか？"),
            self._create_draft_card("3", "画面構成についてですね。チャット画面と操作パネルの比率などは決まっていますか？"),
        ]
        
        self.regenerate_button = ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.REFRESH.value, size=16), ft.Text("Regenerate")]),
            style=ft.ButtonStyle(color=ft.Colors.BLUE.value),
        )

        self.content = ft.Column(
            [
                self.error_container,
                ft.Divider(color=ft.Colors.TRANSPARENT.value, height=10),
                
                ft.Row(
                    [
                        ft.Text("Response Mode", weight=ft.FontWeight.BOLD.value),
                        ft.Row([self.theme_switch, self.settings_button]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN.value,
                ),
                ft.Container(self.mode_segment, padding=ft.padding.only(bottom=20)),

                self.system_prompt,
                
                ft.Row([ft.Icon(ft.Icons.ARROW_DOWNWARD.value, color=ft.Colors.GREY_400.value)], alignment=ft.MainAxisAlignment.CENTER.value),
                
                ft.Row(
                    [
                        ft.Text("COPILOT Draft Candidates", weight=ft.FontWeight.BOLD.value, color=ft.Colors.GREY_700.value),
                        self.regenerate_button
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN.value
                ),
                
                self.drafts_column,
            ],
            scroll=ft.ScrollMode.AUTO.value, # Enable scrolling for console view
        )

    def _create_draft_card(self, index: str, text: str):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(index, size=12, weight=ft.FontWeight.BOLD.value, color=ft.Colors.GREY_600.value),
                        bgcolor=ft.Colors.GREY_200.value,
                        padding=5,
                        border_radius=5,
                    ),
                    ft.Text(text, expand=True, size=13),
                ],
                alignment=ft.MainAxisAlignment.START.value,
                vertical_alignment=ft.CrossAxisAlignment.START.value,
            ),
            padding=10,
            border=ft.border.all(1, "outlineVariant"),
            border_radius=8,
            on_click=lambda e: print(f"Draft {index} clicked"), # Placeholder handler
            ink=True,
        )

    def toggle_theme(self, e):
        # This will be handled by the main app, but we need to expose the event or callback
        if e.control.page:
            e.control.page.theme_mode = ft.ThemeMode.DARK if e.control.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
            e.control.page.update()
