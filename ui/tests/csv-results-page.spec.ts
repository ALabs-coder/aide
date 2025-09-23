import { test, expect } from '@playwright/test';

test('Check CSV buttons on results page', async ({ page }) => {
  // Navigate to the deployed URL
  await page.goto('https://d300pkcz1cpyay.cloudfront.net');

  // Wait for the page to load
  await page.waitForLoadState('networkidle');

  // Look for a "View Results" button for a completed statement
  const viewResultsButton = page.locator('button:has-text("View Results")').first();

  if (await viewResultsButton.count() > 0) {
    console.log('Found View Results button, clicking it...');
    await viewResultsButton.click();

    // Wait for navigation or results to load
    await page.waitForLoadState('networkidle');

    // Take screenshot of results page
    await page.screenshot({
      path: 'csv-debug-results-page.png',
      fullPage: true
    });

    // Look for CSV/export buttons on results page
    const csvButtons = await page.locator('button:has-text("CSV"), button:has-text("Export"), button:has-text("Download")').count();
    console.log(`Found ${csvButtons} CSV/Export buttons on results page`);

    // Check for table or data that should be exportable
    const tables = await page.locator('table').count();
    const dataRows = await page.locator('tr, .data-row').count();
    console.log(`Found ${tables} tables and ${dataRows} data rows`);

    // Look for any hidden or conditional export buttons
    const allButtons = await page.locator('button').all();
    console.log(`Total buttons on results page: ${allButtons.length}`);

    for (const button of allButtons) {
      const text = await button.textContent();
      console.log(`Button text: "${text}"`);
    }
  } else {
    console.log('No View Results button found - may need to upload a file first');
  }
});