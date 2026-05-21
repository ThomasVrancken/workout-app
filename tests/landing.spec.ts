import { expect, test } from '@playwright/test';

test.describe('Landing page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('renders hero with correct messaging', async ({ page }) => {
    await expect(page).toHaveTitle(/Workout Agent.*AI coach.*training history/i);

    const heroHeading = page.getByRole('heading', { level: 1 });
    await expect(heroHeading).toContainText('AI strength coach');
    await expect(heroHeading).toContainText('already knows');

    await expect(page.getByText('Built on top of your Hevy training history')).toBeVisible();
    const heroMeta = page.locator('.hero-meta');
    await expect(heroMeta).toContainText('Free to use');
    await expect(heroMeta).toContainText('2 min setup');
    await expect(heroMeta).toContainText('End-to-end encrypted');
  });

  test('hero CTA links to the chat app', async ({ page }) => {
    const startBtn = page.getByRole('link', { name: 'Start training smarter' });
    await expect(startBtn).toBeVisible();
    await expect(startBtn).toHaveAttribute('href', '/app');
  });

  test('sticky nav has open-app CTA', async ({ page }) => {
    const openApp = page.locator('nav .nav-actions a.btn-primary');
    await expect(openApp).toBeVisible();
    await expect(openApp).toContainText('Open app');
    await expect(openApp).toHaveAttribute('href', '/app');
  });

  test('product mockup renders with workout data card', async ({ page }) => {
    const mockup = page.locator('.mockup');
    await expect(mockup).toBeVisible();
    await expect(mockup.locator('.bot-card')).toBeVisible();
    await expect(mockup.locator('.bot-card')).toContainText('Bench press');
    await expect(mockup.locator('.bot-card')).toContainText('Weekly volume');
  });

  test('features bento grid is visible and complete', async ({ page }) => {
    const features = page.locator('#features .feature-card');
    await expect(features).toHaveCount(3);
    await expect(page.getByRole('heading', { name: 'Knows your full history' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Adjusts routines on the fly' })).toBeVisible();
  });

  test('how-it-works has 3 steps', async ({ page }) => {
    const steps = page.locator('#how .step');
    await expect(steps).toHaveCount(3);
    await expect(steps.nth(0).locator('.step-num')).toContainText('01');
    await expect(steps.nth(1).locator('.step-num')).toContainText('02');
    await expect(steps.nth(2).locator('.step-num')).toContainText('03');
  });

  test('examples section has 6 prompts', async ({ page }) => {
    const examples = page.locator('.examples .example');
    await expect(examples).toHaveCount(6);
  });

  test('vs ChatGPT comparison shows both columns', async ({ page }) => {
    await expect(page.locator('#compare .vs-card.featured')).toBeVisible();
    await expect(page.locator('#compare .vs-card.featured')).toContainText('Workout Agent');
    await expect(page.locator('#compare .vs-card').nth(1)).toContainText('ChatGPT');
  });

  test('footer has core navigation links', async ({ page }) => {
    const footer = page.locator('footer.footer');
    await expect(footer.getByRole('link', { name: 'Privacy Policy' })).toBeVisible();
    await expect(footer.getByRole('link', { name: 'Terms of Service' })).toBeVisible();
    await expect(footer.getByRole('link', { name: 'GitHub' })).toBeVisible();
  });

  test('no "pet project" language remains', async ({ page }) => {
    const body = await page.locator('body').innerText();
    expect(body.toLowerCase()).not.toContain('pet project');
    expect(body.toLowerCase()).not.toContain('individual developer');
  });

  test('smooth scroll anchors work', async ({ page }) => {
    await page.getByRole('link', { name: 'See how it works' }).click();
    await page.waitForTimeout(800);
    const howSection = page.locator('#how');
    await expect(howSection).toBeInViewport();
  });

  test('no console errors on load', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(errors).toEqual([]);
  });
});

test.describe('Landing page - visual', () => {
  test('hero above-the-fold snapshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Allow scroll-reveal animations to settle
    await page.waitForTimeout(800);
    await expect(page).toHaveScreenshot('landing-hero.png', {
      fullPage: false,
      mask: [page.locator('.eyebrow-dot')], // pulsing dot animates
    });
  });
});
