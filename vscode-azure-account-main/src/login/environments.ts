/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from "@azure/ms-rest-azure-env";
import { Response } from "node-fetch";
import * as url from 'url';
import { commands, window, workspace, WorkspaceConfiguration } from "vscode";
import { azureCustomCloud, azurePPE, cloudSetting, customCloudArmUrlSetting, extensionPrefix, ppeSetting, staticEnvironments } from "../constants";
import { localize } from "../utils/localize";
import { fetchWithLogging } from "../utils/logging/nodeFetch/nodeFetch";
import { getSettingValue } from "../utils/settingUtils";

interface ICloudMetadata {
	portal: string;
	authentication: {
		loginEndpoint: string;
		audiences: string[];
	};
	graphAudience: string;
	graph: string;
	name: string;
	suffixes: {
		acrLoginServer: string;
		keyVaultDns: string;
		sqlServerHostname: string;
		storage: string;
	}
	batch: string;
	resourceManager: string;
	sqlManagement: string;
	gallery: string;
}

interface IResourceManagerMetadata {
	galleryEndpoint: string;
	graphEndpoint: string;
	portalEndpoint: string;
	authentication: {
		loginEndpoint: string,
		audiences: [
			string
		]
	};
}

export async function getSelectedEnvironment(): Promise<Environment> {
	const envSetting: string | undefined = getSettingValue(cloudSetting);
	return (await getEnvironments()).find(environment => environment.name === envSetting) || Environment.AzureCloud;
}

/**
 * @param includePartial Include partial environments for the sake of UI (i.e. Azure Stack). Endpoint data will be filled in later
 */
export async function getEnvironments(includePartial: boolean = false): Promise<Environment[]> {
	const metadataDiscoveryUrl: string | undefined = process.env['ARM_CLOUD_METADATA_URL'];
	if (metadataDiscoveryUrl) {
		try {
			const response: Response = await fetchWithLogging(metadataDiscoveryUrl);
			if (response.ok) {
				// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
				const endpoints: ICloudMetadata[] = await response.json();
				return endpoints.map(endpoint => {
					return {
						name: endpoint.name,
						portalUrl: endpoint.portal,
						managementEndpointUrl: endpoint.authentication.audiences[0],
						resourceManagerEndpointUrl: endpoint.resourceManager,
						activeDirectoryEndpointUrl: endpoint.authentication.loginEndpoint,
						activeDirectoryResourceId: endpoint.authentication.audiences[0],
						sqlManagementEndpointUrl: endpoint.sqlManagement,
						sqlServerHostnameSuffix: endpoint.suffixes.sqlServerHostname,
						galleryEndpointUrl: endpoint.gallery,
						batchResourceId: endpoint.batch,
						storageEndpointSuffix: endpoint.suffixes.storage,
						keyVaultDnsSuffix: endpoint.suffixes.keyVaultDns,
						validateAuthority: true
					}
				})
			}
		} catch {
			// ignore, fallback to static environments
		}
	}

	const result: Environment[] = [...staticEnvironments]; // make a clone

	const config: WorkspaceConfiguration = workspace.getConfiguration(extensionPrefix);
	const ppe: Environment | undefined = config.get(ppeSetting);
	if (ppe) {
		result.push({
			...ppe,
			name: azurePPE,
			validateAuthority: getValidateAuthority(ppe.activeDirectoryEndpointUrl)
		});
	}

	const customCloudEnvironment: Environment | undefined = await getCustomCloudEnvironment(config, includePartial);
	if (customCloudEnvironment) {
		result.push(customCloudEnvironment);
	}

	return result;
}

export function isADFS(environment: Environment): boolean {
	const u = url.parse(environment.activeDirectoryEndpointUrl);
	const pathname = (u.pathname || '').toLowerCase();
	return pathname === '/adfs' || pathname.startsWith('/adfs/');
}

async function getCustomCloudEnvironment(config: WorkspaceConfiguration, includePartial: boolean): Promise<Environment | undefined> {
	const armUrl: string | undefined = config.get(customCloudArmUrlSetting);
	if (armUrl) {
		try {
			const endpointsUrl: string = getMetadataEndpoints(armUrl);
			const endpointsResponse: Response = await fetchWithLogging(endpointsUrl);
			if (endpointsResponse.ok) {
				// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
				const endpoints: IResourceManagerMetadata = await endpointsResponse.json();
				return <Environment>{
					name: azureCustomCloud,
					resourceManagerEndpointUrl: armUrl,
					activeDirectoryEndpointUrl: endpoints.authentication.loginEndpoint.endsWith('/') ? endpoints.authentication.loginEndpoint : endpoints.authentication.loginEndpoint.concat('/'),
					activeDirectoryGraphResourceId: endpoints.graphEndpoint,
					activeDirectoryResourceId: endpoints.authentication.audiences[0],
					portalUrl: endpoints.portalEndpoint,
					galleryEndpointUrl: endpoints.galleryEndpoint,
					storageEndpointSuffix: armUrl.substring(armUrl.indexOf('.')),
					keyVaultDnsSuffix: '.vault'.concat(armUrl.substring(armUrl.indexOf('.'))),
					managementEndpointUrl: endpoints.authentication.audiences[0],
					validateAuthority: getValidateAuthority(endpoints.authentication.loginEndpoint)
				};
			}
		} catch {
			const openSettings: string = localize('openSettings', 'Open Settings');
			void window.showErrorMessage(
				localize("azure-account.armUrlFetchFailed", "Fetching custom cloud environment data failed. Please check your custom cloud settings."),
				openSettings
			).then(result => {
				if(result === openSettings){
					void commands.executeCommand('workbench.action.openSettings', '@ext:ms-vscode.azure-account customCloud');
				}
			})
		}
	}

	return includePartial ? <Environment>{ name: azureCustomCloud } : undefined;
}

function getValidateAuthority(activeDirectoryEndpointUrl: string): boolean {
	// get validateAuthority from activeDirectoryUrl from user setting, it should be set to false only under ADFS environemnt.
	let validateAuthority: boolean = true;
	if (activeDirectoryEndpointUrl) {
		const activeDirectoryUrl: string = activeDirectoryEndpointUrl.endsWith('/') ? activeDirectoryEndpointUrl.slice(0, -1) : activeDirectoryEndpointUrl;
		validateAuthority = activeDirectoryUrl.endsWith('/adfs') ? false : true;
	}
	return validateAuthority;
}

function getMetadataEndpoints(resourceManagerUrl: string): string {
	resourceManagerUrl = resourceManagerUrl.endsWith('/') ? resourceManagerUrl.slice(0, -1) : resourceManagerUrl;
	const endpointSuffix: string = '/metadata/endpoints';
	const apiVersion: string = '2018-05-01';
	// return ppe metadata endpoints Url
	return `${resourceManagerUrl}${endpointSuffix}?api-version=${apiVersion}`
}
