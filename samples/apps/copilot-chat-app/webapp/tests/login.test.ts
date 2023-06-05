import { expect, test } from '@playwright/test';

test('login required', async ({ page }) => {
  await page.goto('/');

  // Expect the title to be "Copilot Chat".
  await expect(page).toHaveTitle("Copilot Chat");

  // Expect the page to contain a "Login" button.
  await page.getByRole('button').click();
  // Clicking the login button should redirect to the login page.
  await expect(page).toHaveURL(new RegExp('^'+process.env.REACT_APP_AAD_AUTHORITY));
});