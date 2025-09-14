import { test, expect } from '@playwright/test';

test('File dialog should open when Choose File button is clicked', async ({ page }) => {
  await page.goto('/');
  
  // Wait for page load
  await expect(page.getByText('Upload PDF Statement')).toBeVisible();
  
  // Now the button should be unique (file input has different aria-label)
  const chooseFileButton = page.getByRole('button', { name: 'Choose File' });
  await expect(chooseFileButton).toBeVisible();
  
  console.log('✅ Choose File button is unique and visible');
  
  // Set up file chooser listener
  const fileChooserPromise = page.waitForEvent('filechooser');
  
  // Click the button
  await chooseFileButton.click();
  
  console.log('✅ Button clicked successfully');
  
  // Wait for file chooser
  const fileChooser = await fileChooserPromise;
  
  console.log('🎉 SUCCESS: File chooser opened!');
  console.log('Multiple files allowed:', fileChooser.isMultiple());
  console.log('Element info:', await chooseFileButton.getAttribute('type'));
  
  // Test file selection
  await fileChooser.setFiles([{
    name: 'test-statement.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4 test content')
  }]);
  
  console.log('✅ File selected programmatically');
  
  // Check if the UI updated to show file selected
  await page.waitForTimeout(500);
  
  // Look for evidence that file was selected
  const extractButton = page.getByRole('button', { name: /Extract Transactions/ });
  if (await extractButton.count() > 0) {
    console.log('🎉 Extract Transactions button appeared - file selection worked!');
  } else {
    console.log('⚠️  Extract button not found, checking page content...');
    const content = await page.textContent('body');
    if (content?.includes('test-statement.pdf')) {
      console.log('✅ File name found in page - selection worked!');
    }
  }
});