# DETAIL.user.md — user.py 상세

> 상위: [DETAIL.md](./DETAIL.md) | 디렉토리: [INDEX.md](./INDEX.md)

## 함수 상세

### to_dict() → dict
- **하는 일**: User 객체를 dict로 직렬화 (name, email)
- **호출처**: API 응답, 직렬화 필요 지점
- **실패 시**: 없음 (순수 데이터 변환)
- **중복 금지**: 해당 없음 (프로젝트 유일 User 모델)
- **수정 시 영향**: User 모델 사용하는 모든 API 응답

### validate_email() → bool
- **하는 일**: email 형식 검증 (정규표현식)
- **호출처**: User 생성/수정 시 검증
- **실패 시**: 잘못된 형식 → False 반환
- **중복 금지**: 다른 모델에서 자체 구현 금지 — User.validate_email() 사용
- **수정 시 영향**: email 검증 로직 변경 시 User 생성 흐름 영향

## 상수

| 이름 | 값 | 의미 | 수정 시 영향 |
|------|-----|------|------------|
| (없음) | — | — | — |

## 의존성

### Import
- `re` → 정규표현식 — email 형식 검증

### Imported by
- `src/be/services/auth.py` → User 검증 시 사용 가능성
