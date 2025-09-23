import { test, expect } from '@playwright/test';

test('Wait for PDF loading and check CSV export button', async ({ page }) => {
  // Navigate to the deployed URL
  await page.goto('https://d300pkcz1cpyay.cloudfront.net');

  // Wait for the page to load
  await page.waitForLoadState('networkidle');

  // Click on View Results for a completed statement
  const viewResultsButton = page.locator('button:has-text("View Results")').first();

  if (await viewResultsButton.count() > 0) {
    console.log('Clicking View Results button...');
    await viewResultsButton.click();

    // Wait for navigation
    await page.waitForLoadState('networkidle');

    // Take screenshot of initial loading state
    await page.screenshot({
      path: 'csv-debug-loading-state.png'
    });

    // Wait for the loading text to disappear (give it up to 30 seconds)
    console.log('Waiting for loading to complete...');
    try {
      await page.waitForSelector('text=Loading statement results...', {
        state: 'detached',
        timeout: 30000
      });
      console.log('Loading text disappeared');
    } catch (error) {
      console.log('Loading text still present after 30 seconds, continuing anyway...');
    }

    // Wait a bit more for content to fully load
    await page.waitForTimeout(5000);

    // Take screenshot after loading should be complete
    await page.screenshot({
      path: 'csv-debug-after-loading.png',
      fullPage: true
    });

    // Now look for CSV/Export buttons
    const exportButton = page.locator('button:has-text("Export CSV")');
    const downloadButton = page.locator('button:has-text("Download")');
    const csvButton = page.locator('button:has-text("CSV")');

    const exportCount = await exportButton.count();
    const downloadCount = await downloadButton.count();
    const csvCount = await csvButton.count();

    console.log(`Found ${exportCount} "Export CSV" buttons`);
    console.log(`Found ${downloadCount} "Download" buttons`);
    console.log(`Found ${csvCount} "CSV" buttons`);

    // Check all buttons on the page
    const allButtons = await page.locator('button').all();
    console.log(`Total buttons found: ${allButtons.length}`);

    for (const button of allButtons) {
      const text = await button.textContent();
      const isVisible = await button.isVisible();
      console.log(`Button: "${text}" - Visible: ${isVisible}`);
    }

    // Check for any elements with download/export related text
    const downloadElements = await page.locator('*:has-text("Export"), *:has-text("Download"), *:has-text("CSV")').all();
    console.log(`Found ${downloadElements.length} elements with export/download/CSV text`);

    for (const element of downloadElements) {
      const text = await element.textContent();
      const tagName = await element.evaluate(el => el.tagName);
      const isVisible = await element.isVisible();
      console.log(`${tagName}: "${text}" - Visible: ${isVisible}`);
    }

  } else {
    console.log('No View Results button found');
  }
});