import { expect, Page, test } from '@playwright/test';

/**
 * Tests for the authenticated chat app at /app.
 *
 * Since we can't run real Firebase auth in tests, we mock the /api/config
 * endpoint so the app shows the sign-in overlay. Firebase SDK calls
 * (sign-in popup, auth state) are not exercised; only the static UI shell.
 */

const MOCK_FIREBASE_CONFIG = {
  apiKey: 'mock-api-key',
  authDomain: 'mock.firebaseapp.com',
  projectId: 'mock-project',
};

async function setupMockedApp(page: Page): Promise<void> {
  await page.route('**/api/config', (route) =>
    route.fulfill({ json: MOCK_FIREBASE_CONFIG })
  );

  // Block actual Firebase SDK requests so we don't hit real services.
  await page.route('https://www.googleapis.com/**', (route) =>
    route.fulfill({ status: 200, json: {} })
  );
  await page.route('https://identitytoolkit.googleapis.com/**', (route) =>
    route.fulfill({ status: 200, json: {} })
  );

  await page.goto('/app');
  await page.waitForLoadState('networkidle');
}

test.describe('Chat app - sign-in view', () => {
  test('boot loader hides and sign-in overlay appears', async ({ page }) => {
    await setupMockedApp(page);

    const overlay = page.locator('#signinOverlay');
    await expect(overlay).toBeVisible();

    const bootLoader = page.locator('#bootLoader');
    await expect(bootLoader).toBeHidden();
  });

  test('sign-in overlay shows brand, headline, and CTAs', async ({ page }) => {
    await setupMockedApp(page);

    await expect(page.locator('#signinOverlay h2')).toContainText('Welcome to Workout Agent');
    await expect(page.locator('#googleSigninBtn')).toBeVisible();
    await expect(page.locator('#googleSigninBtn')).toContainText('Continue with Google');
    await expect(page.locator('#showEmailBtn')).toBeVisible();
  });

  test('email form toggles open', async ({ page }) => {
    await setupMockedApp(page);

    const emailForm = page.locator('#emailForm');
    await expect(emailForm).not.toHaveClass(/visible/);

    await page.locator('#showEmailBtn').click();
    await expect(emailForm).toHaveClass(/visible/);
    await expect(page.locator('#emailInput')).toBeVisible();
    await expect(page.locator('#passwordInput')).toBeVisible();
  });

  test('terms and privacy links exist in sign-in', async ({ page }) => {
    await setupMockedApp(page);

    const panel = page.locator('#signinOverlay');
    await expect(panel.getByRole('link', { name: 'Terms' })).toHaveAttribute('href', '/terms');
    await expect(panel.getByRole('link', { name: 'Privacy Policy' })).toHaveAttribute(
      'href',
      '/privacy'
    );
  });

  test('chat shell is hidden until authenticated', async ({ page }) => {
    await setupMockedApp(page);

    await expect(page.locator('#appHeader')).toBeHidden();
    await expect(page.locator('#chat')).toBeHidden();
    await expect(page.locator('#inputBar')).toBeHidden();
  });

  test('shows misconfiguration page when Firebase config is empty', async ({ page }) => {
    await page.route('**/api/config', (route) => route.fulfill({ json: {} }));
    await page.goto('/app');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/Workout Agent isn't fully configured/)).toBeVisible();
  });
});

test.describe('Chat app - empty state visuals (synthetic)', () => {
  /**
   * We can't trigger the real chat without Firebase auth, but we can
   * inject a fake auth state to render the chat shell, allowing us to
   * verify the empty state's suggestion chips and layout.
   */
  test('empty state suggestions render after stub login', async ({ page }) => {
    await setupMockedApp(page);

    // Manually flip the UI into the chat state.
    await page.evaluate(() => {
      const hide = (id: string) => {
        const el = document.getElementById(id);
        if (el) {
          el.classList.add('hidden');
          (el as HTMLElement).style.display = 'none';
        }
      };
      const show = (id: string) => {
        const el = document.getElementById(id);
        if (el) (el as HTMLElement).style.display = '';
      };
      hide('signinOverlay');
      show('appHeader');
      show('chat');
      show('inputBar');
    });

    const empty = page.locator('#emptyState');
    await expect(empty).toBeVisible();
    await expect(empty.getByRole('heading', { name: 'Ready when you are.' })).toBeVisible();

    const chips = page.locator('.suggestion-chip');
    await expect(chips.first()).toBeVisible();
    expect(await chips.count()).toBeGreaterThanOrEqual(6);

    // Categorized groups
    await expect(page.getByText('Analyze', { exact: true })).toBeVisible();
    await expect(page.getByText(/Create.*adjust/i)).toBeVisible();
  });

  test('sign-in overlay visual snapshot', async ({ page }) => {
    await setupMockedApp(page);
    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('signin-overlay.png', { fullPage: false });
  });

  test('chat empty state visual snapshot', async ({ page }) => {
    await setupMockedApp(page);

    await page.evaluate(() => {
      const hide = (id: string) => {
        const el = document.getElementById(id);
        if (el) {
          el.classList.add('hidden');
          (el as HTMLElement).style.display = 'none';
        }
      };
      const show = (id: string) => {
        const el = document.getElementById(id);
        if (el) (el as HTMLElement).style.display = '';
      };
      hide('signinOverlay');
      show('appHeader');
      show('chat');
      show('inputBar');
    });

    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('chat-empty-state.png', {
      fullPage: false,
      mask: [page.locator('.empty-logo'), page.locator('.header-text p')],
    });
  });
});
