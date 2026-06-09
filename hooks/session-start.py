#!/usr/bin/env python3
"""Neo session-start hook — 세션 시작 시 Neo 상태 복원 트리거."""
import sys, json, os, subprocess, re

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        root = os.getcwd()
    ns = os.path.join(root, "docs", "skills", "neo-start.md")
    if not os.path.exists(ns):
        ns = os.path.join(root, "skills", "neo-start.md")
    if not os.path.exists(ns): return
    pn = ""
    am = os.path.join(root, 'AGENTS.md')
    if os.path.exists(am):
        with open(am) as f:
            m = re.search(r'\*\*서비스명\*\*:\s*(.+)', f.read())
            if m: pn = m.group(1).strip()
    ctx = f"""[{pn or ''}] Neo V1 활성화. neo-start.md를 read_file로 읽고 mem0에서 Phase·도메인·LEARN·BADCASE 검색 후 상태 보고하세요.
첫 세션이면 design-init을 제안하세요. neo-start.md: {ns}"""
    print(json.dumps({"context": ctx}))

if __name__ == "__main__":
    main()
