/* eslint-disable testing-library/prefer-screen-queries */
import { expect, test } from '@playwright/test';

const LLMresponsetimeout = 120000; // LLM can take a while to respond, wait upto 2 mins
const ChatStateChangeWait = 500;

/*
This is a test suite to test the functionality of the copilot sample app.
The Test suite goes through a bunch of sub-tests in a single long running test; 
Running the tests individually and asynchronously can confuse the LLM when multiple 
tests ask the LLM to respond to them.
This incidentally also helps to simulate a longer running chat experience. 
There are a number of smaller sub-tests in this unit test:
- Server is running
- User login
- Page has correct title
- Send a message to the bot, and expect a response
- Chat History check
- SK Skill test: joke and fun fact
- Change chat title
- Document upload
- Plan generation and execution for the Klarna plugin
- Plan generation and execution for the Jira plugin 
- Plan generation and execution for the Github plugin 
*/
test.describe('Copilot Chat App Test Suite', () => {
    test('Server Health', async ({ page }) => { await ServerHealth(page) });
    test('Long Running Chat Test', async ({ page }) => { 
        test.setTimeout(300000);
        await LongRunningChatTest(page) });
});

async function ServerHealth( page ) {
    // Make sure the server is running.
    await page.goto('https://localhost:40443/healthz');
    await expect(page.getByText('Healthy')).toBeDefined();
}

async function LoginHelper(page) {
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
}

async function BasicBotResponses( page ) {    
    // Send a message to the bot and wait for the response.
    const responsePromise1 = page.waitForResponse('**/chat',  {timeout : LLMresponsetimeout});
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill('Can you tell me a funny joke about penguins?');
    await page.locator('#chat-input').press('Enter');
    await responsePromise1;

    // Send a message to the bot and wait for the response.
    await page.waitForTimeout(ChatStateChangeWait);
    const responsePromise2 = page.waitForResponse('**/chat', {timeout : LLMresponsetimeout});
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill('Tell me a fun fact about the cosmos!');
    await page.locator('#chat-input').press('Enter');
    await responsePromise2;

    // Expect the chat history to contain 7 messages (both user messages and bot responses).
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect((await chatHistoryItems.all()).length).toBe(5);

    // Expect the last message to be the bot's response.
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
}

async function ChatTitleChange(page) {
    await page.getByRole('button', { name: 'Edit conversation name' }).click();
    await page.locator('input[type="text"]').fill('Copilot Unit Tests');
    await page.locator('input[type="text"]').press('Enter');
}

async function DocumentUpload(page) {    
    const testFilename = 'Lorem_ipsum.pdf';
    const testFilepath = './../importdocument/sample-docs/' + testFilename;    
    await page.setInputFiles("input[type='file']", testFilepath)
    await page.getByRole('tab', { name: 'Files' }).click(); // Go to the file page
    await page.getByRole('cell', { name: testFilename }).locator('path') // Check if corresponding cell for the file exists after upload
    await page.getByRole('tab', { name: 'Chat' }).click(); // Go back to the chat page

    // Wait 3 seconds for document upload; Once document uploads the chat state changes
    // and this can introduce non deterministic behavior depending on when the state change happens.
    // So we wait to skew towards more determinism
    await page.waitForTimeout(3000);
}

async function KlarnaTest(page) {
    // Plan generation and execution using Klarna (doesn't require auth)

    // Enable Klarna
    await page.locator('div').filter({ hasText: /^DB$/ }).getByRole('button').click();
    await page.getByRole('group').filter({ hasText: 'Klarna ShoppingKlarnaEnableSearch' }).getByRole('button', { name: 'Enable plugin' }).click();
    await page.getByRole('button', { name: 'Enable', exact: true }).click();
    await page.locator('.fui-DialogTitle__action > .fui-Button').click();

    // Try using Klarna by sending a request to the bot and wait for the response.
    await page.waitForTimeout(ChatStateChangeWait);
    const responsePromiseKlarnaQuery1 = page.waitForResponse('**/chat', {timeout : LLMresponsetimeout}); 
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill('Can you get me a list of prices of surface notebooks?');
    await page.locator('#chat-input').press('Enter');    
    await responsePromiseKlarnaQuery1;

    // Try executing the plan that is returned
    var buttonLocator = page.getByRole('button', { name: 'Yes, proceed' });
    buttonLocator.click();
    
    // Wait for LLM to respond to request by executing the plan
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout}); 

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
    // Specifically accessing the us site of klarna so any results should have a dollar sign
    await expect(chatHistoryItems.last()).toContainText('$');
}

async function JiraTest(page) {
    // Plan generation and execution using Jira (requires auth)

    // Enable Jira
    await page.locator('div').filter({ hasText: /^DB$/ }).getByRole('button').click();
    await page.getByRole('group').filter({ hasText: 'JiraAtlassianEnableAuthorize' }).getByRole('button', { name: 'Enable plugin' }).click();
    
    // Enter Auth Credentials and server url
    await page.getByPlaceholder('Enter your Jira email').fill(process.env.REACT_APP_TEST_JIRA_EMAIL as string);
    await page.getByPlaceholder('Enter your Jira Personal Access Token').fill(process.env.REACT_APP_TEST_JIRA_ACCESS_TOKEN as string);
    await page.getByPlaceholder('Enter the server url').fill(process.env.REACT_APP_TEST_JIRA_SERVER_URL as string);
    
    await page.getByRole('button', { name: 'Enable', exact: true }).click();
    await page.locator('.fui-DialogTitle__action > .fui-Button').click();
    
    // Try using Jira by sending a request to the bot and wait for it to respond.
    await page.waitForTimeout(ChatStateChangeWait);
    const responsePromiseJiraQuery1 = page.waitForResponse('**/chat', {timeout : LLMresponsetimeout}); 
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill('Can you Get Issue details about SKTES-1 from jira ?');
    await page.locator('#chat-input').press('Enter');    
    await responsePromiseJiraQuery1;

    // Try executing the plan that is returned
    var buttonLocator = page.getByRole('button', { name: 'Yes, proceed' });
    buttonLocator.click();
    
    // Wait for LLM to respond to request by executing the plan
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout}); 

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
    await expect(chatHistoryItems.last()).toContainText('SKTES');
}

async function GithubTest(page) {
    // Plan generation and execution using Jira (requires auth)

    // Enable Jira
    await page.locator('div').filter({ hasText: /^DB$/ }).getByRole('button').click();
    await page.getByRole('group').filter({ hasText: 'GitHubMicrosoftEnableIntegrate' }).getByRole('button', { name: 'Enable plugin' }).click();
    
    // Enter Auth Credentials and server url
    await page.getByPlaceholder('Enter your GitHub Personal Access Token').fill(process.env.REACT_APP_TEST_GITHUB_ACCESS_TOKEN as string);
    await page.getByPlaceholder('Enter the account owner of repository').fill(process.env.REACT_APP_TEST_GITHUB_ACCOUNT_OWNER as string);
    await page.getByPlaceholder('Enter the name of repository').fill(process.env.REACT_APP_TEST_GITHUB_REPOSITORY_NAME as string);
    
    await page.getByRole('button', { name: 'Enable', exact: true }).click();
    await page.locator('.fui-DialogTitle__action > .fui-Button').click();
    
    // Try using Github by sending a request to the bot and wait for it to respond.
    await page.waitForTimeout(ChatStateChangeWait);
    const responsePromiseGithubQuery1 = page.waitForResponse('**/chat', {timeout : LLMresponsetimeout}); 
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill('List the 5 most recent open pull requests');
    await page.locator('#chat-input').press('Enter');    
    await responsePromiseGithubQuery1;

    // Try executing the plan that is returned
    var buttonLocator = page.getByRole('button', { name: 'Yes, proceed' });
    buttonLocator.click();
    
    // Wait for LLM to respond to request by executing the plan
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout}); 

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
}

async function LongRunningChatTest(page) {
    await LoginHelper(page);
    await BasicBotResponses(page);
    await ChatTitleChange(page);
    await DocumentUpload(page);
    await KlarnaTest(page);
    await JiraTest(page);
    await GithubTest(page);
}