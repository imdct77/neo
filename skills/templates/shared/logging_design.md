# 로깅 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `logging_impl.md` 참조

---

## 로그 레벨 기준

| 레벨 | 사용 상황 | 예시 |
|------|---------|------|
| DEBUG | 개발 시 상세 추적. 프로덕션 비활성화 | 쿼리 파라미터, 함수 진입/퇴장 |
| INFO | 정상 비즈니스 이벤트 | 사용자 가입, 주문 생성, 로그인 성공 |
| WARNING | 비정상이지만 서비스 지속 가능 | 존재하지 않는 리소스 접근, 재시도 발생 |
| ERROR | 처리 실패. 즉각 대응 불필요 | 외부 API 오류, DB 쿼리 실패 |
| CRITICAL | 서비스 중단 가능성. 즉각 알림 필요 | DB 연결 불가, 디스크 풀 |

---

## 구조화 로깅 설계

모든 로그는 JSON 형태로 출력한다. 평문 로그는 검색·집계가 불가능하다.

```json
{
  "timestamp": "2026-06-11T10:00:00Z",
  "level": "INFO",
  "event": "order.created",
  "user_id": 123,
  "order_id": 456,
  "trace_id": "abc-123",
  "service": "order-service"
}
```

**필수 필드**: timestamp, level, event, trace_id  
**선택 필드**: user_id, resource_id, duration_ms, error_code

---

## 민감 정보 로깅 금지

로그에 절대 포함하지 않는 것:
- 비밀번호, 해시된 비밀번호
- 신용카드 번호, CVV
- JWT 토큰 전체 (마지막 4자리만 허용)
- 주민등록번호, 여권번호

---

## Task 분리 기준

| 작업 | 위치 | 선행 조건 |
|------|------|---------|
| 로깅 설정 | `core/logging.py` | 없음 (선행) |
| 요청 추적 미들웨어 | `core/middleware.py` | 로깅 설정 후 |
| 도메인 이벤트 로그 | 각 Service | 로깅 설정 후 |
