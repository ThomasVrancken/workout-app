import { expect, test } from '@playwright/test';

/**
 * Responsive smoke tests across the breakpoints defined in playwright.config.ts.
 * Each project (desktop / tablet / mobile) runs these against its own viewport.
 */

test.describe('Responsive smoke', () => {
  test('landing page has no horizontal scroll', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));

    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });

  test('privacy page has no horizontal scroll', async ({ page }) => {
    await page.goto('/privacy');
    await page.waitForLoadState('networkidle');

    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));

    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });

  test('terms page has no horizontal scroll', async ({ page }) => {
    await page.goto('/terms');
    await page.waitForLoadState('networkidle');

    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));

    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });

  test('hero CTA is reachable above the fold', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const cta = page.getByRole('link', { name: 'Start training smarter' });
    await expect(cta).toBeInViewport();
  });

  test('primary touch targets are at least 40px tall', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const handles = await page.locator('.btn, .btn-primary, .btn-ghost').all();
    for (const handle of handles) {
      const box = await handle.boundingBox();
      if (!box) continue;
      expect(box.height).toBeGreaterThanOrEqual(40);
    }
  });
});
