# 9. Newspaper — 신문 편집 레이아웃 (Editorial Classic)

> 출처: `templates/fe/styling_design.md`
> design-init에서 선택된 프리셋만 로드된다.

### 9. Newspaper — 신문 편집 레이아웃 (Editorial Classic)
380|
381|> 따뜻한 신문지 톤·세리프·잉크 느낌. 블로그·뉴스·매거진에 적합.
382|
383|```
384|Font:     Playfair Display (제목, 400–900) + Source Serif 4 (본문)
385|Radius:   --radius: 0 (완전 사각)
386|Shadows:  없음. 구분선(rules)으로 섹션 분리
387|```
388|
389|```css
390|--background: 36 23% 93%;       /* #f5f0e8 newsprint */
391|--foreground: 0 0% 10%;         /* #1a1a1a ink */
392|--primary: 0 0% 10%;
393|--primary-foreground: 36 23% 93%;
394|--secondary: 0 0% 100%;
395|--secondary-foreground: 0 0% 10%;
396|--muted: 30 4% 40%;             /* #6b6560 */
397|--muted-foreground: 30 4% 50%;
398|--accent: 6 63% 46%;            /* #c0392b red accent */
399|--accent-foreground: 0 0% 100%;
400|--border: 0 0% 10%;
401|--radius: 0;
402|```
403|
404|**적합**: 뉴스·블로그·매거진·구독 뉴스레터
405|
406|