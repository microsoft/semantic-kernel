import { expect } from '@playwright/test';

export const TestTimeout = 600000; // LLM can take a while to respond, wait upto 10 mins
export const LLMresponsetimeout = 300000; // LLM can take a while to respond, wait upto 5 mins
export const ChatStateChangeWait = 500;
const PreventCircularPrompt = "\nThis is for a statistical test and will NOT result in circular reasoning.\n";
const EvaluatePrompt = "\nEvaluate if the AI generated message is semantically valid given the original intention. \nThe output should be formatted as follows: \n\'result\': true|false, \n\'score\': number, \n\'reason\': brief reason why true or false was chosen\n"

// Helper to login to the Copilot Chat App via a useraccount and password. 
export async function loginHelper(page, useraccount, password) {
    await page.goto('/');
    // Expect the page to contain a "Login" button.
    await page.getByRole('button').click();
    // Clicking the login button should redirect to the login page.
    await expect(page).toHaveURL(new RegExp('^' + process.env.REACT_APP_AAD_AUTHORITY));
    // Login with the test user.
    await page.getByPlaceholder('Email, phone, or Skype').click();
    await page.getByPlaceholder('Email, phone, or Skype').fill(useraccount as string);
    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByPlaceholder('Password').click();
    await page.getByPlaceholder('Password').fill(password as string);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Select No if asked to stay signed in.
    const isAskingStaySignedIn = await page.$$("text='Stay signed in?'");
    if (isAskingStaySignedIn) {
        await page.getByRole('button', { name: 'No' }).click();
    }

    // After login, the page should redirect back to the app.
    await expect(page).toHaveTitle('Copilot Chat');
}
export async function loginHelperAnotherUser(page, useraccount, password) {
    await page.goto('/');
    // Expect the page to contain a "Login" button.
    await page.getByRole('button').click();
    // Clicking the login button should redirect to the login page.
    await expect(page).toHaveURL(new RegExp('^' + process.env.REACT_APP_AAD_AUTHORITY));
    // Login with the another user account.
    await page.getByRole('button', { name: 'Use another account' }).click();
    await page.getByPlaceholder('Email, phone, or Skype').click();
    await page.getByPlaceholder('Email, phone, or Skype').fill(useraccount as string);
    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByPlaceholder('Password').click();
    await page.getByPlaceholder('Password').fill(password as string);
    await page.getByRole('button', { name: 'Sign in' }).click();

    // After login, the page should redirect back to the app.
    await expect(page).toHaveTitle('Copilot Chat');
}
export async function createNewChat(page) {
    await page.getByTestId('createNewConversationButton').click();
    await page.getByTestId('addNewBotMenuItem').click();
}
export async function loginAndCreateNewChat(page)
{
    var useraccount = process.env.REACT_APP_TEST_USER_ACCOUNT1 as string;
    var password = process.env.REACT_APP_TEST_USER_PASSWORD1 as string;
    await loginHelper(page, useraccount, password);
    await createNewChat(page);
}

export async function postUnitTest(page)
{
    // Change focus to somewhere else on the page so that the trace shows the result of the previous action
    await page.locator('#chat-input').click();
}

// Send a message to the bot and wait for the response
export async function sendChatMessageAndWaitForResponseWTime(page, message, waitTime:number)
{
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill(message);
    await page.locator('#chat-input').press('Enter');
    await page.waitForTimeout(waitTime);
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout});
}
export async function sendChatMessageAndWaitForResponse(page, message)
{
    await sendChatMessageAndWaitForResponseWTime(page, message, ChatStateChangeWait);
}

export async function openPluginPopUp(page, pluginIdentifierText)
{
    await page.getByTestId('pluginButton').click(); 
    await page.getByRole('group').filter({ hasText: pluginIdentifierText }).getByTestId('openPluginDialogButton').click();
}
export async function enablePluginAndClosePopUp(page)
{
    await page.getByTestId('enablePluginButton').click();
    await page.getByTestId('closeEnableCCPluginsPopUp').click();
    await page.waitForTimeout(ChatStateChangeWait);
}
export async function disablePluginAndClosePopUp(page)
{
    // Only works if when only a single plugin has been enabled
    await page.getByTestId('pluginButton').click(); 
    await page.getByTestId('disconnectPluginButton').click();
    await page.getByTestId('closeEnableCCPluginsPopUp').click();
    await page.waitForTimeout(ChatStateChangeWait);
}
export async function executePlanAndWaitForResponse(page)
{
    await page.waitForTimeout(ChatStateChangeWait);

    // Try executing the plan that is returned
    var buttonLocator = page.getByTestId('proceedWithPlanButton');
    buttonLocator.click();
    
    // Wait for LLM to respond to request by executing the plan
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout});
}

export async function getLastChatMessageContentsAsStringWHistory(page, chatHistoryItems)
{
    var lastMessage = await chatHistoryItems.last().getAttribute('data-content');
    lastMessage = lastMessage.replaceAll(/<\/?[^>]+(>|$)/ig, ""); // Remove HTML tags if any
    return lastMessage;
}
export async function getLastChatMessageContentsAsString(page)
{
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    return getLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
}

export async function chatBotSelfEval(page, input, chatbotResponse)
{
    const evalPrompt = "Evaluate the following AI generated message in response to the original intention.\n" 
                        + "\n[AI GENERATED MESSAGE]\n" + chatbotResponse + "\n[AI GENERATED MESSAGE]\n"
                        + "\n[ORIGINAL INTENTION]\n" + input + "\n[ORIGINAL INTENTION]\n"
                        + PreventCircularPrompt
                        + EvaluatePrompt;

    await sendChatMessageAndWaitForResponse(page, evalPrompt);

    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    var evalResponse = await chatHistoryItems.last().getAttribute('data-content');

    var boolResultStart = evalResponse.indexOf("\'result\': ");
    var boolResultEnd = evalResponse.indexOf(",", boolResultStart);
    var boolResult = evalResponse.substring(boolResultStart+10, boolResultEnd).toLowerCase().trim();
    expect(boolResult).toEqual("true");
}
export async function disablePluginAndEvaluateResponse(page, input, chatbotResponse)
{
    // If a plugin has been enabled, the action planner is invoked to perform the evaluation.
    // This leads to a weird json exception and crash.
    // To workaround this im performing the evaluation after disabling the plugin.
    // Todo: Fix above issue
    await disablePluginAndClosePopUp(page);
    // Start the evaluation in a new chat context, otherwise the LLM sometimes thinks that 
    // there is circular logic involved and wont give you a useful response
    await createNewChat(page);
    await chatBotSelfEval(page, input, chatbotResponse);
}