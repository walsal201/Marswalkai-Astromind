# AstroMind v2: AI Space Mission Suite

AstroMind combines a deep-space mission planner and a Mars surface EVA planner. The supplied interface and FastAPI backend are included, and the app starts in Demo mode without credentials.

## Run

Open the app preview. The status pill should show **Demo mode · instant**. Orbital estimates, mission profiles, Marswalk plans, hazards, weather, checklists, and chat examples work without an LLM connection.

The app uses the `/astro-api` path for its FastAPI endpoints so it can coexist with the workspace's shared `/api` service.

## Optional live agents

Live CrewAI responses are optional. Install `requirements-live.txt`, then add a supported provider credential and `LLM_MODEL` through Replit Secrets. Never put credentials in the browser or commit them to the project. See `.env.example` for provider names.

## Notes

- Mars maps and terrain are procedural illustrations, not NASA imagery or elevation data.
- Mission figures are planning-level estimates, not mission-certified.
