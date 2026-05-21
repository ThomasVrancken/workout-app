# Playwright Tests

End-to-end tests for the Workout Agent web app.

## What's covered

- **`landing.spec.ts`** — Landing page content, structure, CTAs, anchor links, and a visual snapshot of the hero.
- **`legal.spec.ts`** — Privacy and Terms pages: structure, GDPR sections, cross-links, visual snapshots.
- **`app.spec.ts`** — Chat app shell: sign-in overlay, misconfiguration fallback, empty-state suggestion chips. Firebase auth is mocked at the network layer (no real sign-in is performed).
- **`responsive.spec.ts`** — Smoke tests across desktop / tablet / mobile breakpoints: no horizontal scroll, CTA visibility, minimum touch target sizes.

Visual snapshots are stored alongside each spec file under `*-snapshots/`.

## Setup

```bash
# From the repo root, install Playwright (one-time)
npm install
npx playwright install --with-deps chromium webkit
```

If you're working in CI or want all browsers:

```bash
npx playwright install --with-deps
```

## Running

The test runner will spin up the FastAPI server itself (via `uv run uvicorn ...`) on `127.0.0.1:8000` if one isn't already running.

```bash
npm test                       # run everything
npm run test:headed            # see the browser
npm run test:ui                # interactive UI mode
npm run test:update-snapshots  # refresh visual baselines after intentional UI changes
npm run test:report            # open the last HTML report
```

You can filter by project (viewport) or test name:

```bash
npx playwright test --project=mobile
npx playwright test landing
```

## Notes

- Tests run in dark mode (`colorScheme: 'dark'`) since the app is dark-only.
- Visual snapshots are platform-sensitive; regenerate baselines on the same OS where CI runs.
- The chat-app tests stub `/api/config` and block Firebase SDK requests to avoid hitting real services.
- We don't test real chat responses (would require valid Hevy + Gemini credentials). Those are covered by Python unit tests for the backend.
