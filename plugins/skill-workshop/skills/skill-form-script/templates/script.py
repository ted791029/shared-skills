# /// script
# requires-python = "{{python_version_spec}}"
# dependencies = [
#   # 重複開始：每個第三方依賴一行
#   "{{dependency_spec}}",
#   # 重複結束
# ]
# ///
"""{{script_summary}}"""

import argparse
import sys
# 重複開始：每個額外的 import 一行
{{import_statement}}
# 重複結束


# 重複開始：每個輔助函式一組
def {{function_signature}}:
    {{function_body}}
# 重複結束


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="{{script_summary}}")
    # 重複開始：每個命令列參數一行
    parser.add_argument({{argument_spec}}, help="{{argument_help}}")
    # 重複結束
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    {{main_logic}}
    return 0


if __name__ == "__main__":
    sys.exit(main())
