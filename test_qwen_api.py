"""在运行 LangGraph 前，单独验证阿里云百炼 API。"""

from backend.agent.config import ModelConfigurationError, create_chat_model


def main() -> None:
    try:
        model = create_chat_model()
    except ModelConfigurationError as exc:
        raise SystemExit(f"配置失败：{exc}") from exc

    response = model.invoke("只回复：阿里云 Qwen API 连接成功")
    print(response.content)


if __name__ == "__main__":
    main()
