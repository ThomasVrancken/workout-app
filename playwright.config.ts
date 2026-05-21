import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for Workout Agent.
 *
 * Tests assume a local server is reachable at http://127.0.0.1:8000.
 * If one isn't already running, `webServer` will start it via uvicorn.
 *
 * Run with:
 *   npm test                  - run all tests
 *   npm run test:ui           - open Playwright UI mode
 *   npm run test:headed       - run with a visible browser
 *   npm run test:update-snapshots - refresh visual snapshots
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['html'], ['github']] : 'html',

  use: {
    baseURL: 'http://127.0.0.1:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    colorScheme: 'dark',
  },

  expect: {
    // Allow small pixel differences for cross-platform consistency
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    },
  },

  projects: [
    {
      name: 'desktop-chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
      },
    },
    {
      name: 'tablet',
      use: {
        ...devices['iPad (gen 7)'],
        viewport: { width: 768, height: 1024 },
      },
    },
    {
      name: 'mobile',
      use: {
        ...devices['iPhone 13'],
      },
    },
  ],

  webServer: {
    command: 'uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning',
    url: 'http://127.0.0.1:8000/api/health',
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
