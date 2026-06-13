# COMMITS.md — 커밋 메시지 컨벤션

> 이 파일은 AGENTS.md §8-1에서 분리된 커밋 메시지 규칙입니다.
> 커밋 작성 시 로드합니다.

## 기본 형식

```
{type}: {한 줄 요약 — 명령형·독립형, 50자 이내}

{본문 — 왜 변경했는지. diff를 읽지 않아도 정보를 제공해야 한다}
{필요 시: Task ID·ADR 번호·관련 이슈}
```

## Type 분류

| Type | 용도 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `refactor` | 동작 변경 없는 코드 정리 |
| `docs` | 문서만 변경 |
| `test` | 테스트 추가·수정 |
| `chore` | 빌드·설정·의존성·잡일 |
| `perf` | 성능 개선 |

## 첫 줄 원칙 (First Line Rule)

**명령형, 독립형 (Imperative, self-contained)**
diff를 읽지 않아도 어떤 변경인지 알 수 있어야 한다.
"이 커밋을 적용하면 ~한다"로 읽히는 문장이어야 한다.

## Anti-Pattern — 절대 금지

```
❌ "Fix bug"           → 어떤 버그인지 알 수 없음
❌ "Add patch"         → 무엇을 추가하는지 알 수 없음
❌ "Moving code"       → 왜 옮기는지 알 수 없음
❌ "Update file.py"    → diff를 봐야만 알 수 있음
❌ "Changes" / "WIP"   → 정보 제로
❌ "temp" / "test"     → 실험적 변경은 브랜치에만
```

## 올바른 예

```
✅ fix: JWT 토큰 만료 시 500 대신 401 반환하도록 수정
✅ feat: 레시피 검색에 카테고리 필터 추가 (AUTH.BE.003)
✅ refactor: UserService에서 인증 로직 분리 — 단일 책임 위반 해소
✅ docs: AGENTS.md §8-1 커밋 메시지 컨벤션 추가
```

## 본문 원칙 (Body Rule)

- **WHAT이 아닌 WHY를 설명한다** — 코드가 WHAT을 말해준다. 커밋 메시지는 WHY
- 변경 파일 목록은 `git diff --stat`으로 확인 가능하므로 본문에 나열하지 않는다
- 여러 파일이 변경된 경우, 논리적 그룹으로 묶어 설명한다
- 영문과 한글 혼용 시: 핵심 정보는 한글, type·기술 용어는 영문

## 커밋 단위 (Commit Granularity)

```
한 커밋 = 한 논리적 변경 (One commit, one logical change)
  ❌ 버그 수정 + 리팩토링을 같은 커밋에
  ✅ 버그 수정 커밋 → 리팩토링 커밋 분리
  ✅ 테스트 코드만 별도 커밋 (docs/test 타입)

작업 도중 커밋:
  feat: 중간 저장 — {무엇을 하던 중이었는지}
  (머지 전 squash 예정임을 전제)
```
