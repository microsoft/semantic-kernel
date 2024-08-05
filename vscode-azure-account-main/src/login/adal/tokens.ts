/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { SubscriptionClient, SubscriptionModels } from "@azure/arm-subscriptions";
import { Environment } from "@azure/ms-rest-azure-env";
import { RequestPolicyFactory } from "@azure/ms-rest-js";
import { DeviceTokenCredentials as DeviceTokenCredentials2 } from '@azure/ms-rest-nodeauth';
import { AuthenticationContext, MemoryCache, TokenResponse, UserCodeInfo } from "adal-node";
import { clientId, commonTenantId } from "../../constants";
import { AzureLoginError } from "../../errors";
import { ext } from "../../extensionVariables";
import { listAll } from "../../utils/arrayUtils";
import { localize } from "../../utils/localize";
import { logErrorMessage } from "../../utils/logErrorMessage";
import { LogRequestPolicy } from "../../utils/logging/msRest/LogRequestPolicy";
import { isADFS } from "../environments";

// eslint-disable-next-line @typescript-eslint/no-var-requires, @typescript-eslint/no-unsafe-assignment, import/no-internal-modules
const CacheDriver = require('adal-node/lib/cache-driver');
// eslint-disable-next-line @typescript-eslint/no-var-requires, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, import/no-internal-modules
const createLogContext = require('adal-node/lib/log').createLogContext;

export class ProxyTokenCache {
	/* eslint-disable */
	public initEnd?: () => void;
	private initTask: Promise<void> = new Promise<void>(resolve => {
		this.initEnd = resolve;
	});

	constructor(private target: any) {
	}

	remove(entries: any, callback: any) {
		this.target.remove(entries, callback)
	}

	add(entries: any, callback: any) {
		this.target.add(entries, callback)
	}

	find(query: any, callback: any) {
		void this.initTask.then(() => {
			this.target.find(query, callback);
		});
	}
	/* eslint-enable */
}

export async function getStoredCredentials(environment: Environment): Promise<string | undefined> {
	try {
		const token = await ext.context.secrets.get('Refresh Token');
		if (token) {
			if (!await ext.context.secrets.get('Azure')) {
				await ext.context.secrets.store('Azure', token);
			}
			await ext.context.secrets.delete('Refresh Token');
		}
	} catch {
		// ignore
	}
	try {
		return await ext.context.secrets.get(environment.name);
	} catch {
		// ignore
	}
}

export async function storeRefreshToken(environment: Environment, token: string): Promise<void> {
	try {
		await ext.context.secrets.store(environment.name, token);
	} catch {
		// ignore
	}
}

export async function deleteRefreshToken(environmentName: string): Promise<void> {
	try {
		await ext.context.secrets.delete(environmentName);
	} catch {
		// ignore
	}
}

export async function tokenFromRefreshToken(environment: Environment, refreshToken: string, tenantId: string, resource?: string): Promise<TokenResponse> {
	return new Promise<TokenResponse>((resolve, reject) => {
		const tokenCache: MemoryCache = new MemoryCache();
		const context: AuthenticationContext = new AuthenticationContext(`${environment.activeDirectoryEndpointUrl}${tenantId}`, environment.validateAuthority, tokenCache);
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		context.acquireTokenWithRefreshToken(refreshToken, clientId, <any>resource, (err, tokenResponse) => {
			if (err) {
				reject(new AzureLoginError(localize('azure-account.tokenFromRefreshTokenFailed', "Acquiring token with refresh token failed"), err));
			} else if (tokenResponse.error) {
				reject(new AzureLoginError(localize('azure-account.tokenFromRefreshTokenFailed', "Acquiring token with refresh token failed"), tokenResponse));
			} else {
				resolve(<TokenResponse>tokenResponse);
			}
		});
	});
}

export async function tokensFromToken(environment: Environment, firstTokenResponse: TokenResponse): Promise<TokenResponse[]> {
	const tokenCache: MemoryCache = new MemoryCache();
	await addTokenToCache(environment, tokenCache, firstTokenResponse);
	const credentials: DeviceTokenCredentials2 = new DeviceTokenCredentials2(clientId, undefined, firstTokenResponse.userId, undefined, environment, tokenCache);
	const client: SubscriptionClient = new SubscriptionClient(credentials, { baseUri: environment.resourceManagerEndpointUrl, requestPolicyFactories: (defaultFactories: RequestPolicyFactory[]) => {
		return defaultFactories.concat({
			create: (nextPolicy, options) => {
				return new LogRequestPolicy(ext.outputChannel, 'SubscriptionsClient', nextPolicy, options);
			}
		});
	}});
	const tenants: SubscriptionModels.TenantIdDescription[] = await listAll(client.tenants, client.tenants.list());
	const responses: TokenResponse[] = <TokenResponse[]>(await Promise.all<TokenResponse | null>(tenants.map((tenant) => {
		if (tenant.tenantId === firstTokenResponse.tenantId) {
			return firstTokenResponse;
		}
		// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
		return tokenFromRefreshToken(environment, firstTokenResponse.refreshToken!, tenant.tenantId!)
			.catch(err => {
				logErrorMessage(err);
				err instanceof AzureLoginError && err.reason && ext.outputChannel.appendLog(err.reason);
				return null;
			});
	}))).filter(r => r);
	if (!responses.some(response => response.tenantId === firstTokenResponse.tenantId)) {
		responses.unshift(firstTokenResponse);
	}
	return responses;
}

/* eslint-disable */
export async function addTokenToCache(environment: Environment, tokenCache: any, tokenResponse: TokenResponse): Promise<void> {
	return new Promise<void>((resolve, reject) => {
		const driver = new CacheDriver(
			{ _logContext: createLogContext('') },
			`${environment.activeDirectoryEndpointUrl}${tokenResponse.tenantId}`,
			environment.activeDirectoryResourceId,
			clientId,
			tokenCache,
			(entry: any, _resource: any, callback: (err: any, response: any) => {}) => {
				callback(null, entry);
			}
		);
		driver.add(tokenResponse, function (err: any) {
			if (err) {
				reject(err);
			} else {
				resolve();
			}
		});
	});
}

export async function clearTokenCache(tokenCache: any): Promise<void> {
	await new Promise<void>((resolve, reject) => {
		tokenCache.find({}, (err: any, entries: any[]) => {
			if (err) {
				reject(err);
			} else {
				tokenCache.remove(entries, (err: any) => {
					if (err) {
						reject(err);
					} else {
						resolve();
					}
				});
			}
		});
	});
}
/* eslint-enable */

export async function getTokenWithAuthorizationCode(clientId: string, environment: Environment, redirectUrl: string, tenantId: string, code: string): Promise<TokenResponse> {
	return new Promise<TokenResponse>((resolve, reject) => {
		const context: AuthenticationContext = new AuthenticationContext(`${environment.activeDirectoryEndpointUrl}${tenantId}`, !isADFS(environment));
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		context.acquireTokenWithAuthorizationCode(code, redirectUrl, environment.activeDirectoryResourceId, clientId, <any>undefined, (err, response) => {
			if (err) {
				reject(err);
			} if (response && response.error) {
				reject(new Error(`${response.error}: ${response.errorDescription}`));
			} else {
				resolve(<TokenResponse>response);
			}
		});
	});
}

export async function getTokensFromToken(environment: Environment, tenantId: string, tokenResponse: TokenResponse): Promise<TokenResponse[]> {
	return tenantId === commonTenantId ? await tokensFromToken(environment, tokenResponse) : [tokenResponse];
}

export async function getTokenResponse(environment: Environment, tenantId: string, userCode: UserCodeInfo): Promise<TokenResponse> {
	return new Promise<TokenResponse>((resolve, reject) => {
		const tokenCache: MemoryCache = new MemoryCache();
		const context: AuthenticationContext = new AuthenticationContext(`${environment.activeDirectoryEndpointUrl}${tenantId}`, environment.validateAuthority, tokenCache);
		context.acquireTokenWithDeviceCode(`${environment.managementEndpointUrl}`, clientId, userCode, (err, tokenResponse) => {
			if (err) {
				reject(new AzureLoginError(localize('azure-account.tokenFailed', "Acquiring token with device code failed"), err));
			} else if (tokenResponse.error) {
				reject(new AzureLoginError(localize('azure-account.tokenFailed', "Acquiring token with device code failed"), tokenResponse));
			} else {
				resolve(<TokenResponse>tokenResponse);
			}
		});
	});
}
