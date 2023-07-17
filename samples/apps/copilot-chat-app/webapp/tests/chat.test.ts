/* eslint-disable testing-library/prefer-screen-queries */
import { test } from '@playwright/test';
import * as util from './utils'
import * as simpletests from './testsBasic'
import * as plannertests from './testsPlanner'
import * as mutests from './testsMultiuser'

test.describe('Copilot Chat App Test Suite', () => {
    // Note: A new chat session is opened for each test so that 
    // the chat history is not polluted and the LLM is not confused.
    test.describe.configure({ mode: 'parallel' });
    
    test.describe('Basic Tests', () => {        
        // Server Tests
        test('Server Health', async ({ page }) => { 
            await simpletests.serverHealth(page) });

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
    
    test.describe('Multi-User Chat Tests', () => {
        test('Share Chat & Have Second User Join Session', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await mutests.shareAndJoinChatSessionTest(page) });
    });

    test.describe('Planner Tests', () => {        
        test('Klarna', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await plannertests.klarnaTest(page) });
            
        test('Jira', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await plannertests.jiraTest(page) });
            
        // Todo: Action Planner intermittently returns a 400 error
        // skipping test for the time being
        test.skip('Github', async ({ page }) => { 
            test.setTimeout(util.TestTimeout);
            await plannertests.githubTest(page) });
    });
});