#!/usr/bin/env python
import sys
import json
import uuid
import time
import threading

pending_sampling = {}   # rid -> invoke_id
pending_results = {}    # invoke_id -> result
write_lock = threading.Lock()
DEBUG_PRETTY = "--pretty" in sys.argv
def log_error(msg):
    """安全地将日志输出到 stderr，绝不污染 stdout 的 JSON-RPC 通信流"""
    sys.stderr.write(f"[Tool Log] {msg}\n")
    sys.stderr.flush()

def handle_initialize(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2.0",
            "serverInfo": {
                "name": "tool-dev-notes-summarizer",
                "version": "1.0.0"
            },
            "capabilities": {
                "sampling": {}
            },
        }
    }
def handle_describe():
    return {
        "name": "tool-dev-notes-summarizer",
        "display_name": "Notes Summarizer",
        "version": "1.0.0",
        "description": "Summarize user notes into structured LLM-generated insights.",
        
        "host_capabilities": ["llm.sample"],
        "category": "productivity",

        # ⭐ Executa tools
        "tools": [
            {
                "name": "tool-dev-notes-summarizer",
                "description": "Summarize a list of notes into a concise overview.",
                "timeout": 60,
                "streaming": False,

                # ⭐ 重点：parameters（不是 input_schema）
                "parameters": [
                    {
                        "name": "notes",
                        "type": "array",
                        "description": "List of note strings to summarize.",
                        "required": True,
                        "items": {
                            "type": "string"
                        }
                    }
                ]
            }
        ],

        # ⭐ runtime 必须有
        "runtime": {
            "type": "python",
            "min_version": "3.10"
        }
    }

def handle_invoke(params):
    invoke_id = params.get("context", {}).get("invoke_id")
    if not invoke_id:
        invoke_id = str(uuid.uuid4())

    notes = params.get("arguments", {}).get("notes", [])

    # ⭐ 关键：触发 sampling
    send_sampling(invoke_id, notes)

    # 等待结果
    for i in range(150):
        if invoke_id in pending_results:
            return {
                "success": True,
                "data": {
                    "summary": pending_results.pop(invoke_id)
                }
            }
        time.sleep(0.1)

    # ⭐ fallback
    pending_sampling.pop(invoke_id, None)

    return {
        "success": True,
        "data": {
            "summary": "未获取到模型结果，请稍后重试"
        }
    }
def handle_health():
    return {
        "status": "ready",
        "message": "ok",
        "details": {}
    }

def handle_shutdown():
    log_error("shutdown received")
    return {
        "success": True
    }

def write_json(msg):
    with write_lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()

def send_sampling(invoke_id, notes):
    rid = str(uuid.uuid4())

    pending_sampling[rid] = invoke_id

    prompt = "请对以下笔记进行结构化总结：\n" + "\n".join(notes)

    write_json({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "sampling/createMessage",
        "params": {
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": prompt
                }
            }],
            "maxTokens": 400,
            "includeContext": "none",
            "metadata": {
                "executa_invoke_id": invoke_id
            }
        }
    })
    log_error(f"SEND sampling rid={rid} invoke={invoke_id}")

def run_invoke(rpc_id, params):
    response = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "result": handle_invoke(params)
    }
    write_json(response)

def handle_sampling_response(msg):
    if "error" in msg:
        log_error(f"SAMPLING ERROR: {msg['error']}")
        return
    rid = msg.get("id")
    log_error(f"RECV sampling rid={rid} OK")

    invoke_id = pending_sampling.pop(rid, None)
    if not invoke_id:
        log_error(f"unknown rid={rid}")
        return
    log_error(f"rid={rid} pending={list(pending_sampling.keys())}")
    result = msg.get("result") or {}

    content = result.get("content") or {}

    # 官方标准：content = {type:"text", text:"..."}
    if isinstance(content, dict):
        text = content.get("text", "")
    else:
        text = ""

    pending_results[invoke_id] = text

def safe_parse(line):
    try:
        msg = json.loads(line)
    except Exception:
        log_error(f"Non-JSON input: {line}")
        return None

    # ⭐ 关键：二次 JSON decode（防 double encode）
    if isinstance(msg, str):
        try:
            msg = json.loads(msg)
        except Exception:
            log_error(f"Double-encoded string: {msg}")
            return None

    return msg
def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        msg = safe_parse(line)
        if not isinstance(msg, dict):
            continue

        # ✅ 1. reverse RPC response（sampling 返回）
        if "method" not in msg:
            handle_sampling_response(msg)
            continue

        rpc_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})

        response = {"jsonrpc": "2.0", "id": rpc_id}

        if method == "initialize":
            response["result"] = handle_initialize(rpc_id)

        elif method == "describe":
            response["result"] = handle_describe()

        elif method == "invoke":
            threading.Thread(
                target=run_invoke,
                args=(rpc_id, params),
                daemon=True
            ).start()
            continue

        elif method == "health":
            response["result"] = handle_health()

        elif method == "shutdown":
            response["result"] = handle_shutdown()
            write_json(response)
            break

        else:
            response["error"] = {
                "code": -32601,
                "message": f"Method not found: {method}"
            }

        write_json(response)

if __name__ == "__main__":
    main()
