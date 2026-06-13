# models/user.py — 상세

## User 클래스
- **용도**: 핵심 사용자 엔티티
- **속성**: `name: str`, `email: str`
- **메서드**: `to_dict()` → `dict`, `validate_email()` → `bool`
- **의존성**: `re` (email 검증)
- **중복 금지**: 자체 email 검증 구현 금지 → `User.validate_email()` 사용

# src/be/models/__init__.py — 상세

## Init

- **용도**: [AUTO] TODO — 자동 생성됨, 검토 필요
- **의존성**: TODO
