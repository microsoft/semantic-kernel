/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IAzExtLogOutputChannel, IExperimentationServiceAdapter } from "@microsoft/vscode-azext-utils";
import { ExtensionContext } from "vscode";
import { AzureAccountLoginHelper } from "./login/AzureAccountLoginHelper";
import { UriEventHandler } from "./login/exchangeCodeForToken";

export namespace ext {
    export let context: ExtensionContext;
    export let loginHelper: AzureAccountLoginHelper;
    export let outputChannel: IAzExtLogOutputChannel;
    export let uriEventHandler: UriEventHandler;
    export let experimentationService: IExperimentationServiceAdapter;
}
