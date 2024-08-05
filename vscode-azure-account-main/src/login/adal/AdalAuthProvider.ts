/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from "@azure/ms-rest-azure-env";
import { IActionContext } from "@microsoft/vscode-azext-utils";
import { Logging, LoggingLevel, MemoryCache, TokenResponse, UserCodeInfo } from "adal-node";
import { DeviceTokenCredentials } from "ms-rest-azure";
import { CancellationToken } from "vscode";
import { AzureSession } from "../../azure-account.api";
import { authTimeoutMs, azureCustomCloud, azurePPE, clientId, staticEnvironments, stoppedAuthTaskMessage } from "../../constants";
import { AzureLoginError } from "../../errors";
import { ext } from "../../extensionVariables";
import { localize } from "../../utils/localize";
import { Deferred } from "../../utils/promiseUtils";
import { AbstractCredentials, AuthProviderBase } from "../AuthProviderBase";
import { DeviceTokenCredentials2 } from "./DeviceTokenCredentials2";
import { getUserCode } from "./getUserCode";
import { ProxyTokenCache, addTokenToCache, clearTokenCache, deleteRefreshToken, getStoredCredentials, getTokenResponse, getTokenWithAuthorizationCode, getTokensFromToken, storeRefreshToken, tokenFromRefreshToken } from "./tokens";

const staticEnvironmentNames: string[] = [
	...staticEnvironments.map(environment => environment.name),
	azureCustomCloud,
	azurePPE
];

const ADALLogLevel: Record<string, LoggingLevel> = {
	Error: 0,
	Warning: 1,
	Info: 2,
	Verbose: 3,
} as const;

export class AdalAuthProvider extends AuthProviderBase<TokenResponse[]> {
	private tokenCache: MemoryCache = new MemoryCache();
	private delayedTokenCache: ProxyTokenCache = new ProxyTokenCache(this.tokenCache);
	
	constructor() {
		super();
		Logging.setLoggingOptions({
			level: ADALLogLevel.Verbose,
			log: (level: LoggingLevel, message: string, error?: Error) => {
				// example message:
				// Wed, 22 Mar 2023 20:03:04 GMT:c118cca5-90ce-4fcb-b3ed-e73d32fc1eee - TokenRequest: INFO: Getting a new token from a refresh token.
				message = message.replace(/.*-\s/, ''); // remove ADAL log timestamp and id
				message = 'ADAL: ' + message;
				switch (level) {
					case ADALLogLevel.Error:
						ext.outputChannel.error(error ?? message);
						break;
					case ADALLogLevel.Warning:
						ext.outputChannel.warn(message);
						break;
					case ADALLogLevel.Info:
						ext.outputChannel.debug(message);
						break;
					case ADALLogLevel.Verbose:
						ext.outputChannel.trace(message);
				}
			}
		});
	}

	public async loginWithAuthCode(code: string, redirectUrl: string, clientId: string, environment: Environment, tenantId: string): Promise<TokenResponse[]> {
		const tokenResponse: TokenResponse = await getTokenWithAuthorizationCode(clientId, environment, redirectUrl, tenantId, code);

		// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
		await storeRefreshToken(environment, tokenResponse.refreshToken!);
		return getTokensFromToken(environment, tenantId, tokenResponse);
	}

	public async loginWithDeviceCode(context: IActionContext, environment: Environment, tenantId: string, cancellationToken: CancellationToken): Promise<TokenResponse[]> {
		// Used for prematurely ending the `tokenResponseTask`.
		let deferredTaskRegulator: Deferred<TokenResponse>;
		const taskRegulator = new Promise<TokenResponse>((resolve, reject) => deferredTaskRegulator = { resolve, reject });

		const timeout = setTimeout(() => {
			context.errorHandling.suppressDisplay = true;
			deferredTaskRegulator.reject(new Error(localize('azure-account.timeoutWaitingForDeviceCode', 'Timeout waiting for device code.')));
		}, authTimeoutMs);

		cancellationToken.onCancellationRequested(() => {
			clearTimeout(timeout);
			deferredTaskRegulator.reject(new Error(stoppedAuthTaskMessage));
		});

		const userCode: UserCodeInfo = await getUserCode(environment, tenantId);
		const messageTask: Promise<void> = this.showDeviceCodeMessage(userCode.message, userCode.userCode, userCode.verificationUrl);
		const tokenResponseTask: Promise<TokenResponse> = getTokenResponse(environment, tenantId, userCode);
		const tokenResponse: TokenResponse = await Promise.race([tokenResponseTask, messageTask.then(() => Promise.race([tokenResponseTask, taskRegulator]))]);

		clearTimeout(timeout);

		// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
		await storeRefreshToken(environment, tokenResponse.refreshToken!);
		return getTokensFromToken(environment, tenantId, tokenResponse);
	}

	public async loginSilent(environment: Environment, tenantId: string): Promise<TokenResponse[]> {
		const storedCreds: string | undefined = await getStoredCredentials(environment);
		if (!storedCreds) {
			throw new AzureLoginError(localize('azure-account.refreshTokenMissing', 'Not signed in'));
		}

		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		let parsedCreds: any;
		let tokenResponse: TokenResponse | null = null;

		try {
			// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
			parsedCreds = JSON.parse(storedCreds);
		} catch {
			tokenResponse = await tokenFromRefreshToken(environment, storedCreds, tenantId)
		}

		if (parsedCreds) {
			// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
			const { redirectionUrl, code } = parsedCreds;
			if (!redirectionUrl || !code) {
				throw new AzureLoginError(localize('azure-account.malformedCredentials', "Stored credentials are invalid"));
			}

			tokenResponse = await getTokenWithAuthorizationCode(clientId, Environment.AzureCloud, redirectionUrl, tenantId, code);
		}

		if (!tokenResponse) {
			throw new AzureLoginError(localize('azure-account.missingTokenResponse', "Using stored credentials failed"));
		}

		return getTokensFromToken(environment, tenantId, tokenResponse);
	}

	public getCredentials(environment: string, userId: string, tenantId: string): AbstractCredentials {
		// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-explicit-any
		return new DeviceTokenCredentials({ environment: (<any>Environment)[environment], username: userId, clientId, tokenCache: this.delayedTokenCache, domain: tenantId });
	}

	public getCredentials2(environment: Environment, userId: string, tenantId: string): DeviceTokenCredentials2 {
		return new DeviceTokenCredentials2(clientId, tenantId, userId, undefined, environment, this.delayedTokenCache);
	}

	public async updateSessions(environment: Environment, loginResult: TokenResponse[], sessions: AzureSession[]): Promise<void> {
		await clearTokenCache(this.tokenCache);

		for (const tokenResponse of loginResult) {
			await addTokenToCache(environment, this.tokenCache, tokenResponse);
		}

		/* eslint-disable @typescript-eslint/no-non-null-assertion */
		this.delayedTokenCache.initEnd!();

		sessions.splice(0, sessions.length, ...loginResult.map<AzureSession>(tokenResponse => ({
			environment,
			userId: tokenResponse.userId!,
			tenantId: tokenResponse.tenantId!,
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			credentials: this.getCredentials(<any>environment, tokenResponse.userId!, tokenResponse.tenantId!),
			credentials2: this.getCredentials2(environment, tokenResponse.userId!, tokenResponse.tenantId!)
		})));
		/* eslint-enable @typescript-eslint/no-non-null-assertion */
	}

	public async clearTokenCache(): Promise<void> {
		// 'Azure' and 'AzureChina' are the old names for the 'AzureCloud' and 'AzureChinaCloud' environments
		const allEnvironmentNames: string[] = staticEnvironmentNames.concat(['Azure', 'AzureChina'])
		for (const name of allEnvironmentNames) {
			await deleteRefreshToken(name);
		}

		await clearTokenCache(this.tokenCache);
		// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
		this.delayedTokenCache.initEnd!();
	}
}
