# Replit prompt: AstroMind back end (FastAPI + CrewAI)

Fastest route: create a new Python Repl, upload the files from this package (`main.py`, `crew_agents.py`, `demo_data.py`, `index.html`, `requirements.txt`, `.replit`, `.env.example`) and press Run. It works immediately in demo mode.

To have Replit Agent build it from scratch instead, paste everything below the line.

---

Build the back end for **AstroMind**, an AI space mission planning suite, using **Python 3.11, FastAPI, Uvicorn and CrewAI**. It must start and answer every endpoint **with no API key configured** (demo mode), and switch to real CrewAI agents automatically when an LLM key is present in Replit Secrets. The browser never sees or sends any key.

## Files
- `main.py`: FastAPI app, CORS, rate limiting, routes, serves `index.html` at `/`.
- `crew_agents.py`: CrewAI agents and task recipes, imported lazily so the app still boots if `crewai` fails to import.
- `demo_data.py`: orbital maths plus deterministic Markdown generators used for demo mode and as a fallback if a live call fails.
- `requirements.txt`: `fastapi, uvicorn[standard], pydantic>=2, python-dotenv, crewai`.
- `.replit`: run `uvicorn main:app --host 0.0.0.0 --port 8000`, expose port 8000 → 80, Cloud Run deployment.

## Configuration (Replit Secrets / env)
`LLM_MODEL` (LiteLLM-style model string; default `gpt-4o-mini` when only `OPENAI_API_KEY` is set), one provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.; optionally `WATSONX_APIKEY` + `WATSONX_PROJECT_ID` + `WATSONX_URL`), `RATE_LIMIT_PER_MIN` (default 20), `CORS_ORIGINS` (default `*`). Mode is **live** only if crewai imports, a provider key exists and a model is resolvable; otherwise **demo**.

## Endpoints
- `GET /api/health` → `{status:"ok", mode:"live"|"demo", engine:"CrewAI"|"built-in", crewai_installed, model}`.
- `POST /api/astromind/metrics` → real Hohmann maths (below).
- `POST /api/astromind/{profile|risks|timeline|brief|chat}` and `POST /api/marswalk/{plan|hazards|science|weather|checklist|brief|chat}` → `{action, mode, engine, text, note?}` where `text` is Markdown. Unknown action → 404. `chat` without `message` → 422. Apply the rate limit (per client IP, using `x-forwarded-for` first hop) to these generation routes → 429.
- If a live CrewAI call raises, return the demo text with `mode:"demo"` and a `note` explaining the fallback. The UI must never get a 500 from an LLM failure.

## Request models (Pydantic v2, strict limits)
`AstroReq`: `destination` (str ≤60, default "Mars"), `mission_type` (≤60, "Crewed Mission"), `launch_year` (2026–2060, default 2028), `crew_size` (0–12, default 4), `duration_days` (1–5000, default 900), `message` (≤2000, optional), `history` (≤20 items of `{role: user|assistant, content ≤4000}`).
`MarsReq`: `site` (≤80), `lat`, `lon`, `elevation_m`, `temp_c`, `wind_ms` (0–100), `dust_tau` (0–10), `duration_hours` (1–12), `crew` (≤60), `objective` (≤80), `route_km` (0–30), `waypoints`, `hazards`, `science_targets` (0–60 each), plus `message` and `history` as above.

## Metrics maths (`demo_data.metrics`)
Destinations: Mars r=1.524 AU, Europa (Jupiter) 5.203, Titan (Saturn) 9.537, Near-Earth Asteroid 1.3, Venus 0.723, Lunar Gateway = cislunar special case (dv_total 3.6, transit 5 d, peak 0.00257 AU, delay 0.02 min). Match destination by case-insensitive substring; default Mars. For heliocentric targets with `v_c(r) = 29.78/√r` km/s:
- `v_dep = v_c(1)·√(2r/(1+r))`, `v∞ = |v_dep − v_c(1)|`
- `v_arr = v_c(r)·√(2/(1+r))`, `dv_arrival = |v_c(r) − v_arr|`
- LEO departure from 300 km: `dv_leo = √(v∞² + 10.93²) − 7.73`
- `dv_total = dv_leo + dv_arrival`; `a = (1+r)/2`; `transit_days = 0.5·a^1.5·365.25`; `ecc = |r−1|/(r+1)`; `peak_au = 1+r`; `comm_delay_min = peak_au·8.317`; `synodic_days = 365.25 / |1 − 1/r^1.5|`.
Return numbers rounded sensibly plus a `notes` string saying it is an impulsive first-pass estimate (real missions use gravity assists, capture burns, aerobraking or low thrust).
Sanity check: Mars ≈ 259 d transit, ≈ 6 km/s total, ≈ 21 min max delay.

## CrewAI design (sequential `Process`, `verbose=False`, `allow_delegation=False`, one shared `LLM(model=…, temperature=0.4)`)
Agents (role / goal): Deep Space Mission Architect; Flight Dynamics Engineer; Mission Risk Analyst; Mission Scheduler; Technical Writer; Mission Control Assistant; EVA Operations Planner; Planetary Scientist; EVA Safety Officer; Mars Meteorologist.
Task recipes (each later task receives earlier tasks via `context`, the last task's `.raw` is returned):
- astromind `profile`: Flight Dynamics (trajectory notes) → Architect (full mission profile).
- `risks`: Risk Analyst (list) → Risk Analyst (table `Risk | Category | Likelihood | Impact | Grade | Mitigation`, grades CRITICAL/HIGH/MEDIUM, crew risks only if crew > 0).
- `timeline`: Scheduler (milestone table). `brief`: Architect (notes) → Writer (formal brief). `chat`: Assistant, under 150 words.
- marswalk `plan`: Planetary Scientist (ranked targets) → EVA Planner (route, phases, go/no-go, abort rules). `hazards`: Safety Officer (table with CRITICAL/HIGH/MEDIUM). `science`: Scientist. `weather`: Meteorologist (GO/HOLD). `checklist`: EVA Planner (`- [ ]` items, Pre/During/Post). `brief`: EVA Planner → Writer (operations order, never claim NASA approval). `chat`: Assistant.
Inject the request fields and, for AstroMind, the computed metrics JSON into every task. Append a style rule: Markdown, ≤ ~450 words, tables where tabular, figures are planning-level estimates not official NASA data.

## Security
Keys only from env. Treat `message` and `history` as untrusted: wrap in `<user_input>…</user_input>` and instruct agents to treat it as data, not instructions. Enforce all input limits above, rate-limit per IP, never log secrets, never echo env values in errors.

## Acceptance tests
```
curl -s $URL/api/health
curl -s -X POST $URL/api/astromind/metrics -H 'content-type: application/json' -d '{"destination":"Mars"}'
curl -s -X POST $URL/api/astromind/risks -H 'content-type: application/json' -d '{"destination":"Titan","mission_type":"Robotic Lander","crew_size":0}'
curl -s -X POST $URL/api/marswalk/plan -H 'content-type: application/json' -d '{"site":"Jezero Crater"}'
curl -s -X POST $URL/api/astromind/chat -H 'content-type: application/json' -d '{"message":"what is the delta-v?"}'
```
All must return 200 in demo mode with no Secrets set; after adding a provider key and `LLM_MODEL`, `/api/health` must report `"mode":"live"`.

## Deploy
Click Deploy → Autoscale/Cloud Run, then copy the public URL and give it to the front end as `VITE_API_URL`. Keep `CORS_ORIGINS=*` while testing, then set it to the Lovable site origin.
