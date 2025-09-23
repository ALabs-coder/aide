import { test, expect } from '@playwright/test';

test('Screenshot and debug CSV buttons on deployed site', async ({ page }) => {
  // Navigate to the deployed URL
  await page.goto('https://d300pkcz1cpyay.cloudfront.net');

  // Wait for the page to load
  await page.waitForLoadState('networkidle');

  // Take a full page screenshot
  await page.screenshot({
    path: 'csv-debug-full-page.png',
    fullPage: true
  });

  // Look for CSV-related elements
  const csvElements = await page.locator('text=/csv/i').all();
  const exportElements = await page.locator('text=/export/i').all();

  console.log(`Found ${csvElements.length} elements containing "csv"`);
  console.log(`Found ${exportElements.length} elements containing "export"`);

  // Check for common CSV button selectors
  const buttonSelectors = [
    'button:has-text("CSV")',
    'button:has-text("Export")',
    'button:has-text("Download")',
    '[data-testid*="csv"]',
    '[data-testid*="export"]',
    '.csv-button',
    '.export-button'
  ];

  for (const selector of buttonSelectors) {
    const element = page.locator(selector);
    const count = await element.count();
    if (count > 0) {
      console.log(`Found ${count} elements with selector: ${selector}`);
      await element.first().screenshot({ path: `csv-button-${selector.replace(/[^a-zA-Z0-9]/g, '-')}.png` });
    }
  }

  // Check if we're on the results page or need to upload a file first
  const hasUpload = await page.locator('input[type="file"]').count() > 0;
  const hasResults = await page.locator('table, .results, .data-table').count() > 0;

  console.log(`Has file upload: ${hasUpload}`);
  console.log(`Has results table: ${hasResults}`);

  // Take a screenshot of the current state
  await page.screenshot({
    path: 'csv-debug-current-state.png'
  });
});