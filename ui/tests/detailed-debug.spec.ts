import { test, expect } from '@playwright/test';

test('Detailed component debugging', async ({ page }) => {
  page.on('console', msg => {
    console.log(`[BROWSER]: ${msg.text()}`);
  });

  page.on('pageerror', error => {
    console.log(`[PAGE ERROR]: ${error.message}`);
  });

  await page.goto('/');
  
  // Wait for React to render
  await page.waitForLoadState('networkidle');
  
  console.log('✅ Page loaded');
  
  // Check if our component is rendered
  const uploadZone = await page.getByText('Upload PDF Statement').count();
  console.log('Upload zone rendered:', uploadZone > 0);
  
  // Let's inspect the actual button element more deeply
  const buttons = page.locator('button');
  const buttonCount = await buttons.count();
  console.log('Total buttons:', buttonCount);
  
  if (buttonCount > 0) {
    const button = buttons.first();
    const buttonHTML = await button.innerHTML();
    console.log('Button HTML:', buttonHTML);
    
    const buttonText = await button.textContent();
    console.log('Button text:', buttonText);
    
    // Check if button has click handler
    const hasOnClick = await button.evaluate(el => {
      const events = getEventListeners ? getEventListeners(el) : {};
      return Object.keys(events).includes('click');
    }).catch(() => 'unknown');
    
    console.log('Button has click listener:', hasOnClick);
    
    // Try to click it and see what happens
    console.log('About to click button...');
    
    try {
      await button.click({ timeout: 5000 });
      console.log('✅ Button clicked successfully');
    } catch (e) {
      console.log('❌ Button click failed:', e.message);
    }
  }
  
  // Also check if there are any React errors by looking for error boundaries
  const errorBoundary = await page.locator('[data-error-boundary]').count();
  console.log('Error boundaries found:', errorBoundary);
  
  // Look for React DevTools indicators
  const reactRoot = await page.locator('#root').count();
  console.log('React root found:', reactRoot > 0);
  
  if (reactRoot > 0) {
    const rootHTML = await page.locator('#root').innerHTML();
    console.log('Root HTML length:', rootHTML.length);
    console.log('Root HTML (first 200 chars):', rootHTML.substring(0, 200));
  }
});