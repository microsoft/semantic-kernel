/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { ext } from "./extensionVariables";
import { localize } from "./utils/localize";

export function logAttemptingToReachUrlMessage(url: string): void {
    ext.outputChannel.appendLog(localize('azure-account.attemptingToReachUrl', 'Attempting to reach URL "{0}"...', url));
}
