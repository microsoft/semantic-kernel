import { expect, test } from '@playwright/test';

test('login required', async ({ page }) => {
  await page.goto('/');
  // Expect the page to contain a "Login" button.
  await page.getByRole('button').click();
  // Clicking the login button should redirect to the login page.
  await expect(page).toHaveURL(new RegExp('^'+process.env.REACT_APP_AAD_AUTHORITY));
});

test('login successful', async ({ page }) => {
  // Skip this test if the environment variable is not set.
  if (!process.env.TEST_USER_ACCOUNT || !process.env.TEST_USER_PASSWORD) {
    test.skip();
  }

  await page.goto('/');
  // Expect the page to contain a "Login" button.
  await page.getByRole('button').click();
  // Clicking the login button should redirect to the login page.
  await expect(page).toHaveURL(new RegExp('^' + process.env.REACT_APP_AAD_AUTHORITY));
  // Login with the test user.
  await page.getByPlaceholder('Email, phone, or Skype').click();
  await page.getByPlaceholder('Email, phone, or Skype').fill(process.env.TEST_USER_ACCOUNT as string);
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByPlaceholder('Password').click();
  await page.getByPlaceholder('Password').fill(process.env.TEST_USER_PASSWORD as string);
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Select No if asked to stay signed in.
  const isAskingStaySignedIn = await page.$$("text='Stay signed in?'");
  if (isAskingStaySignedIn) {
    await page.getByRole('button', { name: 'No' }).click();
  }

  // After login, the page should redirect back to the app.
  await expect(page).toHaveTitle('Copilot Chat');
});