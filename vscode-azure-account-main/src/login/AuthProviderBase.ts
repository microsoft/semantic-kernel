/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { TokenCredential } from "@azure/core-auth";
import { Environment } from "@azure/ms-rest-azure-env";
import { AccountInfo } from "@azure/msal-node";
import { IActionContext, parseError } from "@microsoft/vscode-azext-utils";
import { randomBytes } from "crypto";
import { ServerResponse } from "http";
import { DeviceTokenCredentials } from "ms-rest-azure";
import { CancellationToken, env, MessageItem, UIKind, Uri, window } from "vscode";
import { AzureAccountExtensionApi, AzureSession } from "../azure-account.api";
import { portADFS, redirectUrlAAD } from "../constants";
import { ext } from "../extensionVariables";
import { logAttemptingToReachUrlMessage } from "../logAttemptingToReachUrlMessage";
import { localize } from "../utils/localize";
import { logErrorMessage } from "../utils/logErrorMessage";
import { openUri } from "../utils/openUri";
import { DeviceTokenCredentials2 } from "./adal/DeviceTokenCredentials2";
import { AzureSessionInternal } from "./AzureSessionInternal";
import { getEnvironments } from "./environments";
import { exchangeCodeForToken } from "./exchangeCodeForToken";
import { getLocalCallbackUrl } from "./getCallbackUrl";
import { getKey } from "./getKey";
import { CodeResult, createServer, createTerminateServer, RedirectResult, startServer } from './server';
import { SubscriptionTenantCache } from "./subscriptionTypes";

export type AbstractCredentials = DeviceTokenCredentials;
export type AbstractCredentials2 = DeviceTokenCredentials2 | TokenCredential;

const redirectUrlADFS: string = getLocalCallbackUrl(portADFS);

export abstract class AuthProviderBase<TLoginResult> {
	private terminateServer: (() => Promise<void>) | undefined;

	public abstract loginWithAuthCode(code: string, redirectUrl: string, clientId: string, environment: Environment, tenantId: string): Promise<TLoginResult>;
	public abstract loginWithDeviceCode(context: IActionContext, environment: Environment, tenantId: string, cancellationToken: CancellationToken): Promise<TLoginResult>;
	public abstract loginSilent(environment: Environment, tenantId: string): Promise<TLoginResult>;
	public abstract getCredentials(environment: string, userId: string, tenantId: string): AbstractCredentials;
	public abstract getCredentials2(environment: Environment, userId: string, tenantId: string, accountInfo?: AccountInfo): AbstractCredentials2;
	public abstract updateSessions(environment: Environment, loginResult: TLoginResult, sessions: AzureSession[]): Promise<void>;
	public abstract clearTokenCache(): Promise<void>;

	public async login(context: IActionContext, clientId: string, environment: Environment, isAdfs: boolean, tenantId: string, openUri: (url: string) => Promise<void>, redirectTimeout: () => Promise<void>, cancellationToken: CancellationToken): Promise<TLoginResult> {
		if (env.uiKind === UIKind.Web) {
			return await this.loginWithoutLocalServer(clientId, environment, isAdfs, tenantId);
		}

		if (isAdfs && this.terminateServer) {
			await this.terminateServer();
		}

		const nonce: string = randomBytes(16).toString('base64');
		const { server, redirectPromise, codePromise, codeTimer } = createServer(context, nonce);

		cancellationToken.onCancellationRequested(() => {
			server.close(error => error && ext.outputChannel.appendLog(parseError(error).message));
			clearTimeout(codeTimer);
			context.telemetry.properties.serverClosed = 'true';
			ext.outputChannel.appendLog(localize('azure-account.authProcessCancelled', 'Authentication process cancelled.'));
		});

		if (isAdfs) {
			this.terminateServer = createTerminateServer(server);
		}

		try {
			const port: number = await startServer(server, isAdfs);
			await openUri(`http://localhost:${port}/signin?nonce=${encodeURIComponent(nonce)}`);
			// eslint-disable-next-line @typescript-eslint/no-misused-promises
			const redirectTimer = setTimeout(() => redirectTimeout().catch(logErrorMessage), 10*1000);
			const redirectResult: RedirectResult = await redirectPromise;

			if ('err' in redirectResult) {
				// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
				const { err, res } = redirectResult;
				// eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
				res.writeHead(302, { Location: `/?error=${encodeURIComponent(err && err.message || 'Unknown error')}` });
				res.end();
				throw err;
			}

			clearTimeout(redirectTimer);

			const host: string = redirectResult.req.headers.host || '';
			const updatedPortStr: string = (/^[^:]+:(\d+)$/.exec(Array.isArray(host) ? host[0] : host) || [])[1];
			const updatedPort: number = updatedPortStr ? parseInt(updatedPortStr, 10) : port;
			const state: string = `${encodeURIComponent(getLocalCallbackUrl(updatedPort))}?nonce=${encodeURIComponent(nonce)}`;
			const redirectUrl: string = isAdfs ? redirectUrlADFS : redirectUrlAAD;
			const signInUrl: string = `${environment.activeDirectoryEndpointUrl}${isAdfs ? '' : `${tenantId}/`}oauth2/authorize?response_type=code&client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUrl)}&state=${state}&prompt=select_account`;

			logAttemptingToReachUrlMessage(redirectUrl);
			logAttemptingToReachUrlMessage(signInUrl);

			redirectResult.res.writeHead(302, { Location: signInUrl })
			redirectResult.res.end();

			const codeResult: CodeResult = await codePromise;
			const serverResponse: ServerResponse = codeResult.res;
			try {
				if ('err' in codeResult) {
					throw codeResult.err;
				}

				try {
					return await this.loginWithAuthCode(codeResult.code, redirectUrl, clientId, environment, tenantId);
				} finally {
					serverResponse.writeHead(302, { Location: '/' });
					serverResponse.end();
				}
			} catch (err) {
				serverResponse.writeHead(302, { Location: `/?error=${encodeURIComponent(parseError(err).message || 'Unknown error')}` });
				serverResponse.end();
				throw err;
			}
		} finally {
			setTimeout(() => {
				server.close(error => error && ext.outputChannel.appendLog(parseError(error).message));
			}, 5000);
		}
	}

	public async loginWithoutLocalServer(clientId: string, environment: Environment, isAdfs: boolean, tenantId: string): Promise<TLoginResult> {
		let callbackUri: Uri = await env.asExternalUri(Uri.parse(`${env.uriScheme}://ms-vscode.azure-account`));
		const nonce: string = randomBytes(16).toString('base64');
		const callbackQuery = new URLSearchParams(callbackUri.query);
		callbackQuery.set('nonce', nonce);
		callbackUri = callbackUri.with({
			query: callbackQuery.toString()
		});
		const state = encodeURIComponent(callbackUri.toString(true));
		const signInUrl: string = `${environment.activeDirectoryEndpointUrl}${isAdfs ? '' : `${tenantId}/`}oauth2/authorize`;
		logAttemptingToReachUrlMessage(signInUrl);
		let uri: Uri = Uri.parse(signInUrl);
		uri = uri.with({
			query: `response_type=code&client_id=${encodeURIComponent(clientId)}&redirect_uri=${redirectUrlAAD}&state=${state}&prompt=select_account`
		});
		void env.openExternal(uri);

		const timeoutPromise = new Promise((_resolve: (value: TLoginResult) => void, reject) => {
			const wait = setTimeout(() => {
				clearTimeout(wait);
				reject('Login timed out.');
			}, 1000 * 60 * 5)
		});

		return await Promise.race([exchangeCodeForToken<TLoginResult>(this, clientId, environment, tenantId, redirectUrlAAD, nonce), timeoutPromise]);
	}

	public async initializeSessions(cache: SubscriptionTenantCache, api: AzureAccountExtensionApi): Promise<Record<string, AzureSession>> {
		const sessions: Record<string, AzureSessionInternal> = {};
		const environments: Environment[] = await getEnvironments();

		for (const { session } of cache.subscriptions) {
			const { environment, userId, tenantId, accountInfo } = session;
			const key: string = getKey(environment, userId, tenantId);
			const env: Environment | undefined = environments.find(e => e.name === environment);

			if (!sessions[key] && env) {
				sessions[key] = new AzureSessionInternal(
					env,
					userId,
					tenantId,
					accountInfo,
					this
				);
				api.sessions.push(sessions[key]);
			}
		}

		return sessions;
	}

	protected async showDeviceCodeMessage(message: string, userCode: string, verificationUrl: string): Promise<void> {
		const copyAndOpen: MessageItem = { title: localize('azure-account.copyAndOpen', "Copy & Open") };
		const response: MessageItem | undefined = await window.showInformationMessage(message, copyAndOpen);
		if (response === copyAndOpen) {
			void env.clipboard.writeText(userCode);
			await openUri(verificationUrl);
		}
	}
}
