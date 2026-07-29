"""数据工具共用的文件读取与 JSON 序列化逻辑。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def read_dataframe(file_path: str) -> pd.DataFrame:
    """读取 CSV 或 Excel，并给出适合用户理解的错误信息。"""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"数据文件不存在：{path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"不支持 {suffix or '无扩展名'} 文件，仅支持：{supported}")

    try:
        if suffix == ".csv":
            # utf-8-sig 兼容普通 UTF-8 和带 BOM 的中文 CSV。
            return pd.read_csv(path, encoding="utf-8-sig")
        return pd.read_excel(path)
    except UnicodeDecodeError:
        # 国内 Windows 导出的 CSV 常见 GB18030 编码。
        return pd.read_csv(path, encoding="gb18030")
    except Exception as exc:
        raise ValueError(f"读取数据文件失败：{exc}") from exc


def to_json_value(value: Any) -> Any:
    """把 NumPy/Pandas 标量转换为可被 ToolMessage 序列化的 Python 值。"""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value.item() if hasattr(value, "item") else value
