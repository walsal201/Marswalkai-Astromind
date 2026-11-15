# AstroMind v2: AI Space Mission Suite

AstroMind combines a deep-space mission planner and a Mars surface EVA planner. The supplied interface and FastAPI backend are included, and the app starts in Demo mode without credentials.

## Run

Open the app preview. The status pill should show **Demo mode · instant**. Orbital estimates, mission profiles, Marswalk plans, hazards, weather, checklists, and chat examples work without an LLM connection.

The app uses the `/astro-api` path for its FastAPI endpoints so it can coexist with the workspace's shared `/api` service.

## Optional live agents

Live CrewAI responses are optional. Install `requirements-live.txt`, then add a supported provider credential and `LLM_MODEL` through Replit Secrets. Never put credentials in the browser or commit them to the project. See `.env.example` for provider names.

## Notes

- The editable Marswalk map, route, and terrain overlays are procedural illustrations. Their scale and cursor coordinates are approximate, not live NASA topography.
- The NASA Data tab embeds NASA’s **Mars Perseverance Sol 1934: WATSON Camera** image, captured July 30, 2026. Image credit: NASA/JPL-Caltech.
- The rover image is representative science context only; it is not georegistered to a plotted route. Other site cards are preloaded planning context, not live NASA data layers.
- Mission figures are planning-level estimates, not mission-certified.

## NASA resource for award form

- **Link Text:** NASA Mars 2020 Perseverance Raw Images
- **Resource:** [Mars Perseverance Sol 1934: WATSON Camera](https://mars.nasa.gov/mars2020/multimedia/raw-images/?rawid=SIF_1934_0838664054_968EBY_N0894246SRLC08062_0000LMJ)
