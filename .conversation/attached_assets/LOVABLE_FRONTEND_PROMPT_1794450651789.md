# Lovable prompt: AstroMind front end

Paste everything below the line into Lovable. Before you do, deploy the backend (see `REPLIT_BACKEND_PROMPT.md`) and copy its public URL. You will use it as `VITE_API_URL`.

---

Build **AstroMind**, a modern AI space mission suite, as a React + Vite + TypeScript + Tailwind + shadcn/ui single-page app with React Router and TanStack Query. Dark "mission control" aesthetic, fully responsive (mobile first), accessible (keyboard, labels, contrast).

## Hard requirements
- **No API-key, credential, or "watsonx config" UI anywhere.** The app must work immediately on load. All AI runs on my backend.
- Backend base URL comes from `import.meta.env.VITE_API_URL` (no trailing slash). Create a typed `api.ts` client around `fetch`. Add `.env.example` with `VITE_API_URL=https://YOUR-REPLIT-URL`.
- On load call `GET /api/health`. Show a status pill in the navbar: `mode: "live"` → green "Live · CrewAI agents"; `mode: "demo"` → amber "Demo mode · instant"; request failure → red "Backend offline" with a retry button. Every AI response also carries `mode`; show a small LIVE/DEMO badge on each result card.
- Show friendly loading skeletons while agents work (live calls can take 10 to 40 s) and clear error states with a Retry button. Disable the triggering button while pending. Handle HTTP 429 with "Too many requests, wait a minute."

## Design system
- Background near-black navy `#04060d` with a subtle star-field and soft blue/violet radial glows. Cards: `#0b1020` to `#10172b` gradient, 1px `#1c2742` border, 14px radius.
- Accents: cyan `#38bdf8` and violet `#a78bfa` for AstroMind, Mars orange `#ff6b4a` for MarswalkAI. Status colors: ok `#34d399`, warn `#fbbf24`, critical `#f87171`.
- Headings system sans; labels and numbers in a monospace font, uppercase micro-labels with letter-spacing. Gradient hero title (cyan to violet to pink).
- Smooth 150 ms hover transitions, no heavy animation except the trajectory spacecraft.

## Routes
`/` Home · `/astromind` Deep Space Planner · `/marswalk` MarswalkAI. Sticky navbar: brand "🚀 ASTROMIND", links, health pill.

### 1. Home
Hero (rocket emoji, "AstroMind", one-sentence pitch: multi-agent AI mission suite, works instantly, no keys). Two large product cards: **MarswalkAI** (NEW · MARS SURFACE: layered map, click-to-edit route, terrain profile, AI plan/hazards/weather/checklist, exportable EVA order) and **AstroMind** (Deep space planner: 6 destinations, Hohmann visualiser, risk matrix, timeline, brief, chat). A "How it works" strip: Browser → FastAPI → CrewAI agents → LLM. Chips for science themes (MOLA, CRISM, THEMIS, HiRISE, MCS, rover ground truth, space weather). Disclaimer: maps are procedurally generated illustrations and figures are planning-level estimates.

### 2. AstroMind planner (`/astromind`)
Two-column layout (sidebar collapses on mobile).
**Sidebar form** (react-hook-form + zod):
- Destination: `Mars`, `Europa` (label "Europa (Jupiter system)"), `Titan` (label "Titan (Saturn system)"), `Near-Earth Asteroid`, `Lunar Gateway`, `Venus` (label "Venus Flyby").
- Mission type: `Crewed Mission`, `Robotic Lander`, `Flyby / Observation`, `Sample Return`, `Orbital Survey`.
- Launch year: 2028, 2029, 2031, 2033, 2035. Crew size 0 to 12 (0 = robotic). Max duration days 1 to 5000 (default 900).
- Buttons: Generate Mission Profile, Analyze Mission Risks, Build Mission Timeline, Draft Mission Brief.

**Tabs**: Dashboard · Trajectory · Risk Matrix · Timeline · AI Chat · Mission Brief.
- Dashboard: 4 metric cards (Δv budget km/s, Transit time days, Peak distance AU, Comm delay min) fed by `POST /api/astromind/metrics`, refetched (debounced 250 ms) whenever the form changes, plus the AI Mission Profile card (Markdown).
- Trajectory: SVG Hohmann visualiser. Sun at center, dashed Earth orbit and target orbit (radius `80 * r^0.6` px, `r` = `r_au` from metrics), half-ellipse transfer arc from Earth (right) to target (left) with semi-major `(r1+r2)/2` and semi-minor `sqrt(r1*r2)`, animated spacecraft dot along the path, labels. If `cislunar` is true draw an Earth–Moon/NRHO diagram instead. Below: a parameter table (v∞ departure, LEO departure Δv, arrival Δv, total Δv, semi-major axis, eccentricity, synodic period, transit) and the `notes` string.
- Risk Matrix, Timeline, Mission Brief: render the returned Markdown with `react-markdown` + `remark-gfm`; style tables; turn the words CRITICAL / HIGH / MEDIUM / LOW into colored pill badges. Mission Brief has an "Export all as Markdown" button that downloads every generated section.
- AI Chat: chat bubbles, suggestion chips ("What is the delta-v budget?", "When is the launch window?", "How bad is the comm delay?", "Radiation risk for the crew?"), keeps the last 10 turns as `history`.

### 3. MarswalkAI (`/marswalk`)
Sidebar: Site select (Jezero Crater (Perseverance), Gale Crater (Curiosity), Hellas Planitia Basin, Valles Marineris, Arcadia Planitia, Elysium Planitia (InSight)), EVA hours (1 to 12, default 6), Crew (`2-person EVA team`, `3-person EVA team`, `Solo EVA (emergency only)`), Objective (`Geological Survey`, `Astrobiology Hunt`, `ISRU Site Assessment`, `Sample Cache Retrieval`, `Equipment Repair`), layer toggles (MOLA Topography, CRISM Mineralogy, THEMIS Thermal, HiRISE Terrain, Planned Route, Hazard Zones, Science Targets, Wind/Dust), and AI buttons: Plan Marswalk, Assess Hazards, Science Brief, Weather Report, EVA Checklist.

Tabs: Map · Plan · NASA Data · Weather · Science · Hazards · Timeline · Checklist · Brief · AI Chat.
- **Map**: HUD tiles (lat, lon, MOLA elevation, surface temp, dust opacity) from per-site constants. A `<canvas>` (480×300 internal, scales to width) draws a *procedurally generated* Mars terrain from seeded value noise (seed per site): elevation color ramp dark brown → rust → tan with hillshading; CRISM overlay = teal/green patches where a second noise field is high; THEMIS overlay = blue→orange tint from a third field; HiRISE = dashed cyan coverage rectangle; wind = arrows; hazards = red dashed circles; route = gold polyline with BASE and WP1..n markers; science targets = yellow stars. Toolbar modes: Select, + Waypoint, + Hazard, + Science, Clear route, Reset layers. Click on canvas adds items (convert client coords to canvas coords). Cursor readout of lat/lon/elevation. A default route (BASE + 8 waypoints), 2 hazards and 3 science targets are generated per site. 12.5 m per pixel. Show a clear note that terrain is synthetic.
  - Terrain profile card under the map: sample elevation along the route, draw an SVG area chart, and compute max slope (flag over 15°), total ascent/descent, route length km, and trafficability from the thermal field.
- **Plan / Weather / Science / Hazards / Checklist / Brief**: each has an AI result card (Markdown; render `- [ ]` items as interactive checkboxes). Weather also shows 6 stat tiles (temp, wind, dust tau, pressure, irradiance) and a 10-sol illustrative dust-tau bar chart. Hazards shows 6 baseline hazard cards (solar particle events, dust devils, boulders/slopes, soft regolith, perchlorates, thermal cycling). Science shows ranked targets P1/P2/P3 per site. NASA Data shows 6 cards (MOLA, CRISM, THEMIS, MCS, HiRISE, rover ground truth) per site.
- **Timeline**: Gantt bar from EVA hours: Pre-EVA 8%, Egress 5%, Out 25%, Science 32%, Back 20%, Ingress 10%, starting 09:00 LMST, with time ranges, plus a resource budget (science minutes, O₂ at 0.14 kg per astronaut-hour, 33% reserve, team total).
- **AI Chat** with suggestion chips ("Is the route safe?", "Radiation during EVA?", "Oxygen budget?", "Best time of day for EVA?").
- "Export all as Markdown" downloads every generated section.

## API contract (backend already exists)
All requests `Content-Type: application/json`. All responses JSON.

`GET /api/health` → `{status, mode: "live"|"demo", engine, model}`

AstroMind body (`AstroReq`):
```json
{"destination":"Mars","mission_type":"Crewed Mission","launch_year":2028,"crew_size":4,"duration_days":900,"message":"(chat only)","history":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```
- `POST /api/astromind/metrics` → `{destination, cislunar, r_au, dv_total, dv_departure_leo, dv_vinf_departure, dv_arrival, transit_days, peak_au, comm_delay_min, a_transfer, ecc, synodic_days, notes}`
- `POST /api/astromind/{profile|risks|timeline|brief|chat}` → `{action, mode, engine, text, note?}` where `text` is Markdown. `chat` requires `message`.

MarswalkAI body (`MarsReq`):
```json
{"site":"Jezero Crater (Perseverance)","lat":18.4,"lon":77.7,"elevation_m":-2900,"temp_c":-63,"wind_ms":12,"dust_tau":0.5,"duration_hours":6,"crew":"2-person EVA team","objective":"Geological Survey","route_km":3.2,"waypoints":8,"hazards":2,"science_targets":3,"message":"(chat only)","history":[]}
```
- `POST /api/marswalk/{plan|hazards|science|weather|checklist|brief|chat}` → `{action, mode, engine, text, note?}`.
Always send the **current** route length, waypoint, hazard and science-target counts from the map state.

## Quality bar
Typed API layer, small reusable components (`MetricCard`, `AiResultCard`, `MarkdownView`, `ChatPanel`, `StatusPill`, `LayerToggles`, `MarsMap`, `TrajectorySvg`), no hard-coded backend URL, no secrets in the client, `aria-label`s on icon buttons, works at 375 px width.
