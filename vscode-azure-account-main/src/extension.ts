/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IActionContext, apiUtils, callWithTelemetryAndErrorHandling, createApiProvider, createAzExtLogOutputChannel, createExperimentationService, registerCommand, registerReportIssueCommand, registerUIExtensionVariables } from '@microsoft/vscode-azext-utils';
import axios from 'axios';
import { ConfigurationTarget, ExtensionContext, Uri, WorkspaceConfiguration, env, window, workspace } from 'vscode';
import { AzureAccountExtensionApi } from './azure-account.api';
import { manageAccount } from './commands/manageAccount';
import { cloudSetting, displayName, extensionPrefix, showSignedInEmailSetting } from './constants';
import { ext } from './extensionVariables';
import { AzureAccountLoginHelper } from './login/AzureAccountLoginHelper';
import { checkSettingsOnStartup } from './login/checkSettingsOnStartup';
import { askForLogin } from './login/commands/askForLogin';
import { loginToCloud } from './login/commands/loginToCloud';
import { selectSubscriptions } from './login/commands/selectSubscriptions';
import { selectTenant } from './login/commands/selectTenant';
import { UriEventHandler } from './login/exchangeCodeForToken';
import { updateFilters } from './login/updateFilters';
import { updateSubscriptionsAndTenants } from './login/updateSubscriptions';
import { survey } from './nps';
import { localize } from './utils/localize';
import { logErrorMessage } from './utils/logErrorMessage';
import { setupAxiosLogging } from './utils/logging/axios/AxiosNormalizer';
import { getSettingValue } from './utils/settingUtils';

const enableLogging: boolean = false;

export async function activateInternal(context: ExtensionContext, perfStats: { loadStartTime: number; loadEndTime: number }): Promise<apiUtils.AzureExtensionApiProvider> {
	ext.context = context;
	ext.outputChannel = createAzExtLogOutputChannel(displayName);
	ext.uriEventHandler = new UriEventHandler();
	context.subscriptions.push(ext.outputChannel);
	context.subscriptions.push(window.registerUriHandler(ext.uriEventHandler));
	registerUIExtensionVariables(ext);
	setupAxiosLogging(axios, ext.outputChannel);

	await callWithTelemetryAndErrorHandling('azure-account.activate', async (activateContext: IActionContext) => {
		activateContext.telemetry.properties.isActivationEvent = 'true';
		activateContext.telemetry.properties.activationTime = String((perfStats.loadEndTime - perfStats.loadStartTime) / 1000);

		ext.experimentationService = await createExperimentationService(context);
		ext.loginHelper = new AzureAccountLoginHelper(context, activateContext);

		await checkSettingsOnStartup(context, activateContext, ext.loginHelper);

		await migrateEnvironmentSetting();
		if (enableLogging) {
			logDiagnostics(context, ext.loginHelper.api);
		}
		context.subscriptions.push(createStatusBarItem(context, ext.loginHelper.api));
		registerCommand('azure-account.loginToCloud', loginToCloud);
		registerCommand('azure-account.selectSubscriptions', selectSubscriptions);
		registerCommand('azure-account.selectTenant', selectTenant);
		registerCommand('azure-account.askForLogin', askForLogin);
		registerCommand('azure-account.createAccount', createAccount);
		registerCommand('azure-account.manageAccount', manageAccount);
		context.subscriptions.push(ext.loginHelper.api.onSessionsChanged(updateSubscriptionsAndTenants));
		context.subscriptions.push(ext.loginHelper.api.onSubscriptionsChanged(() => updateFilters()));
		registerReportIssueCommand('azure-account.reportIssue');

		survey(context);
	});

	return Object.assign(ext.loginHelper.legacyApi, createApiProvider([ext.loginHelper.api]));
}

async function migrateEnvironmentSetting() {
	const configuration: WorkspaceConfiguration = workspace.getConfiguration(extensionPrefix);
	const configInfo = configuration.inspect(cloudSetting);

	async function migrateSetting(oldValue: string, newValue: string): Promise<void> {
		if (configInfo?.globalValue === oldValue) {
			await configuration.update(cloudSetting, newValue, ConfigurationTarget.Global);
		}
		if (configInfo?.workspaceValue === oldValue) {
			await configuration.update(cloudSetting, newValue, ConfigurationTarget.Workspace);
		}
		if (configInfo?.workspaceFolderValue === oldValue) {
			await configuration.update(cloudSetting, newValue, ConfigurationTarget.WorkspaceFolder);
		}
	}

	await migrateSetting('Azure', 'AzureCloud');
	await migrateSetting('AzureChina', 'AzureChinaCloud');
}

function logDiagnostics(context: ExtensionContext, api: AzureAccountExtensionApi) {
	const subscriptions = context.subscriptions;
	subscriptions.push(api.onStatusChanged(status => {
		ext.outputChannel.appendLog(`onStatusChanged: ${status}`);
	}));
	subscriptions.push(api.onSessionsChanged(() => {
		ext.outputChannel.appendLog(`onSessionsChanged: ${api.sessions.length} ${api.status}`);
	}));
	(async () => {
		ext.outputChannel.appendLog(`waitForLogin: ${await api.waitForLogin()} ${api.status}`);
	})().catch(logErrorMessage);
	subscriptions.push(api.onSubscriptionsChanged(() => {
		ext.outputChannel.appendLog(`onSubscriptionsChanged: ${api.subscriptions.length}`);
	}));
	(async () => {
		ext.outputChannel.appendLog(`waitForSubscriptions: ${await api.waitForSubscriptions()} ${api.subscriptions.length}`);
	})().catch(logErrorMessage);
	subscriptions.push(api.onFiltersChanged(() => {
		ext.outputChannel.appendLog(`onFiltersChanged: ${api.filters.length}`);
	}));
	(async () => {
		ext.outputChannel.appendLog(`waitForFilters: ${await api.waitForFilters()} ${api.filters.length}`);
	})().catch(logErrorMessage);
}

function createAccount() {
	return env.openExternal(Uri.parse('https://azure.microsoft.com/en-us/free/?utm_source=campaign&utm_campaign=vscode-azure-account&mktingSource=vscode-azure-account'));
}

function createStatusBarItem(context: ExtensionContext, api: AzureAccountExtensionApi) {
	const statusBarItem = window.createStatusBarItem('azure-account.status');
	statusBarItem.name = localize('azure-account.status', 'Azure Account Status');
	statusBarItem.command = "azure-account.manageAccount";
	function updateStatusBar() {
		switch (api.status) {
			case 'LoggingIn':
				statusBarItem.text = localize('azure-account.loggingIn', "Azure: Signing in...");
				statusBarItem.show();
				break;
			case 'LoggedIn':
				if (api.sessions.length) {
					const showSignedInEmail: boolean | undefined = getSettingValue(showSignedInEmailSetting);
					statusBarItem.text = showSignedInEmail ? localize('azure-account.loggedIn', "Azure: {0}", api.sessions[0].userId) : localize('azure-account.loggedIn', "Azure: Signed In");
					statusBarItem.show();
				}
				break;
			default:
				statusBarItem.hide();
				break;
		}
	}
	context.subscriptions.push(
		statusBarItem,
		api.onStatusChanged(updateStatusBar),
		api.onSessionsChanged(updateStatusBar),
		workspace.onDidChangeConfiguration(updateStatusBar)
	);
	updateStatusBar();
	return statusBarItem;
}

export function deactivateInternal(): void {
	return;
}