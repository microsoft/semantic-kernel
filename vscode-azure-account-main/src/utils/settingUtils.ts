/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { workspace, WorkspaceConfiguration } from "vscode";
import { extensionPrefix } from "../constants";
import { getCurrentTarget } from "../login/getCurrentTarget";

export function getSettingWithPrefix(settingName: string): string {
	return `${extensionPrefix}.${settingName}`;
}

export function getSettingValue<T>(settingName: string): T | undefined {
	const config: WorkspaceConfiguration = workspace.getConfiguration(extensionPrefix);
	return config.get(settingName);
}

export async function updateSettingValue<T>(settingName: string, value: T): Promise<void> {
	const config: WorkspaceConfiguration = workspace.getConfiguration(extensionPrefix);
	await config.update(settingName, value, getCurrentTarget(config.inspect(settingName)));
}
