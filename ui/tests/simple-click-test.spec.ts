import { test, expect } from '@playwright/test';

test('Simple button click test', async ({ page }) => {
  await page.goto('/');
  
  // Wait for page load
  await expect(page.getByText('Choose File')).toBeVisible();
  
  console.log('✅ Page loaded, Choose File button visible');
  
  // Add JavaScript to log when file input click happens
  await page.addScriptTag({
    content: `
      // Override the file input click to log when it's triggered
      const originalClick = HTMLInputElement.prototype.click;
      HTMLInputElement.prototype.click = function() {
        if (this.type === 'file') {
          console.log('🎯 File input click() called!', this);
          window.fileInputClicked = true;
        }
        return originalClick.call(this);
      };
    `
  });
  
  // Listen for the injected console log
  page.on('console', msg => {
    if (msg.text().includes('🎯')) {
      console.log(msg.text());
    }
  });
  
  // Now try to click the Choose File button
  const button = page.getByRole('button', { name: 'Choose File' });
  await button.click();
  
  console.log('✅ Button clicked');
  
  // Check if our injected code detected the file input click
  const fileInputClicked = await page.evaluate(() => window.fileInputClicked);
  console.log('File input click detected:', fileInputClicked);
  
  // Let's also try clicking the file input directly
  const fileInput = page.locator('input[type="file"]');
  console.log('Trying to click file input directly...');
  
  try {
    await fileInput.click({ timeout: 1000 });
    console.log('✅ File input clicked directly');
  } catch (e) {
    console.log('❌ Could not click file input directly:', e.message);
  }
});