"""
メイン画面左側のユーザとのチャット部分
"""

import asyncio
import socket
from contextlib import closing
from winsound import Beep

import flet as ft

from model.api_model import (
    ChatCompletionRequestAssistantMessage,
    ChatCompletionRequestDeveloperMessage,
    ChatCompletionRequestFunctionMessage,
    ChatCompletionRequestMessage,
    ChatCompletionRequestSystemMessage,
    ChatCompletionRequestToolMessage,
    ChatCompletionRequestUserMessage,
)
from model.api_server import FastAPIServer


class ChatView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.port_field = ft.TextField(
            value="8080",
            label="PORT",
            width=100,
            text_size=12,
            height=40,
            content_padding=0,
        )
        self.listen_button = ft.ElevatedButton(
            "STOPPED",
            bgcolor=ft.Colors.RED_400.value,
            color=ft.Colors.WHITE.value,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5),
            ),
            on_click=self.toggle_server,
        )

        self.messages_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=True,
        )

        self.input_field = ft.TextField(
            hint_text="ここにレスポンスを入力...",
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=5,
            border_radius=10,
            filled=True,
        )
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED.value,
            icon_color=ft.Colors.WHITE.value,
            bgcolor=ft.Colors.BLUE_600.value,
            tooltip="Send",
        )
        self.local_ip = self.get_local_ip()

        self.content = ft.Column(
            [
                # Top Bar
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{self.local_ip}:",
                                        style=ft.TextStyle(size=12),
                                    ),
                                    self.port_field,
                                    self.listen_button,
                                ],
                                spacing=10,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN.value,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER.value,
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    border=ft.border.only(bottom=ft.BorderSide(1, "outlineVariant")),
                ),
                # Messages Area
                ft.Container(
                    content=self.messages_list,
                    expand=True,
                    bgcolor="surfaceVariant",  # Slightly different background for chat area
                ),
                # Input Area
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [self.input_field, self.send_button],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN.value,
                                vertical_alignment=ft.CrossAxisAlignment.END.value,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=ft.padding.all(10),
                    border=ft.border.only(top=ft.BorderSide(1, "outlineVariant")),
                ),
            ],
            spacing=0,
        )
    
    def set_message(self, messages: list[str]):
        print(f"{messages=}")
        self.messages_list.controls.clear()
        for message in messages:
            self._add_message(message["content"], message["role"] == "user")
        print(f"{self.messages_list.controls=}")
        self.page.update()

    def _add_message(self, message: str, is_user: bool = False):
        alignment = (
            ft.MainAxisAlignment.END.value
            if not is_user
            else ft.MainAxisAlignment.START.value
        )
        bubble_color = (
            ft.Colors.BLUE_600.value if not is_user else ft.Colors.WHITE.value
        )
        text_color = ft.Colors.WHITE.value if not is_user else ft.Colors.BLACK.value

        # Simple bubble implementation for now
        bubble = ft.Container(
            content=ft.Text(message, color=text_color),
            bgcolor=bubble_color,
            border_radius=10,
            padding=10,
            width=None,  # Allow auto width
            #     constraints=ft.BoxConstraints(max_width=400), # Max width constraint
        )

        row = ft.Row(
            [bubble],
            alignment=alignment,
        )
        self.messages_list.controls.append(row)

    def get_local_ip(self):
        """
        外部サーバーに接続を試みることにより、使用中のローカルIPアドレスを取得する
        """
        try:
            # UDPソケットを使用し、外部に出るためのルーティング情報を得る
            with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except socket.error:
            # エラー時はデフォルトとして localhost を返す
            return "127.0.0.1"
    
    async def on_message_received(self, messages: list[ChatCompletionRequestMessage]):
        messages_json = []
        for message in messages:
            if not message.content:
                continue
            if isinstance(message, ChatCompletionRequestSystemMessage) or isinstance(message, ChatCompletionRequestDeveloperMessage):
                messages_json.append(message.model_dump())
            elif isinstance(message, ChatCompletionRequestUserMessage):
                if isinstance(message.content, str):
                    messages_json.append(message.model_dump())
                else:
                    continue # TODO: PartMessageを処理する
            elif isinstance(message, ChatCompletionRequestAssistantMessage):
                messages_json.append(message.model_dump())
            else:
                continue
        self.set_message(messages_json)
        self.page.update()
        # future = asyncio.get_running_loop().create_future()
        # await future
        return "テストメッセージ"
        
    def toggle_server(self, e: ft.ControlEvent):
        if self.listen_button.text == "STOPPED":
            self.listen_button.text = "RUNNING"
            self.listen_button.bgcolor = ft.Colors.GREEN_400.value
            self.listen_button.disabled = True
            self.port_field.disabled = True
            self.listen_button.update()
            self.port_field.update()
            self.api_server = FastAPIServer(
                host="0.0.0.0",
                port=int(self.port_field.value),
                log_level="info",
                on_message_received=self.on_message_received,
            )
            self.api_server.start()
            self.listen_button.disabled = False
            self.listen_button.update()
        else:
            self.listen_button.text = "STOPPED"
            self.listen_button.bgcolor = ft.Colors.RED_400.value
            self.listen_button.disabled = True
            self.listen_button.update()
            self.api_server.stop()
            self.port_field.disabled = False
            self.listen_button.disabled = False
            self.listen_button.update()
            self.port_field.update()
