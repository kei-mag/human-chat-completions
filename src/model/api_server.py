"""
/v1/chat/completions APIリクエストを処理するサーバー
"""

import asyncio
import threading
import time
from datetime import datetime
from logging import getLogger
from typing import AsyncGenerator, Awaitable, Callable, Optional

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# 同じディレクトリにある api_model.py からインポート
# フォルダ構成が異なる場合（例: modelフォルダ内にある場合）は適宜修正してください
from model.api_model import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionRequestMessage,
    ChatCompletionResponseMessage,
    ChatCompletionStreamChoice,
    ChatCompletionStreamResponseDelta,
    CreateChatCompletionRequest,
    CreateChatCompletionResponse,
    FinishReason,
    ListModelsResponse,
    Model,
    OllamaListModelsResponse,
    OllamaModel,
    OllamaModelDetails,
)

logger = getLogger(__name__)


class FastAPIServer:
    def __init__(
        self,
        host: str,
        port: int,
        log_level: str,
        on_message_received: Callable[[Awaitable[ChatCompletionRequestMessage]], str],
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
    ):
        self.app = FastAPI(
            title="Human Chat Completions",
            summary="OpenAI Chat Completions API compatible API.",
            description="Human Chat Completions is a simple HTTP server that implements the OpenAI Chat Completions API.",
            version="0.1.0",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_api_route(
            "/",
            self.root,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
        )
        self.app.add_api_route(
            "/v1/chat/completions",
            self.chat_completions,
            methods=["POST"],
        )
        self.app.add_api_route(
            "/chat/completions",
            self.chat_completions,
            methods=["POST"],
        )
        self.app.add_api_route(
            "/v1/models",
            self.list_models,
            methods=["GET"],
        )
        self.app.add_api_route(
            "/v1/models/{model_id}",
            self.retrieve_model,
            methods=["GET"],
            tags=["Models"],
            summary="Retrieve model",
            operation_id="retrieveModel",
            response_model=Model,
        )
        self.app.add_api_route(
            "/api/tags",
            self.list_models_ollama,
            methods=["GET"],
            tags=["Ollama Compatibility"],
            summary="List models (Ollama)",
            operation_id="listModelsOllama",
            response_model=OllamaListModelsResponse
        )
        self.app.add_exception_handler(404, self.not_found_handler)
        self.config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level=log_level,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            loop="asyncio",
        )
        self.server = uvicorn.Server(self.config)
        self._thread = None
        self.on_message_received = on_message_received
        self.port = port
        self.launch_time = time.time()

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        def target():
            # スレッド内で新しいイベントループを作成・設定
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.server.run()

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        if self.server.started:
            self.server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout)
            if self._thread.is_alive():
                logger.warning("Uvicorn thread did not exit gracefully.")

    # ==========================================
    # Streaming Generator
    # ==========================================

    async def stream_generator(
        self, content: str, model_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Server-Sent Events (SSE) 形式でレスポンスをストリーミングします。
        """
        chunk_id = f"chatcmpl-{int(time.time())}"
        created_time = int(time.time())

        # 文字単位でストリーミングするシミュレーション
        tokens = list(content)

        for i, token in enumerate(tokens):
            # 擬似的なタイピング遅延
            await asyncio.sleep(0.05)

            chunk = ChatCompletionChunk(
                id=chunk_id,
                created=created_time,
                model=model_id,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta=ChatCompletionStreamResponseDelta(
                            # 最初のチャンクだけroleを入れる（仕様上は毎回でも可だが、一般的実装に合わせる）
                            role="assistant" if i == 0 else None,
                            content=token,
                        ),
                        finish_reason=None,
                    )
                ],
            )

            # SSE形式: data: <json_string>\n\n
            yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

        # 完了時のChunk (finish_reason="stop", contentは空)
        final_chunk = ChatCompletionChunk(
            id=chunk_id,
            created=created_time,
            model=model_id,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta=ChatCompletionStreamResponseDelta(),
                    finish_reason=FinishReason.stop,
                )
            ],
            # usageを送る場合はここに `usage=...` を追加
        )
        yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"

        # ストリーム終了シグナル
        yield "data: [DONE]\n\n"

    # ==========================================
    # Endpoints
    # ==========================================

    async def root(self, request: Request):
        return {
            "message": f"Human Chat Completions listening on port {self.port}.\nUsage: POST /chat/completions or /v1/chat/completions.",
            "request": {
                "method": request.method,
                "url": request.url,
                "query_params": request.query_params,
                "headers": request.headers,
                "body": await request.body(),
            }
        }

    async def chat_completions(
        self,
        request: CreateChatCompletionRequest,
        authorization: Optional[str] = Header(None),
    ):
        """
        OpenAI互換のChat Completionsエンドポイント
        """
        # 1. 応答内容の取得（ビジネスロジック呼び出し）
        # ストリーミングの場合でも、現状は「全応答が決まってから流す」方式としています
        logger.debug(request.messages)
        response_content = await self.on_message_received(request.messages)

        # モデルIDの取得
        model_id = request.model

        # 2. ストリーミングリクエストの場合
        if request.stream:
            return StreamingResponse(
                self.stream_generator(response_content, model_id),
                media_type="text/event-stream",
            )

        # 3. 通常リクエストの場合
        else:
            return CreateChatCompletionResponse(
                id=f"chatcmpl-{int(time.time())}",
                created=int(time.time()),
                model=model_id,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatCompletionResponseMessage(
                            role="assistant", content=response_content
                        ),
                        finish_reason=FinishReason.stop,
                    )
                ],
            )
    
    async def list_models(self):
        """
        利用可能なモデルのリストを返します。
        """
        return ListModelsResponse(
            data=[
                Model(id="human", created=int(self.launch_time), owned_by="human-backend"),
            ]
        )
    
    async def retrieve_model(self, model_id: str):
        """
        特定のモデル情報を取得します。
        OpenAI API互換のため、GET /v1/models/human 等に対応します。
        """
        # 許可するモデルの定義
        allowed_models = {
            Model(id="human", created=int(self.launch_time), owned_by="human-backend"),
        }

        if model_id not in allowed_models:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "message": f"The model '{model_id}' does not exist",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": "model_not_found"
                    }
                }
            )
        
        return allowed_models[model_id]
    
    async def list_models_ollama(self):
        """
        Ollama互換のモデル一覧エンドポイントです。
        """
        return OllamaListModelsResponse(
            models=[
                OllamaModel(
                    name="human:latest",
                    model="human:latest",
                    modified_at=datetime.fromtimestamp(self.launch_time).isoformat(),
                    details=OllamaModelDetails()
                ),
            ]
        )

    async def not_found_handler(self, request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Human Chat Completions supports only POST /v1/chat/completions endpoint.",
            },
        )
