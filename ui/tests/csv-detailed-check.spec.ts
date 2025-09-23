import { test, expect } from '@playwright/test';

test('Detailed check for CSV export button', async ({ page }) => {
  // Navigate to the deployed URL
  await page.goto('https://d300pkcz1cpyay.cloudfront.net');
  await page.waitForLoadState('networkidle');

  // Click on View Results
  const viewResultsButton = page.locator('button:has-text("View Results")').first();
  await viewResultsButton.click();
  await page.waitForLoadState('networkidle');

  // Wait for loading to complete
  try {
    await page.waitForSelector('text=Loading statement results...', {
      state: 'detached',
      timeout: 30000
    });
  } catch (error) {
    console.log('Loading may still be present');
  }

  await page.waitForTimeout(5000);

  // Take a full page screenshot
  await page.screenshot({
    path: 'csv-debug-detailed.png',
    fullPage: true
  });

  // Check the page title to make sure we're on the right page
  const title = await page.title();
  console.log(`Page title: ${title}`);

  // Check if we're actually on the results page
  const pageHeader = await page.locator('h1').textContent();
  console.log(`Page header: ${pageHeader}`);

  // Look for the specific element structure from the code
  const headerSection = page.locator('.border-b.bg-card');
  const headerExists = await headerSection.count();
  console.log(`Header section exists: ${headerExists > 0}`);

  // Check for the specific button structure
  const buttonSection = page.locator('div:has(button:has-text("Home"))');
  const buttonSectionExists = await buttonSection.count();
  console.log(`Button section with Home button exists: ${buttonSectionExists > 0}`);

  // Look for any button with Download icon or Export text
  const downloadIcon = page.locator('[data-testid="download"], .lucide-download');
  const downloadIconCount = await downloadIcon.count();
  console.log(`Download icons found: ${downloadIconCount}`);

  // Check for disabled buttons or hidden buttons
  const allButtons = await page.locator('button').all();
  for (let i = 0; i < allButtons.length; i++) {
    const button = allButtons[i];
    const text = await button.textContent();
    const isVisible = await button.isVisible();
    const isDisabled = await button.isDisabled();
    const classes = await button.getAttribute('class');
    console.log(`Button ${i + 1}: "${text}" - Visible: ${isVisible}, Disabled: ${isDisabled}, Classes: ${classes}`);
  }

  // Check the DOM structure around where the export button should be
  const headerContent = await page.locator('.border-b .flex.items-center.justify-between').innerHTML();
  console.log('Header content HTML structure:');
  console.log(headerContent);

  // Scroll to make sure nothing is cut off
  await page.evaluate(() => window.scrollTo(0, 0));

  // Try to find any element with "export" or "csv" in any attribute
  const exportElements = await page.locator('[*|*="export" i], [*|*="csv" i]').count();
  console.log(`Elements with export/csv attributes: ${exportElements}`);
});