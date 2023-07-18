import { expect } from '@playwright/test';
import * as util from './utils';

/*
Summary: Tests if the Chat Copilot can use the Planner with the Klarna plugin, 
to generate a plan and execute it. Klarna doesnt require any auth credentials.   
*/
export async function klarnaTest(page) {
    await util.loginAndCreateNewChat(page);

    // Enable Klarna
    const pluginIdentifierText = 'Klarna ShoppingKlarnaEnableSearch';
    await util.openPluginPopUp(page, pluginIdentifierText);
    await util.enablePluginAndClosePopUp(page);

    // Try using Klarna by sending a request to the bot and wait for the response.
    const klarnaQuery = 'Can you get me a list of prices of surface notebooks?';
    await util.sendChatMessageAndWaitForResponse(page, klarnaQuery);
    await util.executePlanAndWaitForResponse(page);

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');

    // Specifically accessing the us site of klarna so any results should have a dollar sign
    await expect(chatHistoryItems.last()).toContainText('$');

    var chatbotResponse = await util.getLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
    await util.disablePluginAndEvaluateResponse(page, klarnaQuery, chatbotResponse);

    await util.postUnitTest(page);
}

/*
Summary: Tests if the Chat Copilot can use the Planner with the Jira plugin, 
to generate a plan and execute it. The Jira plugin uses a Basic auth header.   
*/
export async function jiraTest(page) {
    await util.loginAndCreateNewChat(page);

    // Enable Jira
    await util.openPluginPopUp(page, 'JiraAtlassianEnableAuthorize');

    // Enter Auth Credentials and server url
    await page.locator('#plugin-email-input').fill(process.env.REACT_APP_TEST_JIRA_EMAIL as string);
    await page.locator('#plugin-pat-input').fill(process.env.REACT_APP_TEST_JIRA_ACCESS_TOKEN as string);
    await page.getByPlaceholder('Enter the server url').fill(process.env.REACT_APP_TEST_JIRA_SERVER_URL as string);

    await util.enablePluginAndClosePopUp(page);

    // Try using Jira by sending a request to the bot and wait for it to respond.
    const jiraQuery = 'Can you Get Issue details about SKTES-1 from jira ?';
    await util.sendChatMessageAndWaitForResponse(page, jiraQuery);
    await util.executePlanAndWaitForResponse(page);

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');
    await expect(chatHistoryItems.last()).toContainText('SKTES');

    var chatbotResponse = await util.getLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
    await util.disablePluginAndEvaluateResponse(page, jiraQuery, chatbotResponse);

    await util.postUnitTest(page);
}

/*
Summary: Tests if the Chat Copilot can use the Planner with the Github plugin, 
to generate a plan and execute it. The Github plugin uses a PAT token for auth.   
*/
export async function githubTest(page) {
    await util.loginAndCreateNewChat(page);

    // Enable Github
    await util.openPluginPopUp(page, 'GitHubMicrosoftEnableIntegrate');

    // Enter Auth Credentials and server url
    await page.locator('#plugin-pat-input').fill(process.env.REACT_APP_TEST_GITHUB_ACCESS_TOKEN as string);
    await page
        .getByPlaceholder('Enter the account owner of repository')
        .fill(process.env.REACT_APP_TEST_GITHUB_ACCOUNT_OWNER as string);
    await page
        .getByPlaceholder('Enter the name of repository')
        .fill(process.env.REACT_APP_TEST_GITHUB_REPOSITORY_NAME as string);

    await util.enablePluginAndClosePopUp(page);

    // Try using Github by sending a request to the bot and wait for it to respond.
    const githubQuery = 'List the 5 most recent open pull requests';
    await util.sendChatMessageAndWaitForResponse(page, githubQuery);
    await util.executePlanAndWaitForResponse(page);

    // Expect the last message to be the bot's response.
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    await expect(chatHistoryItems.last()).toHaveAttribute('data-username', 'Copilot');

    var chatbotResponse = await util.getLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
    await util.disablePluginAndEvaluateResponse(page, githubQuery, chatbotResponse);

    await util.postUnitTest(page);
}
