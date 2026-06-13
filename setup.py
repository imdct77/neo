#!/usr/bin/env python3
"""
Neo V1 — 설치 자동화 스크립트
실행: python3 setup.py

새 프로젝트에 Neo V1을 설치하고 {플레이스홀더}를 자동으로 채운다.
실행 후 "NEO, 시작해줘"로 바로 시작할 수 있다.
"""

import os
import shutil
import sys
import textwrap
from pathlib import Path

def _detect_github_user():
    """gh CLI나 git config에서 GitHub 사용자명 감지"""
    import subprocess as _sp
    try:
        r = _sp.run(["gh", "api", "user", "--jq", ".login"],
                    capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    try:
        r = _sp.run(["git", "config", "github.user"],
                    capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None

def _detect_git_identity():
    """git config에서 user.name, user.email 감지"""
    import subprocess as _sp
    name = email = None
    try:
        r = _sp.run(["git", "config", "user.name"], capture_output=True, text=True)
        if r.returncode == 0:
            name = r.stdout.strip()
    except Exception:
        pass
    try:
        r = _sp.run(["git", "config", "user.email"], capture_output=True, text=True)
        if r.returncode == 0:
            email = r.stdout.strip()
    except Exception:
        pass
    return name, email

# ============================================================
# 설정
# ============================================================
NEO_ROOT = Path(__file__).parent          # 이 스크립트가 있는 디렉토리
HOME = Path.home()
HERMES_DIR = HOME / ".hermes"

PLACEHOLDER_FILES = [
    "SOUL.md",
    "AGENTS.md",
    ".hermes.md",
    "orchestrator.md",
]

STACK_OPTIONS = {
    "backend": [
        ("1", "Python + FastAPI"),
        ("2", "Python + Django"),
        ("3", "Node.js + Express"),
        ("4", "Node.js + NestJS"),
        ("5", "Go + Gin"),
        ("6", "직접 입력"),
    ],
    "frontend": [
        ("1", "Next.js + TypeScript"),
        ("2", "React + TypeScript (Vite)"),
        ("3", "Vue.js + TypeScript"),
        ("4", "SvelteKit"),
        ("5", "없음 (API 서버만)"),
        ("6", "직접 입력"),
    ],
    "database": [
        ("1", "PostgreSQL"),
        ("2", "MySQL"),
        ("3", "SQLite (개발용)"),
        ("4", "MongoDB"),
        ("5", "직접 입력"),
    ],
}

# ============================================================
# 유틸
# ============================================================

BOLD  = "\033[1m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

def p(msg, color=""):
    print(f"{color}{msg}{RESET}")

def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{CYAN}{prompt}{suffix}: {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)
    return val or default

def choose(label, options):
    p(f"\n{label}", BOLD)
    for key, name in options:
        print(f"  {key}. {name}")
    while True:
        choice = ask("선택")
        for key, name in options:
            if choice == key:
                if key == "6" or key == str(len(options)):
                    return ask("직접 입력")
                return name
        p("올바른 번호를 입력해주세요.", RED)

def replace_in_file(file_path: Path, replacements: dict):
    if not file_path.exists():
        return
    content = file_path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        content = content.replace(old, new)
    file_path.write_text(content, encoding="utf-8")

def generate_project_id(project_name: str) -> str:
    """PROJECT_NAME을 kebab-case 소문자 PROJECT_ID로 자동 변환.
    
    예) "My Recipe App" → "my-recipe-app"
        "JGBG Platform" → "jgbg-platform"
    """
    import re
    # 소문자로 변환
    pid = project_name.lower()
    # 영문·숫자·공백·하이픈 외 문자 제거
    pid = re.sub(r"[^a-z0-9\s\-]", "", pid)
    # 공백을 하이픈으로
    pid = re.sub(r"\s+", "-", pid.strip())
    # 연속 하이픈 정리
    pid = re.sub(r"-+", "-", pid)
    return pid

# ============================================================
# 메인 흐름
# ============================================================

def main():
    p("\n" + "=" * 55, BOLD)
    p("  Neo V1 — 새 프로젝트 설치 스크립트", BOLD)
    p("=" * 55, BOLD)
    p("\nNeo V1을 이 프로젝트에 설치합니다.")
    p("완료 후 'NEO, 시작해줘'로 바로 시작할 수 있습니다.\n")

    # --------------------------------------------------------
    # Step 1. 프로젝트 정보 수집
    # --------------------------------------------------------
    p("── Step 1. 프로젝트 정보 ──", BOLD)

    project_name = ask("서비스명 (예: MyApp)")
    if not project_name:
        p("서비스명은 필수입니다.", RED)
        sys.exit(1)

    # PROJECT_ID 자동 생성 및 확인
    project_id = generate_project_id(project_name)
    p(f"\n자동 생성된 PROJECT_ID: {BOLD}{project_id}{RESET}", CYAN)
    p("  (mem0 기록의 접두사로 사용됩니다. 프로젝트 생성 후 변경 불가)", YELLOW)
    custom_id = ask(f"다른 ID를 사용하시겠습니까? (Enter = '{project_id}' 사용)")
    if custom_id:
        import re
        # 입력값 검증: kebab-case만 허용
        if re.match(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$", custom_id) or re.match(r"^[a-z0-9]$", custom_id):
            project_id = custom_id
            p(f"  PROJECT_ID: {project_id}", GREEN)
        else:
            p(f"  유효하지 않은 형식입니다 (소문자 영문·숫자·하이픈만 허용). '{project_id}'를 사용합니다.", YELLOW)

    project_desc = ask("한 줄 포지셔닝 (예: 요리 레시피 공유 플랫폼)")
    target_user  = ask("타겟 사용자 (예: 요리를 즐기는 20-40대)")
    mvp_goal     = ask("MVP 목표 (예: 2026년 9월 베타 출시)")

    # --------------------------------------------------------
    # Step 2. 기술 스택 선택
    # --------------------------------------------------------
    p("\n── Step 2. 기술 스택 ──", BOLD)

    backend  = choose("백엔드 스택", STACK_OPTIONS["backend"])
    frontend = choose("프론트엔드 스택", STACK_OPTIONS["frontend"])
    database = choose("데이터베이스", STACK_OPTIONS["database"])

    # --------------------------------------------------------
    # Step 3. Git 레포 설정
    # --------------------------------------------------------
    p("\n── Step 3. Git 레포지토리 ──", BOLD)

    cwd = Path.cwd()
    is_git = (cwd / ".git").is_dir()

    if not is_git:
        p("현재 디렉토리가 Git 레포지토리가 아닙니다.", YELLOW)
        auto = ask("GitHub에 새 레포를 만들어 clone할까요? (y/n/직접입력)", "y")
        if auto.lower() == "y":
            github_user = _detect_github_user()
            if not github_user:
                p("  GitHub 사용자명을 감지할 수 없습니다.", RED)
                p("  gh auth login 후 다시 시도하거나, 직접입력(n)을 선택하세요.", YELLOW)
                return
            repo_name = ask(f"레포 이름 (Enter = {project_id})", project_id)
            p(f"  Creating {github_user}/{repo_name}...", CYAN)
            import subprocess as _sp
            result = _sp.run(
                ["gh", "repo", "create", f"{github_user}/{repo_name}", "--private",
                 "--description", project_desc or project_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                clone_url = f"https://github.com/{github_user}/{repo_name}.git"
                # Clone into parent's ./{repo_name}/
                target = cwd.parent / repo_name
                _sp.run(["git", "clone", clone_url, str(target)], check=True)
                p(f"  ✓ https://github.com/{github_user}/{repo_name}", GREEN)
                p(f"  cd {target} 에서 다시 실행하거나, 지금 경로에 계속 설치합니다.", YELLOW)
                # Continue with cwd — user might want to install here anyway
            else:
                p(f"  ❌ 레포 생성 실패: {result.stderr.strip()}", RED)
                p("  git init 으로 로컬 레포를 대신 만듭니다.", YELLOW)
                _sp.run(["git", "init"], cwd=str(cwd), check=True)
        elif auto.lower() == "직접입력" or auto.lower() == "n":
            clone_url = ask("Git clone URL (Enter = git init)")
            if clone_url:
                _sp.run(["git", "clone", clone_url, str(cwd)], check=True)
                p(f"  ✓ cloned", GREEN)
            else:
                _sp.run(["git", "init"], cwd=str(cwd), check=True)
                p("  ✓ git init", GREEN)
    else:
        p(f"✓ Git 레포 확인됨: {cwd}", GREEN)
        # Configure identity if not set
        import subprocess as _sp2
        try:
            _sp2.run(["git", "config", "user.name"], cwd=str(cwd), capture_output=True, check=True)
        except Exception:
            name, email = _detect_git_identity()
            if name:
                _sp2.run(["git", "config", "user.name", name], cwd=str(cwd))
            if email:
                _sp2.run(["git", "config", "user.email", email], cwd=str(cwd))

    # --------------------------------------------------------
    # Step 4. 설치 경로 확인
    # --------------------------------------------------------
    p(f"프로젝트 루트: {cwd}")
    p(f"Hermes 전역:   {HERMES_DIR}")

    confirm = ask("\n이 경로에 설치할까요? (y/n)", "y")
    if confirm.lower() != "y":
        p("설치를 취소했습니다.", YELLOW)
        sys.exit(0)

    # --------------------------------------------------------
    # Step 5. 파일 복사 (프로젝트 루트)
    # --------------------------------------------------------
    p("\n── Step 5. 파일 설치 중... ──", BOLD)

    # SOUL.md → ~/.hermes/SOUL.md (전역)
    HERMES_DIR.mkdir(parents=True, exist_ok=True)
    soul_src = NEO_ROOT / "SOUL.md"
    soul_dst = HERMES_DIR / "SOUL.md"
    if soul_dst.exists():
        overwrite = ask("~/.hermes/SOUL.md가 이미 존재합니다. 덮어쓸까요? (y/n)", "n")
        if overwrite.lower() == "y":
            shutil.copy2(soul_src, soul_dst)
            p("  ✓ SOUL.md 갱신", GREEN)
        else:
            p("  ⚠ SOUL.md 건너뜀 (기존 유지)", YELLOW)
    else:
        shutil.copy2(soul_src, soul_dst)
        p("  ✓ SOUL.md → ~/.hermes/SOUL.md", GREEN)

    # 프로젝트 루트 파일 복사
    root_files = [".hermes.md", "AGENTS.md"]
    for fname in root_files:
        src = NEO_ROOT / fname
        dst = cwd / fname
        if src.exists():
            shutil.copy2(src, dst)
            p(f"  ✓ {fname}", GREEN)

    # docs/ 디렉토리 복사
    docs_dst = cwd / "docs"
    docs_dst.mkdir(exist_ok=True)

    # src/ 소스 디렉토리 생성
    for subdir in ["src/be", "src/fe"]:
        (cwd / subdir).mkdir(parents=True, exist_ok=True)
    p("  ✓ src/be/, src/fe/ (하위 구조는 프로젝트 자유)", GREEN)

    doc_files = [
        ("personas/orchestrator.md", "orchestrator.md"),
        ("personas/architect.md", "architect.md"),
        ("personas/backend.md", "backend.md"),
        ("personas/frontend.md", "frontend.md"),
        ("works/workflow.md", "workflow.md"),
        ("works/task_brief_templ.md", "task_brief_templ.md"),
        ("works/tasks_templ.md", "tasks_templ.md"),
        ("works/tests_templ.md", "tests_templ.md"),
    ]
    for src_rel, dst_name in doc_files:
        src = NEO_ROOT / src_rel
        dst = docs_dst / dst_name
        if src.exists():
            shutil.copy2(src, dst)
            p(f"  ✓ docs/{dst_name}", GREEN)

    # skills/ — 배포 시 복사하지 않고 루트에 유지 (2026-06-12 통일 결정)

    # .neo_state.json 초기화 (§6-6)
    import json as json_module
    from datetime import datetime as _dt

    state_dir = NEO_ROOT / "state"
    state_dir.mkdir(exist_ok=True)
    state_file = state_dir / ".neo_state.json"
    if not state_file.exists():
        initial_state = {
            "project_id": project_id,
            "project_name": project_name,
            "current_phase": "-1",
            "current_domain": None,
            "current_task_id": None,
            "task_status": "none",
            "phase_history": [],
            "valid_transitions": {
                "from_current": ["start_design"]
            },
            "last_updated": _dt.now().isoformat()
        }
        with open(state_file, "w") as f:
            json_module.dump(initial_state, f, ensure_ascii=False, indent=2)
        p(f"  ✓ .neo_state.json 초기화 (PROJECT_ID: {project_id})", GREEN)

    # project.json 초기화 (§13)
    project_json_path = NEO_ROOT / "project.json"
    github_user = _detect_github_user() or "your-github-username"
    project_data = {
        "project_id": project_id,
        "project_name": project_name,
        "github_user": github_user,
        "git": {
            "project": "{PROJECT_REPO_URL}"
        }
    }
    with open(project_json_path, "w") as f:
        json_module.dump(project_data, f, ensure_ascii=False, indent=2)
    p(f"  ✓ project.json 초기화", GREEN)

    # --------------------------------------------------------
    # Step 6. 플레이스홀더 치환
    # --------------------------------------------------------
    p("\n── Step 6. 플레이스홀더 치환 중... ──", BOLD)

    replacements = {
        "{PROJECT_NAME}": project_name,
        "{PROJECT_ID}": project_id,
        "{GITHUB_USER}": github_user,
    }

    # SOUL.md (전역)
    replace_in_file(soul_dst, replacements)
    p(f"  ✓ SOUL.md — PROJECT_NAME → {project_name}", GREEN)

    # .hermes.md (프로젝트 루트) — PROJECT_ID + PROJECT_NAME 치환
    replace_in_file(cwd / ".hermes.md", replacements)
    p(f"  ✓ .hermes.md — PROJECT_ID → {project_id}, PROJECT_NAME → {project_name}", GREEN)

    # project.json — placeholder 치환
    replace_in_file(project_json_path, replacements)
    p(f"  ✓ project.json — PROJECT_ID → {project_id}, PROJECT_NAME → {project_name}", GREEN)

    # AGENTS.md
    agents_path = cwd / "AGENTS.md"
    replace_in_file(agents_path, {
        **replacements,
        "- **서비스명**: {서비스명}": f"- **서비스명**: {project_name}",
        "- **포지셔닝**: {한 줄 포지셔닝 — 무엇을 위한 서비스인가}":
            f"- **포지셔닝**: {project_desc}",
        "- **MVP 목표**: {목표일 또는 MVP 완성 기준}":
            f"- **MVP 목표**: {mvp_goal}",
        "- **핵심 루프**: {사용자가 반복하는 핵심 행동 3~5단계}":
            f"- **타겟 사용자**: {target_user}",
        "| 백엔드 | {예: Python + FastAPI} | {버전} |":
            f"| 백엔드 | {backend} | - |",
        "| 프론트엔드 | {예: Next.js + TypeScript} | {버전} |":
            f"| 프론트엔드 | {frontend} | - |",
        "| DB | {예: PostgreSQL} | {버전} |":
            f"| DB | {database} | - |",
    })
    p(f"  ✓ AGENTS.md — 프로젝트 정보·기술스택 채움", GREEN)

    # orchestrator.md
    replace_in_file(
        docs_dst / "orchestrator.md",
        {**replacements,
         "나는 **{PROJECT_NAME} 구현을 총괄하는 Orchestrator NEO(네오)**다.":
             f"나는 **{project_name} 구현을 총괄하는 Orchestrator NEO(네오)**다.",
         "- {PROJECT_NAME} 서비스 전체 목적과 MVP 범위":
             f"- {project_name} 서비스 전체 목적과 MVP 범위"},
    )
    p(f"  ✓ orchestrator.md — PROJECT_NAME, PROJECT_ID 치환", GREEN)

    # --------------------------------------------------------
    # Step 7. Hooks 설치 (선택)
    # --------------------------------------------------------
    p("\n── Step 7. Hooks 설치 (선택) ──", BOLD)
    p("Hooks는 실행 강제력을 95% 수준으로 높입니다.")

    install_hooks = ask("\nHermes Hooks를 설치할까요? (y/n)", "y")
    if install_hooks.lower() == "y":
        neo_hooks_dst = HERMES_DIR / "neo-hooks"
        neo_hooks_dst.mkdir(parents=True, exist_ok=True)

        hook_files = [
            "forbidden-check.py",
            "auto-test.py",
            "context-inject.py",
            "session-start.py",
            "meta_consistency_check.py",
        ]
        hooks_src = NEO_ROOT / "hooks"
        copied = 0
        for fname in hook_files:
            src = hooks_src / fname
            if src.exists():
                shutil.copy2(src, neo_hooks_dst / fname)
                (neo_hooks_dst / fname).chmod(0o755)
                copied += 1

        if copied > 0:
            p(f"  ✓ Hermes Hook 스크립트 {copied}개 → ~/.hermes/neo-hooks/", GREEN)
        else:
            p("  ⚠ hooks/*.py 파일을 찾을 수 없습니다.", YELLOW)

        p("\n⚠️  config.yaml을 덮어쓰지 않습니다.", YELLOW)
        p("   Hook 설정을 config.yaml에 직접 추가하세요:", YELLOW)
        p("   hermes config edit", BOLD)

    install_git = ask("Git pre-commit Hook을 설치할까요? (y/n)", "y")
    if install_git.lower() == "y":
        git_dir = cwd / ".git" / "hooks"
        if not git_dir.exists():
            p("  ⚠ .git 디렉토리를 찾을 수 없습니다. 'git init'을 먼저 실행해주세요.", YELLOW)
        else:
            # 프로젝트 repo용 경량 프록시: harness의 meta 체크 호출
            proxy_script = textwrap.dedent("""\
                #!/usr/bin/env bash
                # Neo pre-commit 프록시 — harness meta 체크 호출
                HARNESS_DIR="../harness"
                CHECK_SCRIPT="$HARNESS_DIR/hooks/meta_consistency_check.py"
                if [ ! -f "$CHECK_SCRIPT" ]; then
                    exit 0
                fi
                HARNESS_ABS="$(cd "$HARNESS_DIR" && pwd)"
                NEO_HARNESS_ROOT="$HARNESS_ABS" \\
                  PYTHONPATH="$HARNESS_ABS/hooks" \\
                  python3 "$CHECK_SCRIPT" --exit-code --sync
                exit $?
            """)
            dst = git_dir / "pre-commit"
            dst.write_text(proxy_script)
            dst.chmod(0o755)
            p("  ✓ Git pre-commit Hook 설치 완료 (프록시)", GREEN)

    # --------------------------------------------------------
    # Step 8. 완료 안내
    # --------------------------------------------------------
    p("\n" + "=" * 55, GREEN)
    p("  Neo V1 설치 완료!", GREEN + BOLD)
    p("=" * 55, GREEN)
    p(f"\n  프로젝트: {project_name}")
    p(f"  PROJECT_ID: {project_id}")
    p(f"  백엔드:   {backend}")
    p(f"  프론트:   {frontend}")
    p(f"  DB:       {database}")
    p(f"\n  설치 위치:")
    p(f"    ~/.hermes/SOUL.md")
    p(f"    {cwd}/.hermes.md")
    p(f"    {cwd}/AGENTS.md")
    p(f"    {cwd}/docs/")
    p(f"\n  다음 단계:")
    p(f"    1. .hermes.md에 Omission Constraints를 작성하세요")
    p(f"       (이 프로젝트의 절대 금지선 — 가장 중요)")
    p(f"    2. Hermes에서 'NEO, 시작해줘'")
    p(f"    → NEO가 아이디어 구체화부터 안내합니다.\n")


if __name__ == "__main__":
    main()
