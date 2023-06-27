import { expect, test } from '@playwright/test';
import * as util from './utils'

/*
Summary: Tests the Multiuser feature of Copilot Chat. Specifically if a user can 
generate a chatid for their chat session and then if another user can join that same chat session.
*/
export async function multiUserTest(page) {
    const useraccount1 = process.env.REACT_APP_TEST_USER_ACCOUNT as string;
    const useraccount2 = process.env.REACT_APP_TEST_USER_ACCOUNT2 as string;
    const password = process.env.REACT_APP_TEST_USER_PASSWORD as string;
    await util.loginHelper(page, useraccount1, password);
    await util.createNewChat(page);

    await page.getByRole('button', { name: 'Share' }).click();
    await page.getByRole('menuitem', { name: 'Invite others to your Bot' }).click();

    const labelByID = await page.getByTestId('copyIDLabel');
    const chatId = await labelByID.textContent();

    await page.getByRole('button', { name: 'Copied' }).click();
    await page.getByRole('button', { name: 'Close' }).click();

    await page.getByText('DB').click();
    await page.getByText('Log Out').click();

    const usernameToLowerCase = useraccount1.toLowerCase();
    const locatorVal = ('[data-test-id="' + usernameToLowerCase + '"]') as string;
    await page.locator(locatorVal).click();

    await util.loginHelperAnotherUser(page, useraccount2, password);
    await page.getByRole('button', { name: 'Create new conversation' }).click();
    await page.getByRole('menuitem', { name: 'Join a Bot' }).click();
    await page.getByLabel('Please enter the chat ID of the chat').fill(chatId as string);

    await page.getByRole('button', { name: 'Join' }).click();

    await page.waitForTimeout(util.ChatStateChangeWait);
    await page.getByRole('button', { name: 'View more people.' }).click();

    const numPeople = await page.getByRole('button', { name: 'View more people.' }).textContent();
    await expect(numPeople).toEqual("+2");

    await util.postUnitTest(page);
}