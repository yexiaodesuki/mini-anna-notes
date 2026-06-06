#!/usr/bin/env python
import sys
import json
DEBUG_PRETTY = "--pretty" in sys.argv
def log_error(msg):
    """安全地将日志输出到 stderr，绝不污染 stdout 的 JSON-RPC 通信流"""
    sys.stderr.write(f"[Tool Log] {msg}\n")
    sys.stderr.flush()

def handle_describe():
    """实现 describe 方法：返回符合 Anna 规约的工具元数据描述"""
    return {
        "name": "tool-dev-notes-summarizer",
        "description": "A rule-driven local notes summarizer that classifies and counts task categories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {
                    "type": "array",
                    "description": "List of strings representing the captured notes.",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["notes"]
        }
    }

def handle_invoke(params):
    notes = params.get("arguments", {}).get("notes", [])

    total_count = len(notes)

    if total_count == 0:
        return {
            "success": True,
            "data": {
                "summary": "当前没有任何待处理的笔记。请输入内容并保存后重试。"
            }
        }

    categories_map = {
        "开发": ["bug", "fix", "修复", "代码", "开发", "测试", "系统", "功能"],
        "协作": ["沟通", "客户", "设计", "会议", "follow up", "对接", "讨论", "谈谈"],
        "内容准备": ["提纲", "想法", "workshop", "思考", "文档", "准备", "ppt", "结构"]
    }

    detected_categories = set()

    for note in notes:
        note_lower = note.lower()
        matched = False

        for category, keywords in categories_map.items():
            if any(keyword in note_lower for keyword in keywords):
                detected_categories.add(category)
                matched = True

        if not matched:
            detected_categories.add("日常事务")

    order = ["开发", "协作", "内容准备", "日常事务"]
    sorted_categories = [cat for cat in order if cat in detected_categories]

    if len(sorted_categories) == 1:
        categories_str = sorted_categories[0]
    elif len(sorted_categories) == 2:
        categories_str = " 和 ".join(sorted_categories)
    else:
        categories_str = "、".join(sorted_categories[:-1]) + " 和 " + sorted_categories[-1]

    summary_text = (
        f"当前共有 {total_count} 条待处理事项，主要集中在{categories_str}。"
    )

    return {
        "success": True,
        "data": {
            "summary": summary_text
        }
    }

def main():
    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        rpc_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        response = {
            "jsonrpc": "2.0",
            "id": rpc_id
        }

        if method == "describe":
            response["result"] = handle_describe()

        elif method == "invoke":
            response["result"] = handle_invoke(params)

        else:
            response["error"] = {
                "code": -32601,
                "message": f"Method not found: {method}"
            }

        if DEBUG_PRETTY:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, indent=2) + "\n")
        else:
            sys.stdout.write(json.dumps(response) + "\n")

        sys.stdout.flush()

if __name__ == "__main__":
    main()