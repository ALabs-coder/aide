import { test, expect } from '@playwright/test';

test('Debug View Results Network Requests', async ({ page }) => {
  // Array to store network requests and responses
  const networkEvents: any[] = [];

  // Listen to all network requests
  page.on('request', request => {
    console.log('🔵 REQUEST:', request.method(), request.url());
    networkEvents.push({
      type: 'request',
      method: request.method(),
      url: request.url(),
      headers: request.headers(),
      timestamp: new Date().toISOString()
    });
  });

  // Listen to all network responses
  page.on('response', response => {
    console.log('🟡 RESPONSE:', response.status(), response.url());
    networkEvents.push({
      type: 'response',
      status: response.status(),
      statusText: response.statusText(),
      url: response.url(),
      headers: response.headers(),
      timestamp: new Date().toISOString()
    });
  });

  // Listen to failed requests
  page.on('requestfailed', request => {
    console.log('🔴 FAILED REQUEST:', request.url(), request.failure()?.errorText);
    networkEvents.push({
      type: 'failed',
      url: request.url(),
      error: request.failure()?.errorText,
      timestamp: new Date().toISOString()
    });
  });

  // Listen to console logs
  page.on('console', msg => {
    console.log('🟢 CONSOLE:', msg.type(), msg.text());
  });

  // Navigate to the application
  await page.goto('http://localhost:5174/');

  // Wait for the page to load
  await page.waitForLoadState('networkidle');

  // Take a screenshot of the initial state
  await page.screenshot({ path: 'debug-initial-state.png' });

  // Look for the statements table and View Results buttons
  await page.waitForSelector('table', { timeout: 10000 });

  // Find all View Results buttons (should be enabled only for completed statements)
  const viewResultsButtons = await page.locator('button:has-text("View Results")').all();

  console.log(`Found ${viewResultsButtons.length} View Results buttons`);

  if (viewResultsButtons.length === 0) {
    console.log('No View Results buttons found. Taking screenshot of current state...');
    await page.screenshot({ path: 'debug-no-buttons.png' });

    // Show the current table content
    const tableText = await page.locator('table').textContent();
    console.log('Table content:', tableText);
    return;
  }

  // Click the first available View Results button
  console.log('Clicking the first View Results button...');
  await viewResultsButtons[0].click();

  // Wait a bit for the navigation and API calls
  await page.waitForTimeout(2000);

  // Take a screenshot after clicking
  await page.screenshot({ path: 'debug-after-click.png' });

  // Check current URL
  console.log('Current URL after click:', page.url());

  // Wait for any additional network requests to complete
  await page.waitForLoadState('networkidle');

  // Print all network events
  console.log('\n=== NETWORK EVENTS SUMMARY ===');
  networkEvents.forEach((event, index) => {
    console.log(`${index + 1}. [${event.type.toUpperCase()}] ${event.timestamp}`);
    if (event.type === 'request') {
      console.log(`   ${event.method} ${event.url}`);
    } else if (event.type === 'response') {
      console.log(`   ${event.status} ${event.statusText} - ${event.url}`);
    } else if (event.type === 'failed') {
      console.log(`   FAILED: ${event.url} - ${event.error}`);
    }
  });

  // Look for API-related requests specifically
  const apiRequests = networkEvents.filter(event =>
    event.url && event.url.includes('cypom236ui.execute-api.us-east-1.amazonaws.com')
  );

  console.log('\n=== API REQUESTS ===');
  if (apiRequests.length === 0) {
    console.log('No API requests found!');
  } else {
    apiRequests.forEach(req => {
      console.log(`API ${req.type}: ${req.method || req.status} ${req.url}`);
      if (req.type === 'response' && req.status >= 400) {
        console.log(`   ❌ ERROR: ${req.status} ${req.statusText}`);
      }
    });
  }

  // Check if we're on the results page
  if (page.url().includes('/results/')) {
    console.log('✅ Successfully navigated to results page');

    // Check for error messages on the page
    const errorElement = await page.locator('[role="alert"], .error, .text-red').first();
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      console.log('❌ Error message found on page:', errorText);
    }
  } else {
    console.log('❌ Did not navigate to results page');
  }
});