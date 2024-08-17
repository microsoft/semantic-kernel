/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { env, Uri } from "vscode";

export async function openUri(uri: string): Promise<void> {
	await env.openExternal(Uri.parse(uri));
}
