/* eslint-disable testing-library/prefer-screen-queries */
import { expect, test } from '@playwright/test';
import * as util from './utils'
import * as simpletests from './basictests'
import * as plannertests from './plannertests'
import { multiUserTest } from './multiuserchattests'

test.describe('Copilot Chat App Test Suite', () => {
    // Note: A new chat session is opened for each test so that 
    // the chat history is not polluted and the LLM is not confused.

    test.describe('A, runs in parallel with B', () => {
        test.describe.configure({ mode: 'parallel' });
        // Server Tests
        test('Server Health', async ({ page }) => { await simpletests.serverHealth(page) });
        // Basic Operations
        test('Basic Bot Responses', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await simpletests.basicBotResponses(page) });
        test('Chat Title Change', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await simpletests.chatTitleChange(page) });
        test('Chat Document Upload', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await simpletests.documentUpload(page) });
    });
        
    test.describe('B, runs in parallel with A', () => {
        test.describe.configure({ mode: 'parallel' });
        
        // Planner Testing
        test('Planner Test: Klarna', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await plannertests.klarnaTest(page) });
        test('Planner Test: Jira', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await plannertests.jiraTest(page) });

        // Todo: Action Planner intermittently returns a 400 error
        // skipping test for the time being
        test.skip('Planner Test: Github', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await plannertests.githubTest(page) });

        // Multi-User Chat
        test('Multi-user chat', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await multiUserTest(page) });
    });
});