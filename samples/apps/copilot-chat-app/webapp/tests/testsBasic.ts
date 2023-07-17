import { expect } from '@playwright/test';
import * as util from './utils'

/*
Summary: Checks if the server is running and healthy
*/
export async function serverHealth( page ) {
    // Make sure the server is running.
    await page.goto('https://localhost:40443/healthz');
    await expect(page.getByText('Healthy')).toBeDefined();
}

/*
Summary: Tests for the following behaviour from the WebApp:
- User login
- Page has correct title
- Start New Chat
- Send a message to the bot, and expect a response
- Chat History has the correct number of messages and that the last message is from Copilot
- SK core skill testing for jokes and fun facts
*/
export async function basicBotResponses( page ) {    
    await util.loginAndCreateNewChat(page);
    
    const joke = "Can you tell me a funny joke about penguins?";
    await util.sendChatMessageAndWaitForResponse(page, joke);

    const funfact = "Tell me a fun fact about the cosmos!";
    await util.sendChatMessageAndWaitForResponse(page, funfact);

    // Expect the chat history to contain 7 messages (both user messages and bot responses).
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect((await chatHistoryItems.all()).length).toBe(5);

    // Expect the last message to be the bot's response.
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');

    await util.postUnitTest(page);
}

/*
Summary: Tests if the title for the current chat can be changed  
*/
export async function chatTitleChange(page) {
    await util.loginAndCreateNewChat(page);
    
    await page.getByTestId('editChatTitleButton').click();
    await page.locator('input[type="text"]').fill('Copilot Unit Tests');
    await page.locator('input[type="text"]').press('Enter');

    await util.postUnitTest(page);
}

/*
Summary: Tests if a single document can be uploaded and then found in the 'Files' tab  
*/
export async function documentUpload(page) {    
    await util.loginAndCreateNewChat(page);
    
    const testFilename = 'Lorem_ipsum.pdf';
    const testFilepath = './../importdocument/sample-docs/' + testFilename;    
    await page.setInputFiles("input[type='file']", testFilepath)
    
    await page.getByTestId('filesTab').click();// Go to the file page
    // Check if corresponding cell for the file exists after upload
    await page.getByRole('cell', { name: testFilename }).locator('path');
    await page.getByTestId('chatTab').click(); // Go back to the chat page

    await util.postUnitTest(page);
}