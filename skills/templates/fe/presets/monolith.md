# 12. Monolith — 흑백 브루탈 모노리스 (Bold Minimal)

> 출처: `templates/fe/styling_design.md`
> design-init에서 선택된 프리셋만 로드된다.

### 12. Monolith — 흑백 브루탈 모노리스 (Bold Minimal)
462|
463|> 흰 바탕·짙은 네이비 그림자·두꺼운 상단 강조선. 강한 브랜드 정체성에 적합.
464|
465|```
466|Font:     System monospace (Tailwind font-mono). 제목 weight 900
467|Radius:   --radius: 0
468|Shadows:  offset shadow (navy), no blur. 그림자도 브루탈
469|```
470|
471|```css
472|--background: 0 0% 100%;
473|--foreground: 221 39% 11%;      /* #111827 gray-900 */
474|--primary: 221 39% 11%;
475|--primary-foreground: 0 0% 100%;
476|--secondary: 0 0% 96%;
477|--secondary-foreground: 221 39% 11%;
478|--muted: 220 9% 46%;            /* gray-600 */
479|--muted-foreground: 220 9% 60%;
480|--accent: 0 0% 0%;              /* no color accents */
481|--accent-foreground: 0 0% 100%;
482|--border: 221 39% 11%;
483|--radius: 0;
484|```
485|
486|**적합**: 크리에이티브 에이전시·패션·컬처 브랜드·포트폴리오
487|
488|