# 6. Dark SaaS — 다크 모드 SaaS (Modern Dark)

> 출처: `templates/fe/styling_design.md`
> design-init에서 선택된 프리셋만 로드된다.

### 6. Dark SaaS — 다크 모드 SaaS (Modern Dark)
299|
300|> 진한 슬레이트에 스카이 블루 포인트. 개발자 도구·기술 SaaS에 적합.
301|
302|```
303|Font:     System-ui (Tailwind 기본)
304|Radius:   --radius: 0.5rem (8px)
305|Shadows:  없음. 테두리와 배경 대비로 계층 구분
306|```
307|
308|```css
309|--background: 229 84% 5%;       /* slate-950 #020617 */
310|--foreground: 210 40% 98%;      /* slate-100 */
311|--primary: 199 89% 48%;         /* sky-500 #0ea5e9 */
312|--primary-foreground: 229 84% 5%;
313|--secondary: 217 33% 17%;       /* slate-900 #0f172a */
314|--secondary-foreground: 210 40% 98%;
315|--muted: 215 20% 65%;           /* slate-400 */
316|--muted-foreground: 215 16% 47%;
317|--accent: 199 89% 48%;
318|--accent-foreground: 229 84% 5%;
319|--border: 217 33% 25%;          /* slate-800 */
320|--radius: 0.5rem;
321|```
322|
323|**적합**: 개발자 도구·API 서비스·기술 블로그·CI/CD 대시보드
324|
325|