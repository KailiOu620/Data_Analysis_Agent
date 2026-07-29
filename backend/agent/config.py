"""阿里云百炼 Qwen 模型配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI


class ModelConfigurationError(RuntimeError):
    """模型配置不完整或不合法。"""


@dataclass(frozen=True)
class ModelSettings:
    """阿里云百炼 OpenAI 兼容接口配置。"""

    model: str
    base_url: str
    api_key: str
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "ModelSettings":
        """从环境变量读取密钥和可选模型参数。"""
        api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            raise ModelConfigurationError(
                "没有找到 DASHSCOPE_API_KEY。请先在 PowerShell 中设置阿里云百炼 API Key。"
            )

        return cls(
            model=os.getenv("DASHSCOPE_MODEL", "qwen3-8b"),
            base_url=os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            api_key=api_key,
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0")),
        )


def create_chat_model(settings: ModelSettings | None = None) -> ChatOpenAI:
    """创建可被 LangGraph bind_tools 使用的 Qwen 云端聊天模型。"""
    config = settings or ModelSettings.from_env()
    return ChatOpenAI(
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=config.temperature,
        timeout=180,
        max_retries=3,
        max_tokens=1024,
        # Qwen3 的 invoke 是非流式调用，必须关闭 thinking 模式。
        extra_body={
            "enable_thinking": False,
        },
    )
