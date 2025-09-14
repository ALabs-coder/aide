import { test, expect } from '@playwright/test';

test('Debug open function call', async ({ page }) => {
  // Listen for console messages from our debug code
  page.on('console', msg => {
    console.log(`[BROWSER]: ${msg.text()}`);
  });

  await page.goto('/');
  
  // Wait for page load
  await expect(page.getByText('Upload PDF Statement')).toBeVisible();
  
  const chooseFileButton = page.getByRole('button', { name: 'Choose File' });
  
  console.log('✅ About to click Choose File button');
  
  // Click the button and see what console logs appear
  await chooseFileButton.click();
  
  console.log('✅ Button clicked, waiting for console output...');
  
  // Wait a bit to see console messages
  await page.waitForTimeout(1000);
  
  console.log('Test completed');
});