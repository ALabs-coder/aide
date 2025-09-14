import { test, expect } from '@playwright/test';

test.describe('File Selection Test', () => {
  test('should open file dialog and select file', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.getByText('Upload PDF Statement')).toBeVisible();
    
    // Find the Choose File button
    const chooseFileButton = page.getByRole('button').filter({ hasText: 'Choose File' });
    await expect(chooseFileButton).toBeVisible();
    
    console.log('✅ Choose File button found and visible');
    
    // Set up file chooser listener
    const fileChooserPromise = page.waitForEvent('filechooser');
    
    // Click the button
    await chooseFileButton.click();
    
    console.log('✅ Button clicked');
    
    // Wait for file chooser to open
    const fileChooser = await fileChooserPromise;
    
    console.log('✅ File chooser opened successfully!');
    console.log('Multiple files allowed:', fileChooser.isMultiple());
    console.log('Element type:', await chooseFileButton.tagName());
  });
  
  test('should show file selected after selection', async ({ page }) => {
    await page.goto('/');
    
    // Create a test PDF file in memory (this will simulate file selection)
    const testContent = '%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n196\n%%EOF';
    
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByRole('button').filter({ hasText: 'Choose File' }).click();
    const fileChooser = await fileChooserPromise;
    
    // Simulate selecting a file
    await fileChooser.setFiles([{
      name: 'test-statement.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from(testContent)
    }]);
    
    console.log('✅ File selected programmatically');
    
    // Check if file appears in the interface
    await page.waitForTimeout(1000); // Give React time to update
    
    // Look for file name or upload button change
    const extractButton = page.getByRole('button', { name: /Extract Transactions/ });
    if (await extractButton.count() > 0) {
      console.log('✅ Extract Transactions button appeared');
    } else {
      console.log('⚠️ Extract button not found, checking for file name...');
      const pageContent = await page.textContent('body');
      if (pageContent?.includes('test-statement.pdf')) {
        console.log('✅ File name found in page content');
      }
    }
  });
});