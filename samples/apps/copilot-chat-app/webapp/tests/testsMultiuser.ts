import { expect } from '@playwright/test';
import * as util from './utils'

/*
Summary: Tests the Multiuser feature of Copilot Chat. Specifically if a user can 
generate a chatid for their chat session and then if another user can join that same chat session.
*/
export async function shareAndJoinChatSessionTest(page) {
    const userAccount1 = process.env.REACT_APP_TEST_USER_ACCOUNT1 as string;
    const userAccount1Initials = process.env.REACT_APP_TEST_USER_ACCOUNT1_INITIALS as string;
    const userAccount2 = process.env.REACT_APP_TEST_USER_ACCOUNT2 as string;
    const password = process.env.REACT_APP_TEST_USER_PASSWORD as string;
    await util.loginHelper(page, userAccount1, password);
    await util.createNewChat(page);

    await page.getByTestId('shareButton').click();
    await page.getByTestId('inviteOthersMenuItem').click();

    const labelByID = await page.getByTestId('copyIDLabel');
    const chatId = await labelByID.textContent();
    
    await page.getByTestId('chatIDCopyButton').click();
    await page.getByTestId('chatIDCloseButton').click();

    await page.getByText(userAccount1Initials).click();    
    await page.getByTestId('logOutMenuButton').click();

    const usernameToLowerCase = userAccount1.toLowerCase();
    const locatorVal = ('[data-test-id="' + usernameToLowerCase + '"]') as string;
    await page.locator(locatorVal).click();

    await util.loginHelperAnotherUser(page, userAccount2, password);
    await page.getByTestId('createNewConversationButton').click();
    await page.getByTestId('joinABotMenuItem').click();
    await page.getByTestId('enterChatIDLabel').fill(chatId as string);

    await page.getByTestId('joinChatButton').click();

    await page.waitForTimeout(util.ChatStateChangeWait);
    await page.getByRole('button', { name: 'View more people.' }).click();

    const numPeople = await page.getByRole('button', { name: 'View more people.' }).textContent();
    await expect(numPeople).toEqual("+2");

    await util.postUnitTest(page);
}