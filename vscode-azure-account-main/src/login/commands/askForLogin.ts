/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { commands, MessageItem, window } from "vscode";
import { ext } from "../../extensionVariables";
import { localize } from "../../utils/localize";

export async function askForLogin(): Promise<unknown> {
	if (ext.loginHelper.api.status === 'LoggedIn') {
		return;
	}
	const login: MessageItem = { title: localize('azure-account.login', "Sign In") };
	const result: MessageItem | undefined = await window.showInformationMessage(localize('azure-account.loginFirst', "You are not signed in. Sign in to continue."), login);
	return result === login && commands.executeCommand('azure-account.login');
}
