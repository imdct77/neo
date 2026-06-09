#!/usr/bin/env python3
"""Neo context-inject hook — 매 LLM 호출 전 금지선 복원."""
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
    hm = os.path.join(root, '.hermes.md')
    if not os.path.exists(hm): return
    with open(hm) as f:
        text = f.read()
    constraints = []
    in_sec = False
    for line in text.split('\n'):
        if '절대 금지' in line or 'Omission Constraint' in line:
            in_sec = True; continue
        if in_sec and line.startswith('##'): break
        if in_sec and line.strip().startswith('- '):
            item = line.strip()[2:]
            if item and not item.startswith('{'): constraints.append(item)
    if not constraints: return
    constraints = constraints[:7]
    pn = ""
    am = os.path.join(root, 'AGENTS.md')
    if os.path.exists(am):
        with open(am) as f:
            m = re.search(r'\*\*서비스명\*\*:\s*(.+)', f.read())
            if m: pn = m.group(1).strip()
    ctx = f"[{pn or 'Neo'}] Omission Constraints (위반 금지):\n"
    for i, c in enumerate(constraints, 1): ctx += f"  {i}. {c}\n"
    print(json.dumps({"context": ctx}))

if __name__ == "__main__":
    main()
