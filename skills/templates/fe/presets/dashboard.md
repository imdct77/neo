# 11. Dashboard — 분석 대시보드 (Analytics & Admin)

> 출처: `templates/fe/styling_design.md`
> design-init에서 선택된 프리셋만 로드된다.

### 11. Dashboard — 분석 대시보드 (Analytics & Admin)
434|
435|> 고밀도 데이터·사이드바·차트 중심. 관리자 패널·분석 도구에 적합.
436|
437|```
438|Font:     Inter (400–700). 숫자·ID는 monospace
439|Radius:   --radius: 0.375rem (6px)
440|Shadows:  최소한. 카드에만 subtle shadow
441|```
442|
443|```css
444|--background: 210 40% 98%;      /* slate-50 #f8fafc */
445|--foreground: 217 33% 17%;      /* slate-800 #1e293b */
446|--primary: 217 91% 60%;         /* blue-500 #3b82f6 */
447|--primary-foreground: 0 0% 100%;
448|--secondary: 0 0% 100%;         /* white cards */
449|--secondary-foreground: 217 33% 17%;
450|--muted: 215 16% 47%;           /* slate-500 */
451|--muted-foreground: 215 20% 65%;
452|--accent: 162 47% 50%;          /* green-500 success */
453|--accent-foreground: 0 0% 100%;
454|--border: 214 32% 91%;          /* slate-200 */
455|--radius: 0.375rem;
456|--sidebar: 222 47% 11%;         /* dark sidebar #0f172a */
457|```
458|
459|**적합**: 관리자 패널·분석 대시보드·데이터 시각화·CRM
460|
461|