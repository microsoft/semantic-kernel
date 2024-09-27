/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from "@azure/ms-rest-azure-env";
import { Disposable, EventEmitter, Uri, UriHandler } from "vscode";
import { ext } from "../extensionVariables";
import { localize } from "../utils/localize";
import { AuthProviderBase } from "./AuthProviderBase";

export class UriEventHandler extends EventEmitter<Uri> implements UriHandler {
	public handleUri(uri: Uri): void {
		this.fire(uri);
	}
}

export async function exchangeCodeForToken<TLoginResult>(authProvider: AuthProviderBase<TLoginResult>, clientId: string, environment: Environment, tenantId: string, callbackUri: string, nonce: string): Promise<TLoginResult> {
	let uriEventListener: Disposable;
	return new Promise((resolve: (value: TLoginResult) => void , reject) => {
		uriEventListener = ext.uriEventHandler.event(async (uri: Uri) => {
			try {
				/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */
				const query = parseQuery(uri);
				const code = query.code;

				// Workaround double encoding issues
				if (query.nonce !== nonce && decodeURIComponent(query.nonce) !== nonce) {
					throw new Error(localize('azure-account.nonceDoesNotMatch', 'Nonce does not match.'));
				}
				/* eslint-enable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */

				resolve(await authProvider.loginWithAuthCode(code, callbackUri, clientId, environment, tenantId));
			} catch (err) {
				reject(err);
			}
		});
	}).then(result => {
		uriEventListener.dispose()
		return result;
	}).catch(err => {
		uriEventListener.dispose();
		throw err;
	});
}

/* eslint-disable @typescript-eslint/no-unsafe-return, @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access */
function parseQuery(uri: Uri): any {
	return uri.query.split('&').reduce((prev: any, current) => {
		const queryString: string[] = current.split('=');
		prev[queryString[0]] = queryString[1];
		return prev;
	}, {});
}
/* eslint-enable @typescript-eslint/no-unsafe-return, @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access */
