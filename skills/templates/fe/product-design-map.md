# Product Design Map — 제품 유형별 디자인 시스템 매핑
> **로드 시점**: design-init Step 1-1 (디자인 스타일 선택 시)
> **출처**: [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — 161개 제품 유형
> **사용법**: CEO가 제품 유형을 말하면 이 표에서 매칭 → 스타일·컬러·레이아웃 패턴 자동 추천

---

## 범례

| 필드 | 의미 |
|------|------|
| **제품 유형** | 매칭 키워드. CEO가 "~만들고 싶다"고 하면 가장 가까운 유형 선택 |
| **1차 스타일** | 최우선 추천 UI 스타일. Neo의 15개 프리셋 또는 stock 스타일과 교차 참조 |
| **2차 스타일** | 대안 스타일. 1차가 브랜드와 안 맞을 때 선택 |
| **컬러 팔레트** | HSL·Hex 변환하여 shadcn/ui CSS 변수에 반영 |
| **랜딩 패턴** | 랜딩 페이지 레이아웃 구성 |
| **대시보드** | 대시보드·관리자 페이지 스타일 (해당 시) |

---

## Tech & SaaS (23개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 1 | SaaS (General) | Glassmorphism + Flat Design | Soft UI Evolution, Minimalism | Hero + Features + CTA | Data-Dense + Real-Time Monitoring | Trust blue + accent contrast |
| 2 | Micro SaaS | Flat Design + Vibrant & Block | Motion-Driven, Micro-interactions | Minimal & Direct + Demo | Executive Dashboard | Vibrant primary + white space |
| 5 | B2B Service | Trust & Authority + Minimal | Feature-Rich, Conversion-Optimized | Feature-Rich Showcase | Sales Intelligence Dashboard | Professional blue + neutral grey |
| 15 | Social Media App | Vibrant & Block-based + Motion-Driven | Aurora UI, Micro-interactions | Feature-Rich Showcase | User Behavior Analytics | Vibrant + engagement colors |
| 16 | Productivity Tool | Flat Design + Micro-interactions | Minimalism, Soft UI Evolution | Interactive Product Demo | Drill-Down Analytics | Clear hierarchy + functional colors |
| 17 | Design System/Component Library | Minimalism + Accessible & Ethical | Flat Design, Zero Interface | Feature-Rich Showcase | N/A - Dev focused | Clear hierarchy + code-like structure |
| 18 | AI/Chatbot Platform | AI-Native UI + Minimalism | Zero Interface, Glassmorphism | Interactive Product Demo | AI/ML Analytics Dashboard | Neutral + AI Purple (#6366F1) |
| 29 | Micro-Credentials/Badges Platform | Minimalism + Flat Design | Accessible & Ethical, Swiss Modernism 2.0 | Trust & Authority | Education Dashboard | Trust Blue + Gold (#FFD700) |
| 46 | Video Streaming/OTT | Dark Mode (OLED) + Motion-Driven | Glassmorphism, Vibrant & Block-based | Hero-Centric Design + Feature-Rich | Media/Entertainment Dashboard | Dark bg + Content poster colors + Brand accent |
| 66 | News/Media Platform | Minimalism + Flat Design | Dark Mode (OLED), Accessible & Ethical | Hero-Centric Design + Feature-Rich | Media Analytics Dashboard | Brand colors + High contrast + Category colors |
| 80 | Cybersecurity Platform | Cyberpunk UI + Dark Mode (OLED) | Neubrutalism, Minimal & Direct | Trust & Authority + Real-Time | Real-Time Monitoring + Heat Map | Matrix Green + Deep Black + Terminal feel |
| 81 | Developer Tool / IDE | Dark Mode (OLED) + Minimalism | Flat Design, Bento Box Grid | Minimal & Direct + Documentation | Real-Time Monitor + Terminal | Dark syntax theme colors + Blue focus |
| 96 | Ride Hailing / Transportation | Minimalism + Glassmorphism | Dark Mode (OLED), Motion-Driven | Conversion-Optimized + Demo | Real-Time Monitoring + Map | Brand primary + map neutral + status indicator colors |
| 102 | Inventory & Stock Management | Flat Design + Minimalism | Dark Mode (OLED), Accessible & Ethical | Feature-Rich Showcase | Real-Time Monitoring + Data-Dense | Functional neutral + status traffic-light (green/amber/re... |
| 107 | Timer & Pomodoro | Minimalism + Neumorphism | Dark Mode (OLED), Micro-interactions | Minimal & Direct | N/A - Utility focused | High-contrast on dark + focus red/amber + break green |
| 113 | Voice Recorder & Memo | Minimalism + AI-Native UI | Flat Design, Dark Mode (OLED) | Interactive Product Demo + Minimal | N/A - Recording focused | Clean white + recording red + waveform accent |
| 118 | File Manager & Transfer | Flat Design + Minimalism | Accessible & Ethical, Dark Mode (OLED) | Feature-Rich Showcase + Demo | N/A - File tree focused | Functional neutral + file type color coding (PDF orange, ... |
| 127 | Short Video Editor | Dark Mode (OLED) + Motion-Driven | Vibrant & Block-based, Glassmorphism | Feature-Rich Showcase + Hero-Centric | N/A - Timeline editor focused | Dark background + timeline track accent colors + effect p... |
| 139 | Gift & Wishlist | Vibrant & Block-based + Soft UI Evolution | Claymorphism, Flat Design | Minimal & Direct + Conversion | N/A - List focused | Celebration warm pink/gold/red + category colors + surpri... |
| 141 | Yoga & Stretching Guide | Organic Biophilic + Soft UI Evolution | Neumorphism, Minimalism | Storytelling-Driven + Social Proof | N/A - Session focused | Earth calming sage/terracotta/cream + breathing gradient ... |
| 151 | Coding Challenge & Practice | Dark Mode (OLED) + Cyberpunk UI | Minimalism, Flat Design | Feature-Rich Showcase + Social Proof | Student Analytics | Code editor dark + success green + difficulty gradient (e... |
| 155 | Public Transit Guide | Flat Design + Accessible & Ethical | Minimalism, Motion-Driven | Feature-Rich Showcase + Interactive Demo | Real-Time Monitoring + Map | Transit brand line colors + real-time indicator green/red... |
| 157 | VPN & Privacy Tool | Minimalism + Dark Mode (OLED) | Cyberpunk UI, Trust & Authority | Trust & Authority + Conversion-Optimized | N/A - Connection focused | Dark shield blue + connected green + disconnected red + t... |

## Finance (7개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 14 | Fintech/Crypto | Glassmorphism + Dark Mode (OLED) | Retro-Futurism, Motion-Driven | Conversion-Optimized | Real-Time Monitoring + Predictive | Dark tech colors + trust + vibrant accents |
| 19 | NFT/Web3 Platform | Cyberpunk UI + Glassmorphism | Aurora UI, 3D & Hyperrealism | Feature-Rich Showcase | Crypto/Blockchain Dashboard | Dark + Neon + Gold (#FFD700) |
| 41 | Insurance Platform | Trust & Authority + Flat Design | Accessible & Ethical, Minimalism | Conversion-Optimized + Trust | Claims Analytics Dashboard | Trust Blue (#0066CC) + Green (security) + Neutral |
| 42 | Banking/Traditional Finance | Minimalism + Accessible & Ethical | Trust & Authority, Dark Mode (OLED) | Trust & Authority + Feature-Rich | Financial Dashboard | Navy (#0A1628) + Trust Blue + Gold accents |
| 91 | Personal Finance Tracker | Glassmorphism + Dark Mode (OLED) | Minimalism, Flat Design | Interactive Product Demo | Financial Dashboard | Calm blue + success green + alert red + chart accents |
| 105 | Invoice & Billing Tool | Minimalism + Flat Design | Swiss Modernism 2.0, Accessible & Ethical | Conversion-Optimized + Trust | Financial Dashboard | Professional navy + paid green + overdue red + neutral grey |
| 112 | Expense Splitter / Bill Split | Flat Design + Vibrant & Block-based | Minimalism, Micro-interactions | Minimal & Direct + Demo | N/A - Balance focused | Success green + alert red + neutral grey + avatar accent ... |

## Healthcare (18개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 8 | Healthcare App | Neumorphism + Accessible & Ethical | Soft UI Evolution, Claymorphism (for patients) | Social Proof-Focused | User Behavior Analytics | Calm blue + health green + trust |
| 22 | Mental Health App | Neumorphism + Accessible & Ethical | Claymorphism, Soft UI Evolution | Social Proof-Focused | Healthcare Analytics | Calm Pastels + Trust colors |
| 32 | Beauty/Spa/Wellness Service | Soft UI Evolution + Neumorphism | Glassmorphism, Minimalism | Hero-Centric Design + Social Proof | User Behavior Analytics | Soft pastels (Pink #FFB6C1 Sage #90EE90) + Cream + Gold a... |
| 35 | Fitness/Gym App | Vibrant & Block-based + Dark Mode (OLED) | Motion-Driven, Neumorphism | Feature-Rich Showcase | User Behavior Analytics | Energetic (Orange #FF6B35 Electric Blue) + Dark bg |
| 58 | Medical Clinic | Accessible & Ethical + Minimalism | Neumorphism, Trust & Authority | Trust & Authority + Conversion | Healthcare Analytics | Medical Blue (#0077B6) + Trust White + Calm Green |
| 59 | Pharmacy/Drug Store | Flat Design + Accessible & Ethical | Minimalism, Trust & Authority | Conversion-Optimized + Trust | Inventory Dashboard | Pharmacy Green + Trust Blue + Clean White |
| 60 | Dental Practice | Soft UI Evolution + Minimalism | Accessible & Ethical, Trust & Authority | Social Proof-Focused + Conversion | Patient Analytics | Fresh Blue + White + Smile Yellow accent |
| 61 | Veterinary Clinic | Claymorphism + Accessible & Ethical | Soft UI Evolution, Flat Design | Social Proof-Focused + Trust | Pet Health Dashboard | Caring Blue + Pet-friendly colors + Warm accents |
| 86 | Biohacking / Longevity App | Biomimetic / Organic 2.0 | Minimalism, Dark Mode (OLED) | Data-Dense + Storytelling | Real-Time Monitor + Biological Data | Cellular Pink/Red + DNA Blue + Clean White |
| 98 | Meditation & Mindfulness | Neumorphism + Soft UI Evolution | Aurora UI, Glassmorphism | Storytelling-Driven + Social Proof | User Behavior Analytics | Ultra-calm pastels (lavender/sage/sky) + breathing animat... |
| 123 | Idle & Clicker Game | Vibrant & Block-based + Motion-Driven | Claymorphism, 3D & Hyperrealism | Feature-Rich Showcase | N/A - Progress focused | Coin gold + upgrade blue + prestige purple + progress green |
| 134 | Plant Care Tracker | Organic Biophilic + Soft UI Evolution | Claymorphism, Flat Design | Storytelling-Driven + Social Proof | N/A - Plant collection focused | Nature greens + earth brown + sunny yellow reminder + wat... |
| 138 | Mood Tracker | Soft UI Evolution + Minimalism | Aurora UI, Neumorphism | Storytelling-Driven + Social Proof | N/A - Mood chart focused | Emotion gradient (blue sad to yellow happy) + pastel per ... |
| 140 | Running & Cycling GPS | Dark Mode (OLED) + Vibrant & Block-based | Motion-Driven, Glassmorphism | Feature-Rich Showcase + Social Proof | Performance Analytics | Energetic orange + map accent + pace zones (green/yellow/... |
| 143 | Calorie & Nutrition Counter | Flat Design + Vibrant & Block-based | Minimalism, Claymorphism | Feature-Rich Showcase + Social Proof | Healthcare Analytics | Healthy green + macro colors (protein blue, carb orange, ... |
| 144 | Period & Cycle Tracker | Soft UI Evolution + Aurora UI | Accessible & Ethical, Claymorphism | Social Proof-Focused + Trust | Healthcare Analytics | Rose/blush + lavender + fertility green + soft calendar t... |
| 145 | Medication & Pill Reminder | Accessible & Ethical + Flat Design | Minimalism, Trust & Authority | Trust & Authority + Feature-Rich | N/A - Schedule focused | Medical trust blue + missed alert red + taken green + cle... |
| 146 | Water & Hydration Reminder | Claymorphism + Vibrant & Block-based | Flat Design, Micro-interactions | Minimal & Direct + Demo | N/A - Daily goal focused | Refreshing blue + water wave animation + goal progress ac... |

## E-commerce (7개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 3 | E-commerce | Vibrant & Block-based | Aurora UI, Motion-Driven | Feature-Rich Showcase | Sales Intelligence Dashboard | Brand primary + success green |
| 4 | E-commerce Luxury | Liquid Glass + Glassmorphism | 3D & Hyperrealism, Aurora UI | Feature-Rich Showcase | Sales Intelligence Dashboard | Premium colors + minimal accent |
| 26 | Subscription Box Service | Vibrant & Block-based + Motion-Driven | Claymorphism, Aurora UI | Feature-Rich Showcase | E-commerce Analytics | Brand + Excitement colors |
| 48 | Marketplace (P2P) | Vibrant & Block-based + Flat Design | Micro-interactions, Trust & Authority | Feature-Rich Showcase + Social Proof | E-commerce Analytics | Trust colors + Category colors + Success green |
| 62 | Florist/Plant Shop | Organic Biophilic + Vibrant & Block-based | Aurora UI, Motion-Driven | Hero-Centric Design + Conversion | E-commerce Analytics | Natural Green + Floral pinks/purples + Earth tones |
| 95 | Food Delivery / On-Demand | Vibrant & Block-based + Motion-Driven | Glassmorphism, Flat Design | Hero-Centric Design + Feature-Rich | Real-Time Monitoring + Map | Appetizing warm (orange/red) + trust blue + map accent |
| 106 | Grocery & Shopping List | Flat Design + Vibrant & Block-based | Claymorphism, Micro-interactions | Minimal & Direct + Demo | N/A - List focused | Fresh green + food-category colors + checkmark accent |

## Services (19개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 13 | Government/Public Service | Accessible & Ethical + Minimalism | Flat Design, Inclusive Design | Minimal & Direct | Executive Dashboard | Professional blue + high contrast |
| 31 | Hyperlocal Services | Minimalism + Vibrant & Block-based | Micro-interactions, Flat Design | Conversion-Optimized | Drill-Down Analytics + Map | Location markers + Trust colors |
| 34 | Restaurant/Food Service | Vibrant & Block-based + Motion-Driven | Claymorphism, Flat Design | Hero-Centric Design + Conversion | N/A - Booking focused | Warm colors (Orange Red Brown) + appetizing imagery |
| 36 | Real Estate/Property | Glassmorphism + Minimalism | Motion-Driven, 3D & Hyperrealism | Hero-Centric Design + Feature-Rich | Sales Intelligence Dashboard | Trust Blue (#0077B6) + Gold accents + White |
| 37 | Travel/Tourism Agency | Aurora UI + Motion-Driven | Vibrant & Block-based, Glassmorphism | Storytelling-Driven + Hero-Centric | Booking Analytics | Vibrant destination colors + Sky Blue + Warm accents |
| 38 | Hotel/Hospitality | Liquid Glass + Minimalism | Glassmorphism, Soft UI Evolution | Hero-Centric Design + Social Proof | Revenue Management Dashboard | Warm neutrals + Gold (#D4AF37) + Brand accent |
| 40 | Legal Services | Trust & Authority + Minimalism | Accessible & Ethical, Swiss Modernism 2.0 | Trust & Authority + Minimal | Case Management Dashboard | Navy Blue (#1E3A5F) + Gold + White |
| 49 | Logistics/Delivery | Minimalism + Flat Design | Dark Mode (OLED), Micro-interactions | Feature-Rich Showcase + Conversion | Real-Time Monitoring + Route Analytics | Blue (#2563EB) + Orange (tracking) + Green (delivered) |
| 54 | Coworking Space | Vibrant & Block-based + Glassmorphism | Minimalism, Motion-Driven | Hero-Centric Design + Feature-Rich | Occupancy Dashboard | Energetic colors + Wood tones + Brand accent |
| 55 | Home Services (Plumber/Electrician) | Flat Design + Trust & Authority | Minimalism, Accessible & Ethical | Conversion-Optimized + Trust | Service Analytics | Trust Blue + Safety Orange + Professional grey |
| 65 | Airline | Minimalism + Glassmorphism | Motion-Driven, Accessible & Ethical | Conversion-Optimized + Feature-Rich | Operations Dashboard | Sky Blue + Brand colors + Trust accents |
| 83 | Space Tech / Aerospace | Holographic / HUD + Dark Mode | Glassmorphism, 3D & Hyperrealism | Immersive Experience + Hero | Real-Time Monitoring + 3D | Deep Space Black + Star White + Metallic |
| 89 | Spatial Computing OS / App | Spatial UI (VisionOS) | Glassmorphism, 3D & Hyperrealism | Immersive/Interactive Experience | Spatial Dashboard | Frosted Glass + System Colors + Depth |
| 103 | Flashcard & Study Tool | Claymorphism + Micro-interactions | Vibrant & Block-based, Flat Design | Feature-Rich Showcase + Demo | Learning Analytics | Playful primary + correct green + incorrect red + progres... |
| 104 | Booking & Appointment App | Soft UI Evolution + Flat Design | Minimalism, Micro-interactions | Conversion-Optimized | Drill-Down Analytics | Trust blue + available green + booked grey + confirm accent |
| 110 | Calendar & Scheduling App | Flat Design + Micro-interactions | Minimalism, Soft UI Evolution | Feature-Rich Showcase + Demo | N/A - Calendar focused | Clean blue + event category accent colors + success green |
| 119 | Email Client | Flat Design + Minimalism | Micro-interactions, Soft UI Evolution | Feature-Rich Showcase + Demo | N/A - Inbox focused | Clean white + brand primary + priority red + snooze amber |
| 150 | Study Together / Virtual Coworking | Minimalism + Soft UI Evolution | Flat Design, Dark Mode (OLED) | Social Proof-Focused + Feature-Rich | User Behavior Analytics | Calm focus blue + session progress indicator + ambient wa... |
| 156 | Road Trip Planner | Aurora UI + Organic Biophilic | Motion-Driven, Vibrant & Block-based | Storytelling-Driven + Hero-Centric | N/A - Trip focused | Adventure warm sunset orange + map teal + stop markers + ... |

## Creative (21개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 10 | Creative Agency | Brutalism + Motion-Driven | Retro-Futurism, Storytelling-Driven | Storytelling-Driven | N/A - Portfolio focused | Bold primaries + artistic freedom |
| 11 | Portfolio/Personal | Motion-Driven + Minimalism | Brutalism, Aurora UI | Storytelling-Driven | N/A - Personal branding | Brand primary + artistic interpretation |
| 12 | Gaming | 3D & Hyperrealism + Retro-Futurism | Motion-Driven, Vibrant & Block | Feature-Rich Showcase | N/A - Game focused | Vibrant + neon + immersive colors |
| 24 | Smart Home/IoT Dashboard | Glassmorphism + Dark Mode (OLED) | Minimalism, AI-Native UI | Interactive Product Demo | Real-Time Monitoring | Dark + Status indicator colors |
| 27 | Podcast Platform | Dark Mode (OLED) + Minimalism | Motion-Driven, Vibrant & Block-based | Storytelling-Driven | Media/Entertainment Dashboard | Dark + Audio waveform accents |
| 45 | Music Streaming | Dark Mode (OLED) + Vibrant & Block-based | Motion-Driven, Aurora UI | Feature-Rich Showcase | Media/Entertainment Dashboard | Dark (#121212) + Vibrant accents + Album art colors |
| 53 | Photography Studio | Motion-Driven + Minimalism | Aurora UI, Glassmorphism | Storytelling-Driven + Hero-Centric | N/A - Portfolio focused | Black + White + Minimal accent |
| 67 | Magazine/Blog | Swiss Modernism 2.0 + Motion-Driven | Minimalism, Aurora UI | Storytelling-Driven + Hero-Centric | Content Analytics | Editorial colors + Brand primary + Clean white |
| 69 | Marketing Agency | Brutalism + Motion-Driven | Vibrant & Block-based, Aurora UI | Storytelling-Driven + Feature-Rich | Campaign Analytics | Bold brand colors + Creative freedom |
| 84 | Architecture / Interior | Exaggerated Minimalism + High Imagery | Swiss Modernism 2.0, Parallax | Portfolio Grid + Visuals | Project Management + Gallery | Monochrome + Gold Accent + High Imagery |
| 88 | Generative Art Platform | Minimalism (Frame) + Gen Z Chaos | Masonry Grid, Dark Mode | Bento Grid Showcase | Gallery / Portfolio | Neutral #F5F5F5 (Canvas) + User Content |
| 114 | Bookmark & Read-Later | Minimalism + Flat Design | Editorial Grid, Swiss Modernism 2.0 | Minimal & Direct + Demo | N/A - List focused | Paper warm white + ink neutral + minimal accent + tag colors |
| 128 | Drawing & Sketching Canvas | Minimalism + Dark Mode (OLED) | Anti-Polish Raw, Motion-Driven | Interactive Product Demo + Storytelling | N/A - Canvas focused | Neutral canvas + full-spectrum color picker + tool panel ... |
| 129 | Music Creation & Beat Maker | Dark Mode (OLED) + Motion-Driven | Cyberpunk UI, Glassmorphism | Interactive Product Demo + Storytelling | N/A - DAW focused | Dark studio background + track colors rainbow + waveform ... |
| 131 | AI Photo & Avatar Generator | AI-Native UI + Aurora UI | Glassmorphism, Minimalism | Feature-Rich Showcase + Social Proof | N/A - Generation focused | AI purple + aurora gradients + before/after neutral |
| 132 | Link-in-Bio Page Builder | Vibrant & Block-based + Bento Box Grid | Minimalism, Glassmorphism | Conversion-Optimized + Social Proof | Analytics (click tracking) | Brand-customizable + accent link color + clean white canvas |
| 136 | Couple & Relationship App | Aurora UI + Soft UI Evolution | Claymorphism, Glassmorphism | Storytelling-Driven + Social Proof | N/A - Couple focused | Warm romantic pink/rose + soft gradient + memory photo tones |
| 142 | Sleep Tracker | Dark Mode (OLED) + Neumorphism | Glassmorphism, Minimalism | Feature-Rich Showcase + Social Proof | Healthcare Analytics | Deep midnight blue + stars/moon accent + sleep quality gr... |
| 153 | Music Instrument Learning | Vibrant & Block-based + Motion-Driven | Dark Mode (OLED), Soft UI Evolution | Interactive Product Demo + Social Proof | Learning Analytics | Musical warm deep red/brown + note color system + skill p... |
| 159 | Wallpaper & Theme App | Vibrant & Block-based + Aurora UI | Glassmorphism, Motion-Driven | Feature-Rich Showcase + Social Proof | N/A - Gallery focused | Content-driven + trending aesthetic palettes + download a... |
| 161 | Home Decoration & Interior Design | Minimalism + 3D Product Preview | Organic Biophilic, Aurora UI | Storytelling-Driven + Feature-Rich | N/A - Project focused | Neutral interior palette + material texture accent + AR blue |

## Lifestyle (17개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 23 | Pet Tech App | Claymorphism + Vibrant & Block-based | Micro-interactions, Flat Design | Storytelling-Driven | User Behavior Analytics | Playful + Warm colors |
| 28 | Dating App | Vibrant & Block-based + Motion-Driven | Aurora UI, Glassmorphism | Social Proof-Focused | User Behavior Analytics | Warm + Romantic (Pink/Red gradients) |
| 78 | Language Learning App | Claymorphism + Vibrant & Block-based | Micro-interactions, Flat Design | Feature-Rich Showcase + Social Proof | Learning Analytics | Playful colors + Progress indicators + Country flags |
| 93 | Notes & Writing App | Minimalism + Flat Design | Swiss Modernism 2.0, Soft UI Evolution | Minimal & Direct | N/A - Editor focused | Clean white/cream + minimal accent + editor syntax colors |
| 94 | Habit Tracker | Claymorphism + Vibrant & Block-based | Micro-interactions, Flat Design | Social Proof-Focused + Demo | User Behavior Analytics | Streak warm (amber/orange) + progress green + motivationa... |
| 97 | Recipe & Cooking App | Claymorphism + Vibrant & Block-based | Soft UI Evolution, Organic Biophilic | Hero-Centric Design + Feature-Rich | N/A - Content focused | Warm food tones (terracotta/sage/cream) + appetizing imagery |
| 99 | Weather App | Glassmorphism + Aurora UI | Motion-Driven, Minimalism | Hero-Centric Design | N/A - Utility focused | Atmospheric gradients (sky blue → sunset → storm grey) + ... |
| 100 | Diary & Journal App | Soft UI Evolution + Minimalism | Neumorphism, Sketch Hand-Drawn | Storytelling-Driven | N/A - Personal focused | Warm paper tones (cream/linen) + muted ink + mood-coded a... |
| 108 | Parenting & Baby Tracker | Claymorphism + Soft UI Evolution | Vibrant & Block-based, Accessible & Ethical | Social Proof-Focused + Trust | User Behavior Analytics | Soft pastels (baby pink/sky blue/mint/peach) + warm accents |
| 115 | Translator App | Flat Design + AI-Native UI | Minimalism, Micro-interactions | Feature-Rich Showcase + Interactive Demo | N/A - Utility focused | Global blue + neutral grey + language flag accent |
| 117 | Alarm & World Clock | Dark Mode (OLED) + Minimalism | Neumorphism, Flat Design | Minimal & Direct | N/A - Utility focused | Deep dark + ambient glow accent + timezone gradient |
| 121 | Trivia & Quiz Game | Vibrant & Block-based + Micro-interactions | Claymorphism, Flat Design | Feature-Rich Showcase + Social Proof | Leaderboard Analytics | Energetic blue + correct green + incorrect red + leaderbo... |
| 133 | Wardrobe & Outfit Planner | Minimalism + Motion-Driven | Aurora UI, Soft UI Evolution | Storytelling-Driven + Feature-Rich | N/A - Wardrobe focused | Clean fashion neutral + full clothes color palette + accent |
| 135 | Book & Reading Tracker | Swiss Modernism 2.0 + Minimalism | E-Ink Paper, Soft UI Evolution | Social Proof-Focused + Feature-Rich | N/A - Library focused | Warm paper white + ink brown + reading progress green + b... |
| 148 | Anonymous Community / Confession | Dark Mode (OLED) + Minimalism | Glassmorphism, Soft UI Evolution | Social Proof-Focused + Feature-Rich | User Behavior Analytics | Dark protective + subtle gradient + upvote green + empath... |
| 149 | Local Events & Discovery | Vibrant & Block-based + Motion-Driven | Glassmorphism, Flat Design | Hero-Centric Design + Feature-Rich | Event Analytics | City vibrant + event category colors + map accent + date ... |
| 160 | White Noise & Ambient Sound | Minimalism + Dark Mode (OLED) | Neumorphism, Organic Biophilic | Minimal & Direct + Social Proof | N/A - Player focused | Calming dark + ambient texture visual + subtle sound wave... |

## Education (3개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 9 | Educational App | Claymorphism + Micro-interactions | Vibrant & Block-based, Flat Design | Storytelling-Driven | User Behavior Analytics | Playful colors + clear hierarchy |
| 43 | Online Course/E-learning | Claymorphism + Vibrant & Block-based | Motion-Driven, Flat Design | Feature-Rich Showcase + Social Proof | Education Dashboard | Vibrant learning colors + Progress green |
| 152 | Kids Learning (ABC & Math) | Claymorphism + Vibrant & Block-based | Micro-interactions, Flat Design | Social Proof-Focused + Trust | Parent Dashboard | Bright primary + child-safe pastels + reward gold + inter... |

## Dashboard & Analytics (6개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 6 | Financial Dashboard | Dark Mode (OLED) + Data-Dense | Minimalism, Accessible & Ethical | N/A - Dashboard focused | Financial Dashboard | Dark bg + red/green alerts + trust blue |
| 7 | Analytics Dashboard | Data-Dense + Heat Map & Heatmap | Minimalism, Dark Mode (OLED) | N/A - Analytics focused | Drill-Down Analytics + Comparative | Cool→Hot gradients + neutral grey |
| 82 | Biotech / Life Sciences | Glassmorphism + Clean Science | Minimalism, Organic Biophilic | Storytelling-Driven + Research | Data-Dense + Predictive | Sterile White + DNA Blue + Life Green |
| 85 | Quantum Computing Interface | Holographic / HUD + Dark Mode | Glassmorphism, Spatial UI | Immersive/Interactive Experience | 3D Spatial Data + Real-Time Monitor | Quantum Blue #00FFFF + Deep Black + Interference patterns |
| 111 | Password Manager | Minimalism + Accessible & Ethical | Dark Mode (OLED), Trust & Authority | Trust & Authority + Feature-Rich | N/A - Vault focused | Trust blue + security green + dark neutral |
| 125 | Arcade & Retro Game | Pixel Art + Retro-Futurism | Vibrant & Block-based, Motion-Driven | Feature-Rich Showcase + Hero-Centric | N/A - Score focused | Neon on black + pixel palette + score gold + danger red |

## Emerging Tech (17개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 25 | EV/Charging Ecosystem | Minimalism + Aurora UI | Glassmorphism, Organic Biophilic | Hero-Centric Design | Energy/Utilities Dashboard | Electric Blue (#009CD1) + Green |
| 44 | Non-profit/Charity | Accessible & Ethical + Organic Biophilic | Minimalism, Storytelling-Driven | Storytelling-Driven + Trust | Donation Analytics Dashboard | Cause-related colors + Trust + Warm |
| 47 | Job Board/Recruitment | Flat Design + Minimalism | Vibrant & Block-based, Accessible & Ethical | Conversion-Optimized + Feature-Rich | HR Analytics Dashboard | Professional Blue + Success Green + Neutral |
| 50 | Agriculture/Farm Tech | Organic Biophilic + Flat Design | Minimalism, Accessible & Ethical | Feature-Rich Showcase + Trust | IoT Sensor Dashboard | Earth Green (#4A7C23) + Brown + Sky Blue |
| 51 | Construction/Architecture | Minimalism + 3D & Hyperrealism | Brutalism, Swiss Modernism 2.0 | Hero-Centric Design + Feature-Rich | Project Management Dashboard | Grey (#4A4A4A) + Orange (safety) + Blueprint Blue |
| 52 | Automotive/Car Dealership | Motion-Driven + 3D & Hyperrealism | Dark Mode (OLED), Glassmorphism | Hero-Centric Design + Feature-Rich | Sales Intelligence Dashboard | Brand colors + Metallic accents + Dark/Light |
| 56 | Childcare/Daycare | Claymorphism + Vibrant & Block-based | Soft UI Evolution, Accessible & Ethical | Social Proof-Focused + Trust | Parent Dashboard | Playful pastels + Safe colors + Warm accents |
| 57 | Senior Care/Elderly | Accessible & Ethical + Soft UI Evolution | Minimalism, Neumorphism | Trust & Authority + Social Proof | Healthcare Analytics | Calm Blue + Warm neutrals + Large text |
| 87 | Autonomous Drone Fleet Manager | HUD / Sci-Fi FUI | Real-Time Monitor, Spatial UI | Real-Time Monitor | Geographic + Real-Time | Tactical Green #00FF00 + Alert Red + Map Dark |
| 90 | Sustainable Energy / Climate Tech | Organic Biophilic + E-Ink / Paper | Data-Dense, Swiss Modernism | Interactive Demo + Data | Energy/Utilities Dashboard | Earth Green + Sky Blue + Solar Yellow |
| 109 | Scanner & Document Manager | Minimalism + Flat Design | Dark Mode (OLED), Accessible & Ethical | Feature-Rich Showcase + Demo | N/A - Tool focused | Clean white + camera viewfinder accent + file-type color ... |
| 122 | Card & Board Game | 3D & Hyperrealism + Flat Design | Motion-Driven, Dark Mode (OLED) | Feature-Rich Showcase | N/A - Game focused | Game-theme felt green + dark wood + card back patterns |
| 124 | Word & Crossword Game | Minimalism + Flat Design | Swiss Modernism 2.0, Micro-interactions | Minimal & Direct + Demo | N/A - Game focused | Clean white + warm letter tiles + success green + shake red |
| 130 | Meme & Sticker Maker | Vibrant & Block-based + Flat Design | Gen Z Chaos, Claymorphism | Feature-Rich Showcase + Social Proof | N/A - Creator focused | Bold primary + comedic yellow + viral red + high saturati... |
| 137 | Family Calendar & Chores | Flat Design + Claymorphism | Accessible & Ethical, Vibrant & Block-based | Feature-Rich Showcase + Social Proof | N/A - Family hub focused | Warm playful + member color coding + chore completion green |
| 154 | Parking Finder | Minimalism + Glassmorphism | Flat Design, Micro-interactions | Conversion-Optimized + Feature-Rich | Real-Time Monitoring + Map | Trust blue + available green + occupied red + map neutral |
| 158 | Emergency SOS & Safety | Accessible & Ethical + Flat Design | Dark Mode (OLED), Minimalism | Trust & Authority + Social Proof | N/A - Safety focused | Alert red + safety blue + location green + high contrast ... |

## 기타 (23개)

| # | 제품 유형 | 1차 스타일 | 2차 스타일 | 랜딩 패턴 | 대시보드 | 컬러 팔레트 |
|---|----------|-----------|-----------|----------|--------|----------|
| 20 | Creator Economy Platform | Vibrant & Block-based + Bento Box Grid | Motion-Driven, Aurora UI | Social Proof-Focused | User Behavior Analytics | Vibrant + Brand colors |
| 21 | Remote Work/Collaboration Tool | Soft UI Evolution + Minimalism | Glassmorphism, Micro-interactions | Feature-Rich Showcase | Drill-Down Analytics | Calm Blue + Neutral grey |
| 30 | Knowledge Base/Documentation | Minimalism + Accessible & Ethical | Swiss Modernism 2.0, Flat Design | FAQ/Documentation | N/A - Documentation focused | Clean hierarchy + minimal color |
| 33 | Luxury/Premium Brand | Liquid Glass + Glassmorphism | Minimalism, 3D & Hyperrealism | Storytelling-Driven + Feature-Rich | Sales Intelligence Dashboard | Black + Gold (#FFD700) + White + Minimal accent |
| 39 | Wedding/Event Planning | Soft UI Evolution + Aurora UI | Glassmorphism, Motion-Driven | Storytelling-Driven + Social Proof | N/A - Planning focused | Soft Pink (#FFD6E0) + Gold + Cream + Sage |
| 63 | Bakery/Cafe | Vibrant & Block-based + Soft UI Evolution | Claymorphism, Motion-Driven | Hero-Centric Design + Conversion | N/A - Order focused | Warm Brown + Cream + Appetizing accents |
| 64 | Brewery/Winery | Motion-Driven + Storytelling-Driven | Dark Mode (OLED), Organic Biophilic | Storytelling-Driven + Hero-Centric | N/A - E-commerce focused | Deep amber/burgundy + Gold + Craft aesthetic |
| 68 | Freelancer Platform | Flat Design + Minimalism | Vibrant & Block-based, Micro-interactions | Feature-Rich Showcase + Conversion | Marketplace Analytics | Professional Blue + Success Green + Neutral |
| 70 | Event Management | Vibrant & Block-based + Motion-Driven | Glassmorphism, Aurora UI | Hero-Centric Design + Feature-Rich | Event Analytics | Event theme colors + Excitement accents |
| 71 | Membership/Community | Vibrant & Block-based + Soft UI Evolution | Bento Box Grid, Micro-interactions | Social Proof-Focused + Conversion | Community Analytics | Community brand colors + Engagement accents |
| 72 | Newsletter Platform | Minimalism + Flat Design | Swiss Modernism 2.0, Accessible & Ethical | Minimal & Direct + Conversion | Email Analytics | Brand primary + Clean white + CTA accent |
| 73 | Digital Products/Downloads | Vibrant & Block-based + Motion-Driven | Glassmorphism, Bento Box Grid | Feature-Rich Showcase + Conversion | E-commerce Analytics | Product category colors + Brand + Success green |
| 74 | Church/Religious Organization | Accessible & Ethical + Soft UI Evolution | Minimalism, Trust & Authority | Hero-Centric Design + Social Proof | N/A - Community focused | Warm Gold + Deep Purple/Blue + White |
| 75 | Sports Team/Club | Vibrant & Block-based + Motion-Driven | Dark Mode (OLED), 3D & Hyperrealism | Hero-Centric Design + Feature-Rich | Performance Analytics | Team colors + Energetic accents |
| 76 | Museum/Gallery | Minimalism + Motion-Driven | Swiss Modernism 2.0, 3D & Hyperrealism | Storytelling-Driven + Feature-Rich | Visitor Analytics | Art-appropriate neutrals + Exhibition accents |
| 77 | Theater/Cinema | Dark Mode (OLED) + Motion-Driven | Vibrant & Block-based, Glassmorphism | Hero-Centric Design + Conversion | Booking Analytics | Dark + Spotlight accents + Gold |
| 79 | Coding Bootcamp | Dark Mode (OLED) + Minimalism | Cyberpunk UI, Flat Design | Feature-Rich Showcase + Social Proof | Student Analytics | Code editor colors + Brand + Success green |
| 92 | Chat & Messaging App | Minimalism + Micro-interactions | Glassmorphism, Flat Design | Feature-Rich Showcase + Demo | User Behavior Analytics | Brand primary + bubble contrast (sender/receiver) + typin... |
| 101 | CRM & Client Management | Flat Design + Minimalism | Soft UI Evolution, Micro-interactions | Feature-Rich Showcase + Demo | Sales Intelligence Dashboard | Professional blue + pipeline stage colors + closed-won green |
| 116 | Calculator & Unit Converter | Neumorphism + Minimalism | Flat Design, Dark Mode (OLED) | Minimal & Direct | N/A - Utility focused | Dark functional + orange operation keys + clear button hi... |
| 120 | Casual Puzzle Game | Claymorphism + Vibrant & Block-based | Micro-interactions, Motion-Driven | Feature-Rich Showcase + Social Proof | N/A - Game focused | Cheerful pastels + progression gradient + reward gold + b... |
| 126 | Photo Editor & Filters | Minimalism + Dark Mode (OLED) | Motion-Driven, Flat Design | Feature-Rich Showcase + Interactive Demo | N/A - Editor focused | Dark editor background + vibrant filter preview strip + t... |
| 147 | Fasting & Intermittent Timer | Minimalism + Dark Mode (OLED) | Neumorphism, Flat Design | Feature-Rich Showcase + Social Proof | N/A - Timer focused | Fasting deep blue/purple + eating window green + timeline... |

---

> 총 161개 제품 유형. Neo의 design-init Step 1-1에서 이 표를 검색하여 자동 추천.
> 스타일명은 아래 매핑 테이블로 Neo 15개 프리셋으로 변환한다.

---

## 스타일 매핑 테이블 (Style Mapping)

> UI UX Pro Max의 58개 스타일명을 Neo의 15개 프리셋으로 변환.
> ⚠️ AI Aesthetic 위반 스타일은 WARN 표시 — 추천 시 CEO에게 경고.

| 원본 스타일 | → Neo 프리셋 | 비고 |
|-----------|------------|------|
| Bento Box Grid | **Bento** | 정확 일치 |
| Swiss Modernism / 2.0 | **Swiss** | 정확 일치 |
| Organic Biophilic / 2.0 | **Organic** | 정확 일치 |
| Minimalism / Minimal / Minimal & Direct / Exaggerated Minimalism | **Swiss** | 미니멀 계열 |
| Flat Design | **Swiss** | 평면 미니멀 |
| Zero Interface | **Scandinavian** | 극단적 절제 |
| Accessible & Ethical / Inclusive Design | **Scandinavian** | 접근성 최우선 |
| Glassmorphism / Liquid Glass | **Soft Modern** | 블러·투명도 |
| Soft UI Evolution | **Soft Modern** | 부드러운 UI |
| Neumorphism | **Soft Modern** | 부드러운 그림자 |
| Micro-interactions / Motion-Driven | **Soft Modern** | 동적 인터랙션 |
| Dark Mode / Dark Mode (OLED) | **Dark SaaS** | 다크 테마 |
| AI-Native UI | **Dark SaaS** | 기술적 현대성 |
| HUD / Sci-Fi FUI / Holographic / HUD | **Blueprint** | 기술 도면 |
| Clean Science | **Blueprint** | 과학적 정밀 |
| Data-Dense / Heat Map / Real-Time Monitor | **Dashboard** | 대시보드 |
| Trust & Authority / Conversion-Optimized | **Corporate** | 신뢰·전환 |
| Masonry Grid | **Corporate** | 구조적 B2B |
| Storytelling-Driven / Editorial Grid | **Newspaper** | 편집·내러티브 |
| E-Ink / Paper | **Newspaper** | 종이 질감 |
| Vibrant & Block / Vibrant & Block-based | **Dot Grid** | 대담한 색상 |
| Neubrutalism | **Dot Grid** | 하드 섀도우+컬러 |
| Brutalism | **Monolith** | 원시적 구조 |
| Anti-Polish Raw | **Monolith** | 가공하지 않은 |
| Aurora UI / Parallax / Feature-Rich / High Imagery | **Enterprise Editorial** | 풍부한 시각 |
| Spatial UI / Spatial UI (VisionOS) | **Bento** | 공간적 그리드 |
| Claymorphism / Claymorphism (for patients) | **Organic** | 물리적 깊이·따뜻함 |
| Sketch Hand-Drawn | **Organic** | 자연스러운 손맛 |
| Biomimetic / Organic 2.0 | **Organic** | 생체모방 |
| Retro-Futurism | **Dot Grid** | 레트로+모던 |
| Pixel Art | **Monolith** | 픽셀 미학 |
| ⚠️ Cyberpunk UI | **Dark Mono** | WARN: 네온·위험 패턴 §8 위반 가능 |
| ⚠️ 3D & Hyperrealism | **Enterprise Editorial** | WARN: 렌더링 비용·복잡도 |
| ⚠️ Gen Z Chaos | **Dot Grid** | WARN: 맥시멀·AI Aesthetic 위반 가능 |
| (럭셔리 제품 전용) Liquid Glass + Glassmorphism | **Luxury** | 명품·프리미엄 브랜드 시 대체 매핑 |

### 매핑 규칙

1. **WARN 표시 스타일**: 추천 시 CEO에게 "이 스타일은 Neo의 AI Aesthetic 규칙과 일부 충돌합니다. 적용 전 검토가 필요합니다." 고지
2. **럭셔리 제품**: 제품 유형에 "Luxury" "Premium" "High-End"가 포함되면 → **Luxury** 프리셋 우선 매핑 (세리프·골드·크림)
3. **매핑 없는 스타일**: 위 테이블에 없는 원본 스타일명 → 가장 키워드 유사도가 높은 Neo 프리셋으로 매핑
4. **복합 스타일** (예: "Glassmorphism + Flat Design"): `+` 앞의 첫 번째 스타일 기준으로 매핑
