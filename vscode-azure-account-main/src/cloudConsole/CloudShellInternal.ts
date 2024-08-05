/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Terminal, TerminalProfile } from "vscode";
import { CloudShell, CloudShellStatus } from "../azure-account.api";

export interface CloudShellInternal extends Omit<CloudShell, 'terminal'> {
	status: CloudShellStatus;
	terminal?: Promise<Terminal>;
	terminalProfile?: Promise<TerminalProfile>;
}
