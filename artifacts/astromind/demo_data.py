"""Orbital maths + deterministic demo generators.

Used for (a) the /metrics endpoint (always real maths) and (b) instant "demo mode"
text when no LLM key is configured, so the app works the moment it starts.
"""
import math

AU_LIGHT_MIN = 8.317  # light-minutes per AU
V_EARTH = 29.78       # km/s, Earth heliocentric circular speed

DEST = {
    "Mars": dict(r=1.524, env="cold, thin CO2 atmosphere, global dust storms, ~0.38 g",
                 sci="habitability, ancient lake sediments, subsurface ice",
                 entry="aerocapture / aerobraking plus powered descent",
                 special="Dust storms can cut solar power and delay EDL"),
    "Europa": dict(r=5.203, env="Jovian radiation belts, ice shell, no atmosphere to speak of",
                   sci="subsurface ocean, ice-shell chemistry, plume sampling",
                   entry="Jupiter capture burn, then a long tour of gravity assists",
                   special="Jupiter radiation (>5 Mrad behind thin shielding) limits electronics life"),
    "Titan": dict(r=9.537, env="dense N2 atmosphere, methane lakes, ~94 K surface",
                  sci="prebiotic organic chemistry, methane cycle, dune fields",
                  entry="Saturn capture, then aerodynamic entry and parachute / rotor descent",
                  special="Very long comm delay and low solar flux force RTG power"),
    "Near-Earth Asteroid": dict(r=1.3, env="microgravity, rubble-pile or monolithic surface",
                                sci="primitive-body composition, resource assessment, planetary defense",
                                entry="rendezvous and proximity operations, touch-and-go or anchoring",
                                special="Poorly known surface mechanics make touchdown risky"),
    "Lunar Gateway": dict(r=None, env="cislunar NRHO, deep-space radiation, thermal cycling",
                          sci="lunar surface access, heliophysics, deep-space habitation tests",
                          entry="trans-lunar injection and NRHO insertion",
                          special="Station-keeping propellant and eclipse seasons drive power margins"),
    "Venus": dict(r=0.723, env="~92 bar CO2 atmosphere, 460 C surface, sulfuric acid clouds",
                  sci="atmospheric dynamics, surface geology, cloud-layer chemistry",
                  entry="flyby, aerobraking or aerocapture; short-lived surface probes",
                  special="Thermal environment limits surface assets to hours"),
}


def dest_key(name: str) -> str:
    n = (name or "").lower()
    for k in DEST:
        if k.lower() in n:
            return k
    return "Mars"


def metrics(destination: str) -> dict:
    """Impulsive Hohmann estimate Earth -> target orbit. Planning-level only."""
    k = dest_key(destination)
    d = DEST[k]
    if d["r"] is None:  # cislunar
        return dict(destination=k, cislunar=True, r_au=1.0, dv_total=3.6, dv_departure_leo=3.15,
                    dv_vinf_departure=0.0, dv_arrival=0.45, transit_days=5, peak_au=0.00257,
                    comm_delay_min=0.02, a_transfer=0.0, ecc=0.0, synodic_days=27.3,
                    notes="Cislunar estimate: trans-lunar injection plus NRHO insertion. Real profiles vary by trajectory family.")
    r2 = d["r"]
    vc = lambda r: V_EARTH / math.sqrt(r)
    v_dep = vc(1.0) * math.sqrt(2 * r2 / (1 + r2))
    dv1 = abs(v_dep - vc(1.0))                       # heliocentric v-infinity at Earth
    v_arr = vc(r2) * math.sqrt(2 * 1.0 / (1 + r2))
    dv2 = abs(vc(r2) - v_arr)                        # heliocentric arrival excess
    v_leo, v_esc = 7.73, 10.93                       # 300 km LEO, km/s
    dv_leo = math.sqrt(dv1 ** 2 + v_esc ** 2) - v_leo
    a = (1 + r2) / 2
    transit = 0.5 * a ** 1.5 * 365.25
    t2 = r2 ** 1.5
    syn = abs(1 / (1 - 1 / t2)) * 365.25 if abs(t2 - 1) > 1e-6 else 0
    peak = 1 + r2
    return dict(destination=k, cislunar=False, r_au=r2, dv_total=round(dv_leo + dv2, 2),
                dv_departure_leo=round(dv_leo, 2), dv_vinf_departure=round(dv1, 2),
                dv_arrival=round(dv2, 2), transit_days=round(transit),
                peak_au=round(peak, 2), comm_delay_min=round(peak * AU_LIGHT_MIN, 1),
                a_transfer=round(a, 3), ecc=round(abs(r2 - 1) / (r2 + 1), 3),
                synodic_days=round(syn),
                notes="Impulsive Hohmann estimate to the target's heliocentric orbit plus LEO departure. "
                      "Real missions use gravity assists, capture burns, aerobraking or low-thrust; treat as a first-pass figure.")


MARS_WINDOWS = {2026: "Nov-Dec 2026", 2028: "Dec 2028-Jan 2029", 2029: "Jan-Feb 2029",
                2031: "Mar 2031", 2033: "Apr 2033", 2035: "May 2035"}


def _crew(p):
    return p["crew_size"] if p["crew_size"] > 0 else 0


def _who(p):
    return f"{p['crew_size']} crew" if p["crew_size"] > 0 else "robotic (no crew)"


# --------------------------------------------------------------------- AstroMind
def astro_profile(p):
    m = metrics(p["destination"]); k = m["destination"]; d = DEST[k]
    crewed = p["crew_size"] > 0
    win = f" (typical window: {MARS_WINDOWS[p['launch_year']]}, verify with an ephemeris)" if k == "Mars" and p["launch_year"] in MARS_WINDOWS else ""
    need = 2 * m["transit_days"] + 30
    fit = "fits" if p["duration_days"] >= need else "does NOT fit"
    rad = round(1.8 * 2 * m["transit_days"]) if crewed and not m["cislunar"] else None
    return f"""## Mission Profile: {p['mission_type']} to {k}
**Launch year:** {p['launch_year']}{win} | **Crew:** {_who(p)} | **Max duration:** {p['duration_days']} days

### Trajectory and delta-v
- Transfer: Hohmann-class, **{m['transit_days']} days** one way, transfer semi-major axis {m['a_transfer']} AU, eccentricity {m['ecc']}.
- Delta-v budget (impulsive estimate): **{m['dv_total']} km/s** ({m['dv_departure_leo']} km/s LEO departure + {m['dv_arrival']} km/s arrival).
- Maximum Earth distance {m['peak_au']} AU, so one-way light delay up to **{m['comm_delay_min']} min**.

### Destination environment
- {d['env'].capitalize()}.
- Science focus: {d['sci']}.
- Arrival strategy: {d['entry']}.

### Architecture
- {"Crew transit habitat with radiation storm shelter, closed-loop ECLSS, and a dedicated ascent/descent element." if crewed else "Spacecraft bus with high-gain antenna, autonomous fault management and a science payload tuned to the objectives."}
- Power: {"solar arrays plus batteries" if k in ("Mars", "Venus", "Near-Earth Asteroid", "Lunar Gateway") else "radioisotope power (solar flux is too low)"}.
- Comms: X/Ka-band to Deep Space Network, store-and-forward with delay-tolerant networking.

### Key design drivers
1. {d['special']}.
2. {"Crew radiation dose: roughly " + str(rad) + " mSv for the round-trip transit alone at ~1.8 mSv/day (MSL-RAD cruise measurement)." if rad else "Autonomy: comm delay prevents real-time control of critical events."}
3. Propellant mass fraction driven by the {m['dv_total']} km/s budget.

### Feasibility
Round-trip transit needs about {2 * m['transit_days']} days; a {p['duration_days']}-day limit **{fit}** a minimal stay (needs ~{need} days). {"Consider a conjunction-class architecture with a longer stay." if fit == "does NOT fit" else "Margin remains for surface or proximity operations."}

*Planning-level estimates only; not mission-certified.*"""


def astro_risks(p):
    m = metrics(p["destination"]); k = m["destination"]; crewed = p["crew_size"] > 0
    rows = [
        ("Launch / TLI failure", "Propulsion", "Low", "Catastrophic", "CRITICAL", "Qualified vehicle, abort modes, reserve launch slot"),
        (f"Orbit insertion / arrival at {k}", "GNC", "Medium", "Catastrophic", "CRITICAL", "Navigation margin, contingency burns, independent verification"),
        ("Communication blackout / delay", "Comms", "High", "Major", "HIGH", f"Autonomy, store-and-forward, delay up to {m['comm_delay_min']} min"),
        ("Power shortfall", "Power", "Medium", "Major", "HIGH", "Oversized arrays/RTG, load shedding, battery margin"),
        ("Solar particle event", "Radiation", "Medium", "Major" if crewed else "Moderate", "HIGH" if crewed else "MEDIUM", "Storm shelter, shielding, space-weather monitoring"),
        ("Thermal control anomaly", "Thermal", "Medium", "Moderate", "MEDIUM", "Redundant loops, heaters, thermal margin analysis"),
        ("Software / fault-management bug", "Software", "Medium", "Major", "HIGH", "Independent V&V, hardware-in-loop testing, safe mode"),
        (k + " environment: " + d_short(k), "Environment", "Medium", "Major", "HIGH", DEST[k]["special"]),
    ]
    if crewed:
        rows += [("Life-support failure", "ECLSS", "Low", "Catastrophic", "CRITICAL", "Redundant loops, spares, 30-day contingency consumables"),
                 ("Crew medical emergency", "Human factors", "Medium", "Major", "HIGH", "Telemedicine, onboard surgical kit, crew cross-training")]
    body = "\n".join(f"| {a} | {b} | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in rows)
    return f"""## Risk Matrix: {p['mission_type']} to {k}
| Risk | Category | Likelihood | Impact | Grade | Mitigation |
|---|---|---|---|---|---|
{body}

**Top concern:** {"Crew survival depends on ECLSS reliability and radiation response." if crewed else "Single-point failures at launch and arrival dominate mission loss probability."}

*Qualitative screening, not a probabilistic risk assessment.*"""


def d_short(k):
    return DEST[k]["env"].split(",")[0]


def astro_timeline(p):
    m = metrics(p["destination"]); y = p["launch_year"]; t = m["transit_days"]
    mo = round(t / 30.4)
    rows = [(f"T-{max(24, mo)} mo", "Mission definition review and architecture freeze"),
            ("T-18 mo", "Preliminary design review; long-lead procurement"),
            ("T-12 mo", "Critical design review"),
            ("T-6 mo", "Integration and environmental testing"),
            ("T-1 mo", "Flight readiness review; ship to launch site"),
            (f"Launch ({y})", f"Departure and injection onto the transfer to {m['destination']}"),
            ("L+30 d", "Checkout complete; first trajectory correction"),
            (f"L+{t // 2} d", "Mid-course correction and deep-space health review"),
            (f"L+{t} d", f"Arrival at {m['destination']} ({m['dv_arrival']} km/s excess handled by capture strategy)"),
            (f"L+{t + 30} d", "Operations begin"),
            (f"L+{min(p['duration_days'], t + 180)} d", "Primary science / surface phase complete (or return departure)")]
    body = "\n".join(f"| {a} | {b} |" for a, b in rows)
    return f"""## Mission Timeline
| When | Milestone |
|---|---|
{body}

*Schedule is illustrative; real programs add margin for each review gate.*"""


def astro_brief(p):
    m = metrics(p["destination"]); k = m["destination"]
    return f"""## MISSION BRIEF: {k.upper()} {p['mission_type'].upper()}
**Status:** DRAFT | **Classification:** Planning study

### 1. Executive summary
A {p['mission_type'].lower()} to {k}, launching {p['launch_year']}, {_who(p)}, within a {p['duration_days']}-day mission limit.

### 2. Objectives
- Primary: {DEST[k]['sci'].split(',')[0]}.
- Secondary: {DEST[k]['sci'].split(',')[-1].strip()}.

### 3. Mission concept
Transfer time {m['transit_days']} days, delta-v budget {m['dv_total']} km/s, peak Earth distance {m['peak_au']} AU.

### 4. Key risks
{DEST[k]['special']}. Communication delay up to {m['comm_delay_min']} min. See the Risk Matrix for the full list.

### 5. Recommendation
Proceed to concept-definition phase; resolve trajectory family, power architecture and entry strategy first.

*Prepared by AstroMind. Planning estimates only.*"""


def astro_chat(p):
    q = (p.get("message") or "").lower(); m = metrics(p["destination"]); k = m["destination"]
    if any(w in q for w in ("delta", "dv", "v budget", "propell", "fuel")):
        return f"The first-pass delta-v to {k} is about **{m['dv_total']} km/s** ({m['dv_departure_leo']} km/s leaving LEO, {m['dv_arrival']} km/s at arrival). Capture burns, gravity assists and low-thrust options can change this substantially."
    if any(w in q for w in ("window", "launch", "when")):
        w = MARS_WINDOWS.get(p["launch_year"])
        return f"Launch windows repeat every synodic period (~{m['synodic_days']} days for {k})." + (f" For {p['launch_year']} Mars the window is roughly **{w}**; confirm with an ephemeris." if k == "Mars" and w else "")
    if any(w in q for w in ("comm", "delay", "blackout", "signal")):
        return f"One-way light delay to {k} reaches **{m['comm_delay_min']} min** at maximum distance ({m['peak_au']} AU). Plan for autonomy and delay-tolerant networking; solar conjunction blackouts last ~2 weeks."
    if any(w in q for w in ("radiat", "dose", "safety", "crew")):
        return "Deep-space cruise dose is about **1.8 mSv/day** (MSL-RAD cruise data), so a long transit accumulates hundreds of mSv. Use a storm shelter for solar particle events and monitor space weather."
    if any(w in q for w in ("power", "solar", "rtg", "battery")):
        return f"At {m['r_au']} AU solar flux is {round(1361 / (m['r_au'] ** 2))} W/m2 versus 1361 at Earth, so {'solar arrays work' if m['r_au'] < 3 else 'radioisotope power is needed'}."
    return f"For a {p['mission_type'].lower()} to {k}: transit ~{m['transit_days']} days, delta-v ~{m['dv_total']} km/s, delay up to {m['comm_delay_min']} min. Ask me about windows, delta-v, radiation, comms or power."


# --------------------------------------------------------------------- MarswalkAI
def _s(p):
    return p.get("site", "Jezero Crater")


def mars_plan(p):
    h = p["duration_hours"]; km = p["route_km"]
    sci_min = round(h * 60 * 0.32)
    return f"""## Marswalk Plan: {_s(p)}
**Objective:** {p['objective']} | **Crew:** {p['crew']} | **EVA length:** {h} h | **Route:** {km} km, {p['waypoints']} waypoints

### Route summary
- Out-and-back loop from base camp, {p['waypoints']} waypoints, {p['hazards']} hazard zones avoided, {p['science_targets']} science stops.
- At ~0.8 km/h suited traverse speed, walking alone takes ~{round(km / 0.8, 1)} h of the {h} h EVA.
- Planned science time: **{sci_min} min** (about 32% of the EVA).

### Phases
1. Pre-EVA checkout and egress (first 10-15%)
2. Outbound traverse (25%)
3. Science stops at priority targets (32%)
4. Return traverse (20%)
5. Ingress and decontamination (10%)

### Go / no-go criteria
- Wind below 25 m/s, dust tau below 1.0, no SPE alert, suit pressure and comms nominal.
- Turn-around time: abort if walk-back time plus 30 min margin exceeds remaining consumables.

*Planning-level output; not mission-certified.*"""


def mars_hazards(p):
    return f"""## Hazard Assessment: {_s(p)}
| Hazard | Severity | Mitigation |
|---|---|---|
| Solar particle event | CRITICAL | Monitor space weather, short return path to shelter, abort on alert |
| Suit failure / loss of pressure | CRITICAL | Buddy system, tethered partner assist, immediate return |
| Dust devils / gusts | MEDIUM | Avoid tracks, schedule key stops before late morning |
| Boulder fields and slopes | HIGH | Route detours; keep slopes under 15 degrees ({p['hazards']} zones already marked) |
| Soft regolith | HIGH | Mark as AVOID; probe with rover or pole before crossing |
| Perchlorate contamination | MEDIUM | Decon station at airlock, no bare-skin contact |
| Thermal cycling | MEDIUM | EVA in mid-day window, monitor battery drain in cold |

Surface radiation is roughly 0.6 mSv/day (Curiosity RAD), so a {p['duration_hours']} h EVA adds a small dose unless a solar particle event occurs."""


def mars_science(p):
    return f"""## Science Brief: {_s(p)}
**Objective:** {p['objective']}

1. **Priority 1:** Layered sedimentary outcrop nearest the route; collect a paired sample (context image + core/scoop).
2. **Priority 2:** Mineral-rich unit flagged by orbital spectrometer; hand-lens imaging and spectrometer reading.
3. **Priority 3:** Fresh regolith exposure for soil mechanics and perchlorate data.

Recommended instrument time: Raman/UV spectrometer 30% - XRF 35% - sampling 35%.
With {p['science_targets']} science stops planned, budget ~{round(p['duration_hours'] * 60 * 0.32 / max(p['science_targets'], 1))} min per stop."""


def mars_weather(p):
    return f"""## EVA Weather Report: {_s(p)}
- **Surface temperature:** {p['temp_c']} C (expect swing of ~60 C between dawn and midday).
- **Wind:** {p['wind_ms']} m/s; EVA limit 25 m/s -> **{'GO' if p['wind_ms'] < 25 else 'NO-GO'}**.
- **Dust optical depth:** tau {p['dust_tau']} -> **{'clear' if p['dust_tau'] < 1 else 'degraded power and visibility'}**.
- **Recommended window:** 09:00-15:00 local mean solar time; schedule high-priority stops in the first three hours.

**Status:** {'GO' if p['wind_ms'] < 25 and p['dust_tau'] < 1.5 else 'HOLD'}"""


def mars_checklist(p):
    return f"""## EVA Checklist: {_s(p)}
### Pre-EVA
- [ ] Weather and space-weather go/no-go confirmed
- [ ] Suit leak check and consumables topped up ({p['crew']})
- [ ] Comms check with Mission Control and EVA partner
- [ ] Route, hazards and abort path reviewed
### During EVA
- [ ] Check suit status every 15 minutes
- [ ] Log each sample with photo, position and tube number
- [ ] Turn around when consumables reach the reserve line
### Post-EVA
- [ ] Decontamination and dust removal at airlock
- [ ] Sample stowage and inventory
- [ ] Medical and suit inspection debrief"""


def mars_brief(p):
    return f"""## EVA OPERATIONS ORDER: {_s(p).upper()}
**Status:** DRAFT | **Duration:** {p['duration_hours']} h | **Crew:** {p['crew']}

### 1. Mission overview
{p['objective']} along a {p['route_km']} km route with {p['waypoints']} waypoints.

### 2. Science objectives
See the Science tab; priority stops sequenced in the first half of the EVA.

### 3. Hazard summary
{p['hazards']} hazard zones marked; radiation, terrain, dust and perchlorate controls apply.

### 4. Weather and go/no-go
Temp {p['temp_c']} C, wind {p['wind_ms']} m/s, tau {p['dust_tau']}.

### 5. Emergency procedures
- Solar particle alert: abort immediately and shelter.
- Suit failure: partner assist and immediate return.
- Visibility under 50 m: halt and shelter in place.
- Comms loss: return along the pre-planned abort route.

*Planning-style document, not an official NASA operations order.*"""


def mars_chat(p):
    q = (p.get("message") or "").lower()
    if any(w in q for w in ("radiat", "spe", "dose")):
        return "Surface dose is roughly **0.6 mSv/day** from galactic cosmic rays. A solar particle event can add much more, so keep the shelter within a short walk and abort on alert."
    if any(w in q for w in ("weather", "dust", "wind", "storm")):
        return f"At {_s(p)}: wind {p['wind_ms']} m/s, tau {p['dust_tau']}, temp {p['temp_c']} C. Keep EVA to mid-day and check forecast before each sol."
    if any(w in q for w in ("route", "slope", "boulder", "terrain")):
        return f"Your route is {p['route_km']} km with {p['hazards']} marked hazard zones. Keep slopes under 15 degrees and avoid low thermal-inertia (soft) ground."
    if any(w in q for w in ("suit", "oxygen", "o2", "battery")):
        return f"Planning assumption: ~0.14 kg O2 per astronaut-hour, so a {p['duration_hours']} h EVA needs ~{round(0.14 * p['duration_hours'], 2)} kg each, plus a 33% reserve."
    return f"I can help with route, hazards, science targets, weather and suit consumables for {_s(p)}. What would you like to know?"


ASTRO = dict(profile=astro_profile, risks=astro_risks, timeline=astro_timeline, brief=astro_brief, chat=astro_chat)
MARS = dict(plan=mars_plan, hazards=mars_hazards, science=mars_science, weather=mars_weather,
            checklist=mars_checklist, brief=mars_brief, chat=mars_chat)


def generate(domain: str, action: str, p: dict) -> str:
    return (ASTRO if domain == "astromind" else MARS)[action](p)
