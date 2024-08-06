/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from "@azure/ms-rest-azure-env";
import { localize } from "./utils/localize";

export type AuthLibrary = 'ADAL' | 'MSAL';

export const extensionPrefix: string = 'azure';
export const authLibrarySetting: string = 'authenticationLibrary';
export const cloudSetting: string = 'cloud';
export const customCloudArmUrlSetting: string = 'customCloud.resourceManagerEndpointUrl';
export const ppeSetting: string = 'ppe';
export const resourceFilterSetting: string = 'resourceFilter';
export const showSignedInEmailSetting: string = 'showSignedInEmail';
export const tenantSetting: string = 'tenant';

export const authTimeoutSeconds: number = 5 * 60;
export const authTimeoutMs: number = authTimeoutSeconds * 1000;
export const azureCustomCloud: string = 'AzureCustomCloud';
export const azurePPE: string = 'AzurePPE';
export const cacheKey: string = 'cache';
export const clientId: string = 'aebc6443-996d-45c2-90f0-388ff96faa56';
export const commonTenantId: string = 'common';
export const displayName: string = 'Azure Account';
export const portADFS: number = 19472;
export const redirectUrlAAD: string = 'https://vscode.dev/redirect';
export const stoppedAuthTaskMessage: string = localize('azure-account.stoppedAuthTask', 'Stopped authentication task.');

export const staticEnvironments: Environment[] = [
	Environment.AzureCloud,
	Environment.ChinaCloud,
	Environment.GermanCloud,
	Environment.USGovernment
];

export const environmentLabels: Record<string, string> = {
	AzureCloud: localize('azure-account.azureCloud', 'Azure'),
	AzureChinaCloud: localize('azure-account.azureChinaCloud', 'Azure China'),
	AzureGermanCloud: localize('azure-account.azureGermanyCloud', 'Azure Germany'),
	AzureUSGovernment: localize('azure-account.azureUSCloud', 'Azure US Government'),
	[azureCustomCloud]: localize('azure-account.azureCustomCloud', 'Azure Custom Cloud'),
	[azurePPE]: localize('azure-account.azurePPE', 'Azure PPE'),
};
