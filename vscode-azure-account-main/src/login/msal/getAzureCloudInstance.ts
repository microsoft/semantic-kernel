/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from "@azure/ms-rest-azure-env";
import { AzureCloudInstance } from "@azure/msal-node";
import { callWithTelemetryAndErrorHandlingSync, IActionContext } from "@microsoft/vscode-azext-utils";
import { localize } from "../../utils/localize";

export function getAzureCloudInstance(environment: Environment): AzureCloudInstance {
    const azureCloudInstance: AzureCloudInstance | undefined = callWithTelemetryAndErrorHandlingSync('getAzureCloudInstance', (context: IActionContext) => {
        let azureCloudInstance: AzureCloudInstance;

        switch (environment.name) {
            case 'AzureCloud':
                azureCloudInstance = AzureCloudInstance.AzurePublic;
                break;
            case 'AzureChinaCloud':
                azureCloudInstance = AzureCloudInstance.AzureChina;
                break;
            case 'AzureUSGovernment':
                azureCloudInstance = AzureCloudInstance.AzureUsGovernment;
                break;
            case 'AzureGermanCloud':
                azureCloudInstance = AzureCloudInstance.AzureGermany;
                break;
            default:
                azureCloudInstance = AzureCloudInstance.None;
        }

        context.telemetry.properties.azureCloudInstance = String(azureCloudInstance);
        return azureCloudInstance;
    });

    if (!azureCloudInstance) {
        throw new Error(localize('azure-account.failedToGetAzureCloudInstance', `Failed to get Azure Cloud Instance for cloud "{0}".`, environment.name));
    }

    return azureCloudInstance;
}
