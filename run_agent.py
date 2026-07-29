"""使用阿里云百炼 Qwen 模型运行 Day 2 Agent。"""

from __future__ import annotations

import argparse
from pathlib import Path

from langchain_core.messages import HumanMessage
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)

from backend.agent.config import ModelConfigurationError, create_chat_model
from backend.agent.graph import build_agent, save_mermaid_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="企业经营数据分析 Agent")
    parser.add_argument("file", help="CSV、XLSX 或 XLS 数据文件路径")
    parser.add_argument("query", help="需要 Agent 回答的业务问题")
    parser.add_argument("--save-graph", default="graph.mmd")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    file_path = Path(args.file).expanduser().resolve()
    if not file_path.is_file():
        raise SystemExit(f"数据文件不存在：{file_path}")

    try:
        model = create_chat_model()
    except ModelConfigurationError as exc:
        raise SystemExit(f"\n模型配置错误：{exc}") from exc

    agent = build_agent(model)
    if args.save_graph:
        graph_path = save_mermaid_graph(agent, args.save_graph)
        print(f"LangGraph 流程图已保存：{graph_path.resolve()}")

    try:
        result = agent.invoke(
            {
                "messages": [HumanMessage(content=args.query)],
                "file_path": str(file_path),
                "llm_calls": 0,
            },
            config={"recursion_limit": 12},
        )
    except AuthenticationError as exc:
        raise SystemExit("\nAPI Key 无效，请重新检查 DASHSCOPE_API_KEY。") from exc
    except PermissionDeniedError as exc:
        raise SystemExit("\n当前 API Key 没有 qwen2.5-14b-instruct 的调用权限。") from exc
    except RateLimitError as exc:
        raise SystemExit("\n阿里云百炼请求限流或账户额度不足，请稍后重试并检查余额。") from exc
    except BadRequestError as exc:
        raise SystemExit(f"\n百炼拒绝了请求参数：{exc}") from exc
    except APITimeoutError as exc:
        raise SystemExit("\n百炼接口在 180 秒内没有响应。") from exc
    except APIConnectionError as exc:
        raise SystemExit("\n无法连接阿里云百炼，请检查网络或代理设置。") from exc
    except InternalServerError as exc:
        raise SystemExit(f"\n阿里云百炼服务端暂时异常：{exc}") from exc

    print("\nAgent 最终回答：")
    print(result["messages"][-1].content)
    print(f"\n模型调用次数：{result['llm_calls']}")


if __name__ == "__main__":
    main()
