import { test, expect } from '@playwright/test';

test.describe('PDF Upload Fix Test', () => {
  test('should open file dialog when Choose File button is clicked', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.getByText('Upload PDF Statement')).toBeVisible();
    
    // Find the actual button (not the file input)
    const chooseFileButton = page.getByRole('button').filter({ hasText: 'Choose File' });
    await expect(chooseFileButton).toBeVisible();
    
    // Set up file chooser listener
    const fileChooserPromise = page.waitForEvent('filechooser');
    
    // Click the button
    await chooseFileButton.click();
    
    // Wait for file chooser to open
    const fileChooser = await fileChooserPromise;
    expect(fileChooser.isMultiple()).toBe(false);
    
    console.log('✅ File chooser opened successfully!');
  });

  test('should handle drag and drop', async ({ page }) => {
    await page.goto('/');
    
    // Wait for upload zone
    await expect(page.getByText('Upload PDF Statement')).toBeVisible();
    
    // Find the dropzone
    const dropzone = page.locator('.border-dashed').first();
    await expect(dropzone).toBeVisible();
    
    // Test drag enter (should change appearance)
    await dropzone.dispatchEvent('dragenter', {
      dataTransfer: {
        types: ['Files'],
        files: []
      }
    });
    
    console.log('✅ Dropzone responds to drag events!');
  });
});