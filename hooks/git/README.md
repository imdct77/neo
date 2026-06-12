# hooks/git/ — Git Hooks

> ⚠️ 이 디렉토리는 **Hermes Shell Hooks가 아닌 Git Hooks**입니다.
> Hermes Hook은 `hooks/*.py` (상위 디렉토리)에 있습니다.

## pre-commit

커밋 전 자동 실행되는 Git Hook. 코드 품질·보안·브랜치 보호 검사를 수행한다.

### 설치

```bash
cp hooks/git/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
