import { test, expect } from '@playwright/test';

test('Debug UI elements and console errors', async ({ page }) => {
  // Listen for console messages
  page.on('console', msg => {
    console.log(`[BROWSER CONSOLE - ${msg.type()}]: ${msg.text()}`);
  });

  // Listen for page errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR]: ${error.message}`);
  });

  await page.goto('/');
  
  // Wait for page load
  await page.waitForLoadState('networkidle');
  
  console.log('✅ Page loaded');
  
  // Check what's rendered
  const titleExists = await page.getByText('PDF Extractor').count();
  console.log('PDF Extractor title found:', titleExists > 0);
  
  // Check for upload text
  const uploadText = await page.getByText('Upload PDF Statement').count();
  console.log('Upload PDF Statement text found:', uploadText > 0);
  
  // Check for buttons
  const allButtons = await page.locator('button').count();
  console.log('Total buttons found:', allButtons);
  
  // List all button texts
  const buttons = page.locator('button');
  for (let i = 0; i < Math.min(allButtons, 5); i++) {
    const buttonText = await buttons.nth(i).textContent();
    console.log(`Button ${i}: "${buttonText}"`);
  }
  
  // Check for file input
  const fileInputs = await page.locator('input[type="file"]').count();
  console.log('File inputs found:', fileInputs);
  
  if (fileInputs > 0) {
    const fileInput = page.locator('input[type="file"]').first();
    const isHidden = await fileInput.isHidden();
    const isVisible = await fileInput.isVisible();
    console.log('File input - Hidden:', isHidden, 'Visible:', isVisible);
  }
  
  // Take a screenshot for debugging
  await page.screenshot({ path: 'debug-screenshot.png', fullPage: true });
  console.log('✅ Screenshot taken: debug-screenshot.png');
  
  // Try to inspect the dropzone structure
  const dropzones = await page.locator('.border-dashed').count();
  console.log('Dropzone areas found:', dropzones);
  
  if (dropzones > 0) {
    const dropzoneHTML = await page.locator('.border-dashed').first().innerHTML();
    console.log('Dropzone HTML (first 500 chars):', dropzoneHTML.substring(0, 500));
  }
});