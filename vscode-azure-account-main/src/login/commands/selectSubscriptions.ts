/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IActionContext } from "@microsoft/vscode-azext-utils";
import { CancellationTokenSource, commands, ConfigurationTarget, QuickPickItem, window, workspace, WorkspaceConfiguration } from "vscode";
import { AzureSubscription } from "../../azure-account.api";
import { extensionPrefix, resourceFilterSetting } from "../../constants";
import { ext } from "../../extensionVariables";
import { localize } from "../../utils/localize";
import { openUri } from "../../utils/openUri";
import { addFilter, removeFilter } from "../filters";
import { getCurrentTarget } from "../getCurrentTarget";
import { ISubscriptionItem } from "../subscriptionTypes";

export async function selectSubscriptions(context: IActionContext): Promise<unknown> {
	if (!(await ext.loginHelper.api.waitForSubscriptions())) {
		context.telemetry.properties.outcome = 'notLoggedIn';
		return commands.executeCommand('azure-account.askForLogin');
	}

	try {
		const azureConfig: WorkspaceConfiguration = workspace.getConfiguration(extensionPrefix);
		const resourceFilter: string[] = (azureConfig.get<string[]>(resourceFilterSetting) || ['all']).slice();
		let filtersChanged: boolean = false;

		const subscriptions = ext.loginHelper.subscriptionsTask
			.then(list => getSubscriptionItems(list, resourceFilter));
		const source: CancellationTokenSource = new CancellationTokenSource();
		const cancellable: Promise<ISubscriptionItem[]> = subscriptions.then(s => {
			if (!s.length) {
				context.telemetry.properties.outcome = 'noSubscriptionsFound';
				source.cancel();
				showNoSubscriptionsFoundNotification(context);
			}
			return s;
		});
		const picks: QuickPickItem[] | undefined = await window.showQuickPick(cancellable, { canPickMany: true, placeHolder: 'Select Subscriptions' }, source.token);
		if (picks) {
			if (resourceFilter[0] === 'all') {
				resourceFilter.splice(0, 1);
				for (const subscription of await subscriptions) {
					addFilter(resourceFilter, subscription);
				}
			}
			for (const subscription of await subscriptions) {
				if (subscription.picked !== (picks.indexOf(subscription) !== -1)) {
					filtersChanged = true;
					if (subscription.picked) {
						removeFilter(resourceFilter, subscription);
					} else {
						addFilter(resourceFilter, subscription);
					}
				}
			}
		}

		if (filtersChanged) {
			await updateConfiguration(azureConfig, resourceFilter);
		}
		context.telemetry.properties.outcome = 'success';
	} catch (error) {
		context.telemetry.properties.outcome = 'error';
		throw error;
	}
}

function getSubscriptionItems(subscriptions: AzureSubscription[], resourceFilter: string[]): ISubscriptionItem[] {
	return subscriptions.map(subscription => {
		const picked: boolean = resourceFilter.indexOf(`${subscription.session.tenantId}/${subscription.subscription.subscriptionId}`) !== -1 || resourceFilter[0] === 'all';
		return <ISubscriptionItem>{
			label: subscription.subscription.displayName,
			// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
			description: subscription.subscription.subscriptionId!,
			subscription,
			picked,
		};
	});
}

async function updateConfiguration(azureConfig: WorkspaceConfiguration, resourceFilter: string[]): Promise<void> {
	const resourceFilterConfig = azureConfig.inspect<string[]>(resourceFilterSetting);
	const target: ConfigurationTarget = getCurrentTarget(resourceFilterConfig);
	await azureConfig.update(resourceFilterSetting, resourceFilter[0] !== 'all' ? resourceFilter : undefined, target);
}

function showNoSubscriptionsFoundNotification(context: IActionContext): void {
	const noSubscriptionsFound = localize('azure-account.noSubscriptionsFound', 'No subscriptions were found. Setup your account if you have yet to do so or check out our troubleshooting page for common solutions to this problem.');
	const setupAccount = localize('azure-account.setupAccount', 'Setup Account');
	const openTroubleshooting = localize('azure-account.openTroubleshooting', 'Open Troubleshooting');
	void window.showInformationMessage(noSubscriptionsFound, setupAccount, openTroubleshooting).then(response => {
		if (response === setupAccount) {
			context.telemetry.properties.setupAccount = 'true';
			void openUri('https://aka.ms/AAeyf8k');
		} else if (response === openTroubleshooting) {
			context.telemetry.properties.openTroubleshooting = 'true';
			void openUri('https://aka.ms/AAevvhr');
		}
	});
}
