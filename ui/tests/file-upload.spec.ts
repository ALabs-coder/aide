import { test, expect } from '@playwright/test';

test.describe('PDF Upload Functionality', () => {
  test('should render upload zone correctly', async ({ page }) => {
    await page.goto('/');
    
    // Check if header is rendered
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('PDF Extractor')).toBeVisible();
    
    // Check if upload zone is visible
    await expect(page.getByText('Upload PDF Statement')).toBeVisible();
    await expect(page.getByText('Drag & drop your bank statement or click to browse')).toBeVisible();
    
    // Check if Choose File button is present
    const chooseFileButton = page.getByRole('button', { name: 'Choose File' });
    await expect(chooseFileButton).toBeVisible();
    
    console.log('Choose File button HTML:', await chooseFileButton.innerHTML());
  });

  test('should have clickable file input', async ({ page }) => {
    await page.goto('/');
    
    // Look for the file input element
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();
    
    console.log('File input count:', await fileInput.count());
    console.log('File input attributes:', await fileInput.getAttribute('accept'));
    
    // Check if the dropzone area is clickable
    const dropzone = page.locator('[data-testid="dropzone"], .cursor-pointer').first();
    
    if (await dropzone.count() > 0) {
      await expect(dropzone).toBeVisible();
      console.log('Dropzone classes:', await dropzone.getAttribute('class'));
    }
  });

  test('should trigger file dialog on button click', async ({ page }) => {
    await page.goto('/');
    
    // Try to find and click the Choose File button
    const chooseFileButton = page.getByRole('button', { name: 'Choose File' });
    
    // Add a listener for file chooser dialog
    const fileChooserPromise = page.waitForEvent('filechooser', { timeout: 5000 });
    
    try {
      await chooseFileButton.click();
      const fileChooser = await fileChooserPromise;
      console.log('File chooser opened successfully');
      console.log('Accepted file types:', fileChooser.page().url());
    } catch (error) {
      console.error('File chooser did not open:', error);
      
      // Let's inspect the DOM structure around the button
      const buttonParent = chooseFileButton.locator('..');
      console.log('Button parent HTML:', await buttonParent.innerHTML());
      
      // Try clicking the dropzone area instead
      const dropzoneArea = page.locator('.cursor-pointer').first();
      if (await dropzoneArea.count() > 0) {
        console.log('Trying to click dropzone area...');
        await dropzoneArea.click();
        
        try {
          await page.waitForEvent('filechooser', { timeout: 2000 });
          console.log('File chooser opened via dropzone click');
        } catch (e) {
          console.log('File chooser still not opened via dropzone');
        }
      }
    }
  });

  test('should inspect PDF viewer component structure', async ({ page }) => {
    await page.goto('/');
    
    // Get the entire page content to understand the structure
    const pdfViewerSection = page.locator('.w-3\\/5').first(); // 60% width section
    
    if (await pdfViewerSection.count() > 0) {
      console.log('PDF Viewer section HTML:', await pdfViewerSection.innerHTML());
    } else {
      console.log('PDF Viewer section not found, full body HTML:');
      console.log(await page.locator('body').innerHTML());
    }
  });
});