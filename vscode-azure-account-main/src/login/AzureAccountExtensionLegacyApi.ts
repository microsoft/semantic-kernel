/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Event } from 'vscode';
import * as legacyTypes from '../azure-account.legacy.api';
import { OSName } from '../cloudConsole/OS.4';
import { AzureAccountExtensionApi } from './AzureAccountExtensionApi';

export class AzureAccountExtensionLegacyApi implements legacyTypes.AzureAccount {
	public onStatusChanged: Event<legacyTypes.AzureLoginStatus>;
	public onFiltersChanged: Event<void>;
	public onSessionsChanged: Event<void>;
	public onSubscriptionsChanged: Event<void>;

	constructor(private api: AzureAccountExtensionApi) {
		this.onStatusChanged = api.onStatusChanged;
		this.onFiltersChanged = api.onFiltersChanged;
		this.onSessionsChanged = api.onSessionsChanged;
		this.onSubscriptionsChanged = api.onSubscriptionsChanged;
	}

	public get status(): legacyTypes.AzureLoginStatus {
		return this.api.status;
	}

	public get filters(): legacyTypes.AzureResourceFilter[] {
		return <legacyTypes.AzureResourceFilter[]>this.api.filters;
	}

	public get sessions(): legacyTypes.AzureSession[] {
		return <legacyTypes.AzureSession[]>this.api.sessions;
	}

	public get subscriptions(): legacyTypes.AzureSubscription[] {
		return <legacyTypes.AzureSubscription[]>this.api.subscriptions;
	}

	public async waitForFilters(): Promise<boolean> {
		return await this.api.waitForFilters(true);
	}

	public async waitForLogin(): Promise<boolean> {
		return await this.api.waitForLogin(true);
	}

	public async waitForSubscriptions(): Promise<boolean> {
		return await this.api.waitForSubscriptions(true);
	}

	public createCloudShell(os: OSName): legacyTypes.CloudShell {
		return <legacyTypes.CloudShell>this.api.createCloudShell(os);
	}
}
