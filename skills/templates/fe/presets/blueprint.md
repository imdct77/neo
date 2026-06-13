# 10. Blueprint — 청사진 기술 도면 (Technical Blueprint)

> 출처: `templates/fe/styling_design.md`
> design-init에서 선택된 프리셋만 로드된다.

### 10. Blueprint — 청사진 기술 도면 (Technical Blueprint)
407|
408|> 짙은 청색 배경·흰 격자·모노스페이스. 기술 문서·API 레퍼런스에 적합.
409|
410|```
411|Font:     Courier Prime (400, 700, italic) — 전부 monospace
412|Radius:   --radius: 0
413|Shadows:  없음. 격자선이 구조를 만든다
414|```
415|
416|```css
417|--background: 210 100% 20%;     /* #003366 blueprint blue */
418|--foreground: 208 100% 97%;     /* #F0F8FF alice blue */
419|--primary: 208 100% 97%;
420|--primary-foreground: 210 100% 20%;
421|--secondary: 210 100% 15%;      /* #002b55 darker panel */
422|--secondary-foreground: 208 100% 97%;
423|--muted: 208 30% 60%;
424|--muted-foreground: 208 30% 70%;
425|--accent: 50 100% 60%;          /* yellow annotations */
426|--accent-foreground: 210 100% 20%;
427|--border: 208 100% 97% / 0.15;  /* grid lines */
428|--radius: 0;
429|```
430|
431|**적합**: API 문서·기술 명세·아키텍처 다이어그램·개발자 허브
432|
433|