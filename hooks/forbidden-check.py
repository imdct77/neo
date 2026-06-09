#!/usr/bin/env python3
"""Neo forbidden-check hook — Hermes shell-script 호환 버전.
stdin에서 JSON payload 읽음 → 금지 패턴 검사 → stdout으로 결과 출력.
"""
import sys, json, re

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    tool_name = payload.get("tool_name", "")
    if tool_name not in ("write_file", "patch", "terminal"):
        return
    args = payload.get("arguments", {})
    scan_text = args.get("content", "") or args.get("command", "")
    if not scan_text:
        return
    CRITICAL = {
        "JWT 검증 우회": (r"verify_signature\s*=\s*False", r"verify\s*=\s*False", r"skip.*auth", r"bypass.*auth"),
        "비밀번호 평문": (r"password\s*=\s*['\"]\\w{4,}['\"]",),
        "하드코딩 시크릿": (r"SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]", r"API_KEY\s*=\s*['\"][^'\"]{8,}['\"]"),
        "SSL 검증 비활성화": (r"verify\s*=\s*False",),
        "localStorage 토큰": (r"localStorage\.setItem\(['\"]token", r"localStorage\.setItem\(['\"]access"),
    }
    for category, patterns in CRITICAL.items():
        for pat in patterns:
            if re.search(pat, scan_text, re.IGNORECASE):
                print(json.dumps({"decision": "block", "reason": f"[Neo] 금지 패턴: {category}"}))
                return

if __name__ == "__main__":
    main()
