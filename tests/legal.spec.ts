import { expect, test } from '@playwright/test';

test.describe('Privacy page', () => {
  test('loads with correct title and headings', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page).toHaveTitle(/Privacy Policy.*Workout Agent/);
    await expect(page.getByRole('heading', { name: 'Privacy Policy', level: 1 })).toBeVisible();
    await expect(page.getByText('Last updated:')).toBeVisible();
  });

  test('has TL;DR callout', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.locator('.callout')).toBeVisible();
    await expect(page.locator('.callout')).toContainText('TL;DR');
  });

  test('all required GDPR sections present', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.getByRole('heading', { name: 'Who we are' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'What data we collect' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'How we use your data' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Third-party services' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Your rights (GDPR)' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'How long we keep your data' })).toBeVisible();
  });

  test('back link returns to landing', async ({ page }) => {
    await page.goto('/privacy');
    await page.getByRole('link', { name: /Back/ }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('no "pet project" language', async ({ page }) => {
    await page.goto('/privacy');
    const body = await page.locator('body').innerText();
    expect(body.toLowerCase()).not.toContain('pet project');
  });
});

test.describe('Terms page', () => {
  test('loads with correct title and headings', async ({ page }) => {
    await page.goto('/terms');
    await expect(page).toHaveTitle(/Terms of Service.*Workout Agent/);
    await expect(page.getByRole('heading', { name: 'Terms of Service', level: 1 })).toBeVisible();
  });

  test('has all required legal sections', async ({ page }) => {
    await page.goto('/terms');
    await expect(page.getByRole('heading', { name: 'The service' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Eligibility' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Your responsibilities' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'AI responses are not professional advice' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Limitation of liability' })).toBeVisible();
  });

  test('cross-links between legal pages work', async ({ page }) => {
    await page.goto('/terms');
    await page.locator('footer').getByRole('link', { name: 'Privacy' }).click();
    await expect(page).toHaveURL(/\/privacy/);
  });

  test('no "pet project" language', async ({ page }) => {
    await page.goto('/terms');
    const body = await page.locator('body').innerText();
    expect(body.toLowerCase()).not.toContain('pet project');
  });
});

test.describe('Legal pages - visual', () => {
  test('privacy page top snapshot', async ({ page }) => {
    await page.goto('/privacy');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('privacy-top.png', { fullPage: false });
  });

  test('terms page top snapshot', async ({ page }) => {
    await page.goto('/terms');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('terms-top.png', { fullPage: false });
  });
});
