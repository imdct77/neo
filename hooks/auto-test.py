#!/usr/bin/env python3
"""Neo auto-test hook — 파일 저장 후 관련 테스트 자동 실행."""
import sys, json, os, subprocess

def find_test(p, root):
    base = os.path.basename(p)
    name = os.path.splitext(base)[0]
    rel_dir = os.path.dirname(os.path.relpath(p, root))
    if p.endswith('.py'):
        for c in [os.path.join(root, 'tests', f'test_{name}.py'),
                  os.path.join(root, 'tests', rel_dir, f'test_{name}.py')]:
            if os.path.exists(c): return c
    if p.endswith(('.ts', '.tsx', '.js', '.jsx')):
        for c in [os.path.join(root, rel_dir, f'{name}.test.ts'),
                  os.path.join(root, '__tests__', f'{name}.test.ts')]:
            if os.path.exists(c): return c
    return None

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if payload.get("tool_name") not in ("write_file", "patch"):
        return
    path = payload.get("arguments", {}).get("path", "")
    if not path: return
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        root = os.getcwd()
    tf = find_test(path, root)
    if not tf: return
    try:
        if path.endswith('.py'):
            r = subprocess.run(
                ["python", "-m", "pytest", tf, "-v", "--tb=short", "-q"],
                capture_output=True, text=True, timeout=60, cwd=root)
            if r.returncode != 0:
                print(json.dumps({"context":
                    f"[Neo Auto-Test] {os.path.basename(tf)} FAIL:\n```\n{r.stdout[-1500:]}\n```"}))
        elif path.endswith(('.ts', '.tsx', '.js', '.jsx')):
            r = subprocess.run(
                ["npx", "vitest", "run", tf, "--reporter=verbose"],
                capture_output=True, text=True, timeout=60, cwd=root)
            if r.returncode != 0:
                print(json.dumps({"context":
                    f"[Neo Auto-Test] {os.path.basename(tf)} FAIL:\n```\n{r.stdout[-1500:]}\n```"}))
    except Exception:
        pass

if __name__ == "__main__":
    main()
