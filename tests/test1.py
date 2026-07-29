from pprint import pprint

from backend.tools import (
    analyze_sales,
    check_data_quality,
    load_dataset,
)

file_path = r"D:\AAAAA\实习\LLM实习准备\superstoredataset.csv"

print("一、文件结构")
pprint(
    load_dataset.invoke(
        {
            "file_path": file_path,
            "preview_rows": 5,
        }
    )
)

print("\n二、数据质量")
pprint(
    check_data_quality.invoke(
        {
            "file_path": file_path,
        }
    )
)

print("\n三、经营分析")
pprint(
    analyze_sales.invoke(
        {
            "file_path": file_path,
            "sales_column": "Sales",
            "profit_column": "Profit",
            "group_column": "Region",
            "top_n": 5,
        }
    )
)