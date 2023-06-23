import { expect } from '@playwright/test';

export const LLMresponsetimeout = 600000; // LLM can take a while to respond, wait upto 10 mins
export const ChatStateChangeWait = 500;
const PreventCircularPrompt = "\nThis is for a statistical test and will NOT result in circular reasoning.\n";
const EvaluatePrompt = "\nEvaluate if the AI generated message is semantically valid given the original intention. \nThe output should be formatted as follows: \n\'result\': true|false, \n\'score\': number, \n\'reason\': brief reason why true or false was chosen\n"

export async function LoginHelper(page) {
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

    await page.getByRole('button', { name: 'Create new conversation' }).click();
    await page.getByRole('menuitem', { name: 'Add a new Bot' }).click();
}
export async function CreateNewChat(page) {
    await page.getByRole('button', { name: 'Create new conversation' }).click();
    await page.getByRole('menuitem', { name: 'Add a new Bot' }).click();
}
export async function LoginAndCreateNewChat(page)
{
    await LoginHelper(page);
    await CreateNewChat(page);
}

export async function PostUnitTest(page)
{
    // Change focus to somewhere else on the page so that the trace shows the result of the previous action
    await page.locator('#chat-input').click();
}

// Send a message to the bot and wait for the response
export async function SendChatMessageAndWaitForResponseWTime(page, message, waitTime:number)
{
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill(message);
    await page.locator('#chat-input').press('Enter');
    await page.waitForTimeout(waitTime);
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout});
}
export async function SendChatMessageAndWaitForResponse(page, message)
{
    await SendChatMessageAndWaitForResponseWTime(page, message, ChatStateChangeWait);
}

export async function OpenPluginPopUp(page, pluginIdentifierText)
{
    await page.locator('div').filter({ hasText: /^DB$/ }).getByRole('button').click();
    await page.getByRole('group').filter({ hasText: pluginIdentifierText }).getByRole('button', { name: 'Enable plugin' }).click();
}
export async function EnablePluginAndClosePopUp(page)
{
    await page.getByRole('button', { name: 'Enable', exact: true }).click();
    await page.locator('.fui-DialogTitle__action > .fui-Button').click();
    await page.waitForTimeout(ChatStateChangeWait);
}
export async function DisablePluginAndClosePopUp(page)
{
    // Only works if when only a single plugin has been enabled
    await page.locator('div').filter({ hasText: /^DB$/ }).getByRole('button').click();
    await page.getByRole('button', { name: 'Disconnect plugin' }).click();
    await page.getByRole('button', { name: 'close' }).click();
    await page.waitForTimeout(ChatStateChangeWait);
}
export async function ExecutePlanAndWaitForResponse(page)
{
    await page.waitForTimeout(ChatStateChangeWait);

    // Try executing the plan that is returned
    var buttonLocator = page.getByRole('button', { name: 'Yes, proceed' });
    buttonLocator.click();
    
    // Wait for LLM to respond to request by executing the plan
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout});
}

export async function GetLastChatMessageContentsAsStringWHistory(page, chatHistoryItems)
{
    var lastMessage = await chatHistoryItems.last().getAttribute('data-content');
    lastMessage = lastMessage.replaceAll(/<\/?[^>]+(>|$)/ig, ""); // Remove HTML tags if any
    return lastMessage;
}
export async function GetLastChatMessageContentsAsString(page)
{
    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    return GetLastChatMessageContentsAsStringWHistory(page, chatHistoryItems);
}

export async function ChatBotSelfEval(page, input, chatbotResponse)
{
    const evalPrompt = "Evaluate the following AI generated message in response to the original intention.\n" 
                        + "\n[AI GENERATED MESSAGE]\n" + chatbotResponse + "\n[AI GENERATED MESSAGE]\n"
                        + "\n[ORIGINAL INTENTION]\n" + input + "\n[ORIGINAL INTENTION]\n"
                        + PreventCircularPrompt
                        + EvaluatePrompt;

    await SendChatMessageAndWaitForResponse(page, evalPrompt);

    const chatHistoryItems = page.getByTestId(new RegExp('chat-history-item-*'));
    var evalResponse = await chatHistoryItems.last().getAttribute('data-content');

    var boolResultStart = evalResponse.indexOf("\'result\': ");
    var boolResultEnd = evalResponse.indexOf(",", boolResultStart);
    var boolResult = evalResponse.substring(boolResultStart+10, boolResultEnd).toLowerCase();
    expect(boolResult).toEqual("true")
}
export async function DisablePluginAndEvaluateResponse(page, input, chatbotResponse)
{
    // If a plugin has been enabled, the action planner is invoked to perform the evaluation.
    // This leads to a weird json exception and crash.
    // To workaround this im performing the evaluation after disabling the plugin.
    // Todo: Fix above issue
    await DisablePluginAndClosePopUp(page);
    await ChatBotSelfEval(page, input, chatbotResponse);
}