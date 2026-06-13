# 인증/인가 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `auth_impl.md` 참조

---

## 인증/인가 레이어 경계

```
FE (Next.js)
    middleware.ts          ← 라우트 보호 (인증 여부 확인)
    useAuthStore           ← 토큰/사용자 정보 클라이언트 보관
    clientFetch            ← 요청마다 Authorization 헤더 첨부

          ↕ HTTP (JWT Bearer Token)

BE (FastAPI)
    get_current_user()     ← 토큰 검증 + 사용자 조회 (공유 의존성)
    Router                 ← Depends(get_current_user)로 보호
    Service                ← 권한 검사 (ForbiddenError)
```

---

## 토큰 흐름

```
로그인 요청
    FE → POST /api/v1/auth/login
    BE → access_token (15분) + refresh_token (7일) 반환

API 요청
    FE → Authorization: Bearer {access_token}
    BE → 토큰 검증 → 유효하면 처리

토큰 만료
    FE → 401 응답 감지 → POST /api/v1/auth/refresh
    BE → refresh_token 검증 → 새 access_token 반환
    FE → 원래 요청 재시도

로그아웃
    FE → refresh_token 삭제 (클라이언트)
    BE → refresh_token 블랙리스트 추가 (선택)
```

---

## 인가 설계 기준

역할 기반 접근 제어(RBAC) 적용:

```
역할: ADMIN > MANAGER > USER
권한 검사 위치: Service 레이어
Router에서 권한 검사 금지 (비즈니스 로직이 Router에 누출됨)
```

---

## Task 분리 기준

| 작업 | 위치 | 선행 조건 |
|------|------|---------|
| JWT 생성/검증 유틸 | `core/auth.py` | 없음 (선행) |
| 로그인/토큰 갱신 API | `auth/router.py` | core/auth 완료 후 |
| get_current_user 의존성 | `core/dependencies.py` | auth router 완료 후 |
| FE 미들웨어 | `middleware.ts` | BE 인증 API 완료 후 |
| FE auth store | `stores/useAuthStore.ts` | 없음 (FE 선행) |

---

## 주의: 설계에서 자주 발생하는 실수

- access_token을 localStorage에 저장 → XSS 공격으로 탈취 가능 (sessionStorage 사용)
- refresh_token을 localStorage에 저장 → httpOnly 쿠키 사용 권장
- FE middleware에서만 인증 확인 → API Route Handler는 여전히 노출됨
- 토큰 만료 처리 없이 401만 반환 → 사용자가 갑자기 로그아웃됨
