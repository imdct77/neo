# 5. Swiss — 헬베티카 타이포그래픽 (Typographic Purity)

> 출처: `templates/fe/styling_design.md`
> design-init에서 선택된 프리셋만 로드된다.

### 5. Swiss — 헬베티카 타이포그래픽 (Typographic Purity)
272|
273|> 흑·백·빨강만. 타이포그래피가 유일한 장식. 문서 중심·출판에 적합.
274|
275|```
276|Font:     Inter (700 max, bold만 사용, black 금지)
277|Radius:   --radius: 0
278|Shadows:  없음. 모든 시각적 구분은 선·여백·폰트 웨이트로
279|```
280|
281|```css
282|--background: 0 0% 100%;
283|--foreground: 0 0% 0%;
284|--primary: 0 0% 0%;             /* black */
285|--primary-foreground: 0 0% 100%;
286|--secondary: 0 0% 96%;          /* #f4f4f4 */
287|--secondary-foreground: 0 0% 0%;
288|--muted: 0 0% 40%;
289|--muted-foreground: 0 0% 55%;
290|--accent: 0 100% 45%;           /* #e60000 — 유일한 색상 */
291|--accent-foreground: 0 0% 100%;
292|--border: 0 0% 0%;
293|--radius: 0;
294|```
295|
296|**적합**: 블로그·문서 플랫폼·출판·뉴스레터
297|
298|