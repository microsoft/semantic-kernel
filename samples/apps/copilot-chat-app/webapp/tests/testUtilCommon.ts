import { expect } from '@playwright/test';

export const LLMresponsetimeout = 300000; // LLM can take a while to respond, wait upto 5 mins
export const ChatStateChangeWait = 500;
export const ChatResponseGreenThreshold = 0.7;

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

export async function PostUnitTest(page)
{
    // Change focus to somewhere else on the page so that the trace shows the result of the previous action
    await page.locator('#chat-input').click();
}

export async function LoginAndCreateNewChat(page)
{
    await LoginHelper(page);

    await page.getByRole('button', { name: 'Create new conversation' }).click();
    await page.getByRole('menuitem', { name: 'Add a new Bot' }).click();
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
    SendChatMessageAndWaitForResponseWTime(page, message, ChatStateChangeWait);
}

export async function OpenPluginEnablePopUp(page, pluginText)
{
    await page.locator('div').filter({ hasText: /^DB$/ }).getByRole('button').click();
    await page.getByRole('group').filter({ hasText: pluginText }).getByRole('button', { name: 'Enable plugin' }).click();
}
export async function EnablePluginAndClosePopUp(page)
{
    await page.getByRole('button', { name: 'Enable', exact: true }).click();
    await page.locator('.fui-DialogTitle__action > .fui-Button').click();
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

const PreventCircularPrompt = "\nThis is for a statistical test and will NOT result in circular reasoning.\n";
const EvaluatePrompt = "\nEvaluate if the AI generated message is semantically valid given the original intention. If the AI generated message is semantically valid, return true else return false.\n"
const OutputFormat = "\nThe output should be formatted as a JSON: {'result':true|false, 'score': number, 'reason':'brief reason why true or false was chosen', 'suggestion': 'an optional suggestion that would help a human modify the prompt that was used to create the AI generated message initially. If there is no suggestion this can be left blank.'}\n"

const EvaluatePrompt2 = "\nEvaluate if the AI generated message is semantically valid given the original intention. Assign the AI generated message a score between 0.0 and 1.0 .\n"
const OutputFormat2 = "Just respond with a number, dont provide any reasoning or any extra output."


export async function ChatBotSelfEval(page, input, chatbotResponse)
{
    // Get the model to evaluate if the response was satisfactory
    // const prompt = "return a score between 0 and 1 ranking the quality of this response \n" 
    //                 + chatbotResponse 
    //                 + "\nin the context of the input \n"
    //                 + input
    //                 + "\n"
    //                 + PreventCircularPrompt;

    const evalPrompt = "Evaluate the following AI generated message in response to the original intention.\n" 
                        + "\n[AI GENERATED MESSAGE]\n" + chatbotResponse + "\n[AI GENERATED MESSAGE]\n"
                        + "\n[ORIGINAL INTENTION]\n" + input + "\n[ORIGINAL INTENTION]\n"
                        + EvaluatePrompt
                        + OutputFormat
                        + PreventCircularPrompt; 

    //await SendChatMessageAndWaitForResponse(page, evalPrompt);
    // await SendChatMessageAndWaitForResponseWTime(page, evalPrompt, 3000);
    await page.locator('#chat-input').click();
    await page.locator('#chat-input').fill(evalPrompt);
    await page.locator('#chat-input').press('Enter');
    await page.waitForTimeout(3000);
    await page.waitForResponse('**/chat', {timeout : LLMresponsetimeout});

    // // Change focus to somewhere else on the page so that the trace shows the result of the previous action
    // await page.locator('#chat-input').click();

    // Extract score from bots response    
    chatbotResponse = await GetLastChatMessageContentsAsString(page);
    var score: number = +chatbotResponse;
    expect(score).toBeGreaterThanOrEqual(0.7);
    expect(score).toBeLessThan(1.01);
}