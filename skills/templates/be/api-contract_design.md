# API 계약 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `api-contract_impl.md` 참조

---

## 요청/응답 스키마 설계 원칙

**입력과 출력을 분리한다.**

```
CreateUserRequest  ← 클라이언트 → 서버 입력용
UpdateUserRequest  ← 클라이언트 → 서버 수정용
UserResponse       ← 서버 → 클라이언트 출력용
UserDTO            ← Service 내부 이동용 (HTTP 무관)
```

`UserResponse`와 `UserDTO`를 같은 클래스로 쓰지 않는다.
내부 도메인 객체가 외부 계약(API 응답)에 직접 노출되면
내부 변경이 API 스키마를 깨뜨린다.

---

## 버전 관리 전략

MVP 단계에서는 URL 버전 접두어를 사용한다:
```
/api/v1/users
/api/v1/orders
```

버전 전환 기준:
- 기존 필드 제거 → 반드시 버전 업
- 기존 필드 타입 변경 → 반드시 버전 업
- 신규 필드 추가 (선택적) → 버전 업 불필요
- 신규 엔드포인트 추가 → 버전 업 불필요

---

## 페이지네이션 설계

커서 기반 페이지네이션을 기본으로 사용한다.
오프셋 기반은 데이터가 실시간으로 변하는 목록에서 중복·누락이 발생한다.

```
요청: GET /api/v1/orders?cursor={last_id}&limit=20
응답:
  {
    "items": [...],
    "next_cursor": "{next_id}",
    "has_more": true
  }
```

---

## 공통 응답 구조 설계 기준

성공 응답은 래퍼 없이 직접 반환한다:
```json
// 단건: 객체 직접 반환
{ "id": 1, "email": "user@example.com" }

// 목록: 페이지네이션 메타와 함께
{ "items": [...], "next_cursor": "...", "has_more": true }
```

에러 응답은 통일된 구조 (`error-handling_design.md` 참조):
```json
{ "error_code": "USER_NOT_FOUND", "message": "...", "detail": {} }
```

---

## Task 분리 기준

| 작업 | 위치 | 비고 |
|------|------|------|
| 공통 응답 스키마 | `core/schemas.py` | 선행 Task |
| 도메인 입출력 스키마 | `{domain}/schemas.py` | 도메인 Task |
| 라우터 + 스키마 연결 | `{domain}/router.py` | 스키마 완료 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- 응답에 ORM 모델 직접 노출 → 내부 DB 구조가 외부에 누출됨
- 모든 응답을 `{"success": true, "data": {...}}` 래퍼로 감쌈 → REST 원칙 위반, FE 개발 불편
- 에러와 성공이 같은 HTTP 코드 반환 → FE가 `success` 필드로 분기해야 함
