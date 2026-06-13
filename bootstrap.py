#!/usr/bin/env python3
"""
Neo Bootstrap — HARNESS_ROOT 자동 감지

사용자가 어디에 Neo를 설치하든, 이 파일의 물리적 위치(__file__)로
HARNESS_ROOT와 NEO_ROOT를 결정한다.

실행:
    python bootstrap.py
    source <(python bootstrap.py --export)  # env 주입용

사용법:
    from bootstrap import HARNESS_ROOT, NEO_ROOT  # import 방식
"""

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent  # .../neo/harness/
HARNESS_ROOT = _HERE
NEO_ROOT = _HERE.parent                  # .../neo/


def setup_env():
    """세션 환경에 HARNESS_ROOT, NEO_ROOT 주입"""
    os.environ["HARNESS_ROOT"] = str(HARNESS_ROOT)
    os.environ["NEO_ROOT"] = str(NEO_ROOT)
    return str(HARNESS_ROOT), str(NEO_ROOT)


def export_shell():
    """source <(python bootstrap.py --export) 용"""
    print(f"export HARNESS_ROOT={HARNESS_ROOT}")
    print(f"export NEO_ROOT={NEO_ROOT}")


if __name__ == "__main__":
    if "--export" in sys.argv:
        export_shell()
    else:
        h, n = setup_env()
        print(f"HARNESS_ROOT={h}")
        print(f"NEO_ROOT={n}")
