import { expect, test } from '@playwright/test';

/*
This test is a simple end-to-end test that verifies the app can be
loaded, and signed in. The user can send a message to the bot, and expect
a response.
*/
test('get response from bot', async ({ page }) => {
    // Make sure the server is running.
    await page.goto('https://localhost:40443/healthz');
    expect(page.getByText('Healthy')).toBeDefined();

    await page.goto('/');
    // Expect the page to contain a "Login" button.
    await page.getByRole('button').click();
    // Clicking the login button should redirect to the login page.
    await expect(page).toHaveURL(new RegExp('^' + process.env.REACT_APP_AAD_AUTHORITY));
    // Login with the test user.
    await page.getByPlaceholder('Email, phone, or Skype').click();
    await page.getByPlaceholder('Email, phone, or Skype').fill(process.env.REACT_APP_TEST_USER_ACCOUNT as string);
    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByPlaceholder('Password').click();
    await page.getByPlaceholder('Password').fill(process.env.REACT_APP_TEST_USER_PASSWORD as string);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Select No if asked to stay signed in.
    const isAskingStaySignedIn = await page.$$("text='Stay signed in?'");
    if (isAskingStaySignedIn) {
        await page.getByRole('button', { name: 'No' }).click();
    }

    // After login, the page should redirect back to the app.
    await expect(page).toHaveTitle('Copilot Chat');

    // Send a message to the bot and wait for the response.
    const responsePromise = page.waitForResponse('**/chat');
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill('Hi!');
    await page.locator('#chat-input').press('Enter');
    await responsePromise;

    // Expect the chat history to contain 3 messages.
    // The first message is the welcome message from the bot.
    // The second message is the user's message.
    // The third message is the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    expect((await chatHistoryItems.all()).length).toBe(3);

    // Expect the third message to be the bot's response.
    await expect(chatHistoryItems.nth(2)).toHaveAttribute('data-username', 'Copilot');
});