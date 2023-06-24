/* eslint-disable testing-library/prefer-screen-queries */
import { expect, test } from '@playwright/test';
import * as util from './testUtilCommon'

/*
This is a test suite to test the functionality of the copilot sample app.
The Test suite goes through a bunch of tests, opening a new chat session
for each test so that chat history is not polluted and the LLM isn't confused; 
Here is a list of things we test right now, either standalone or as part of another test:
- Server is running
- User login
- Page has correct title
- Send a message to the bot, and expect a response
- Chat History check
- Start New Chat
- SK Skill test: joke and fun fact
- Change chat title
- Document upload
- Plan generation and execution for the Klarna plugin
- Plan generation and execution for the Jira plugin 
- Plan generation and execution for the Github plugin 
*/
test.describe('Copilot Chat App Test Suite', () => {

   test.describe('A, runs in parallel with B', () => {
        test.describe.configure({ mode: 'parallel' });
        // Server Tests
        test('Server Health', async ({ page }) => { await ServerHealth(page) });
        // Basic Operations
        test('Basic Bot Responses', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await BasicBotResponses(page) });
        test('Chat Title Change', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await ChatTitleChange(page) });
        test('Chat Document Upload', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await DocumentUpload(page) });
    });
        
    test.describe('B, runs in parallel with A', () => {
        test.describe.configure({ mode: 'serial' });
        
        // Planner Testing
        test('Planner Test: Klarna', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await KlarnaTest(page) });
        test('Planner Test: Jira', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await JiraTest(page) });
        test('Planner Test: Github', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await GithubTest(page) });
        // Multi-User Chat
        test('Multi-user chat', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await MultiUserTest(page) });
    });
});

async function ServerHealth( page ) {
    // Make sure the server is running.
    await page.goto('https://localhost:40443/healthz');
    await expect(page.getByText('Healthy')).toBeDefined();
}

async function BasicBotResponses( page ) {    
    await util.LoginAndCreateNewChat(page);
    
    const joke = "Can you tell me a funny joke about penguins?";
    await util.SendChatMessageAndWaitForResponse(page, joke);

    const funfact = "Tell me a fun fact about the cosmos!";
    await util.SendChatMessageAndWaitForResponse(page, funfact);

    // Expect the chat history to contain 7 messages (both user messages and bot responses).
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect((await chatHistoryItems.all()).length).toBe(5);

    // Expect the last message to be the bot's response.
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');

    await util.PostUnitTest(page);
}

async function ChatTitleChange(page) {
    await util.LoginAndCreateNewChat(page);
    
    await page.getByRole('button', { name: 'Edit conversation name' }).click();
    await page.locator('input[type="text"]').fill('Copilot Unit Tests');
    await page.locator('input[type="text"]').press('Enter');

    await util.PostUnitTest(page);
}

async function DocumentUpload(page) {    
    await util.LoginAndCreateNewChat(page);
    
    const testFilename = 'Lorem_ipsum.pdf';
    const testFilepath = './../importdocument/sample-docs/' + testFilename;    
    await page.setInputFiles("input[type='file']", testFilepath)
    await page.getByRole('tab', { name: 'Files' }).click(); // Go to the file page
    await page.getByRole('cell', { name: testFilename }).locator('path') // Check if corresponding cell for the file exists after upload
    await page.getByRole('tab', { name: 'Chat' }).click(); // Go back to the chat page

    await util.PostUnitTest(page);
}

async function KlarnaTest(page) {
    await util.LoginAndCreateNewChat(page);
    
    // Plan generation and execution using Klarna (doesn't require auth)

    // Enable Klarna
    const pluginIdentifierText = 'Klarna ShoppingKlarnaEnableSearch';
    await util.OpenPluginPopUp(page, pluginIdentifierText);
    await util.EnablePluginAndClosePopUp(page);
    
    // Try using Klarna by sending a request to the bot and wait for the response.
    const klarnaQuery = "Can you get me a list of prices of surface notebooks?";
    await util.SendChatMessageAndWaitForResponse(page, klarnaQuery);
    await util.ExecutePlanAndWaitForResponse(page);

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
    
    // Specifically accessing the us site of klarna so any results should have a dollar sign
    await expect(chatHistoryItems.last()).toContainText('$');

    var chatbotResponse = await util.GetLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
    await util.DisablePluginAndEvaluateResponse(page, klarnaQuery, chatbotResponse);

    await util.PostUnitTest(page);
}

async function JiraTest(page) {
    await util.LoginAndCreateNewChat(page);

    // Plan generation and execution using Jira (requires auth)

    // Enable Jira
    await util.OpenPluginPopUp(page, 'JiraAtlassianEnableAuthorize');
    
    // Enter Auth Credentials and server url
    await page.getByPlaceholder('Enter your Jira email').fill(process.env.REACT_APP_TEST_JIRA_EMAIL as string);
    await page.getByPlaceholder('Enter your Jira Personal Access Token').fill(process.env.REACT_APP_TEST_JIRA_ACCESS_TOKEN as string);
    await page.getByPlaceholder('Enter the server url').fill(process.env.REACT_APP_TEST_JIRA_SERVER_URL as string);
    
    await util.EnablePluginAndClosePopUp(page);
    
    // Try using Jira by sending a request to the bot and wait for it to respond.
    const jiraQuery = "Can you Get Issue details about SKTES-1 from jira ?";
    await util.SendChatMessageAndWaitForResponse(page, jiraQuery);
    await util.ExecutePlanAndWaitForResponse(page);

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
    await expect(chatHistoryItems.last()).toContainText('SKTES');

    var chatbotResponse = await util.GetLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
    await util.DisablePluginAndEvaluateResponse(page, jiraQuery, chatbotResponse);
    
    await util.PostUnitTest(page);
}

async function GithubTest(page) {
    await util.LoginAndCreateNewChat(page);
    
    // Plan generation and execution using Github (requires auth)

    // Enable Github
    await util.OpenPluginPopUp(page, 'GitHubMicrosoftEnableIntegrate');
    
    // Enter Auth Credentials and server url
    await page.getByPlaceholder('Enter your GitHub Personal Access Token').fill(process.env.REACT_APP_TEST_GITHUB_ACCESS_TOKEN as string);
    await page.getByPlaceholder('Enter the account owner of repository').fill(process.env.REACT_APP_TEST_GITHUB_ACCOUNT_OWNER as string);
    await page.getByPlaceholder('Enter the name of repository').fill(process.env.REACT_APP_TEST_GITHUB_REPOSITORY_NAME as string);
    
    await util.EnablePluginAndClosePopUp(page);
    
    // Try using Github by sending a request to the bot and wait for it to respond.
    const githubQuery = "List the 5 most recent open pull requests";
    await util.SendChatMessageAndWaitForResponse(page, githubQuery);
    await util.ExecutePlanAndWaitForResponse(page);

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');

    var chatbotResponse = await util.GetLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
    await util.DisablePluginAndEvaluateResponse(page, githubQuery, chatbotResponse);

    await util.PostUnitTest(page);
}

async function MultiUserTest(page) {
    const useraccount1 = process.env.REACT_APP_TEST_USER_ACCOUNT as string;
    const useraccount2 = process.env.REACT_APP_TEST_USER_ACCOUNT2 as string;
    const password = process.env.REACT_APP_TEST_USER_PASSWORD as string;
    await util.LoginHelper(page, useraccount1, password);
    await util.CreateNewChat(page);

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

    await util.LoginHelperAnotherUser(page, useraccount2, password);
    await page.getByRole('button', { name: 'Create new conversation' }).click();
    await page.getByRole('menuitem', { name: 'Join a Bot' }).click();
    await page.getByLabel('Please enter the chat ID of the chat').fill(chatId as string);

    await page.getByRole('button', { name: 'Join' }).click();

    await page.waitForTimeout(util.ChatStateChangeWait);
    await page.getByRole('button', { name: 'View more people.' }).click();

    const numPeople = await page.getByRole('button', { name: 'View more people.' }).textContent();
    await expect(numPeople).toEqual("+2");

    await util.PostUnitTest(page);
}
