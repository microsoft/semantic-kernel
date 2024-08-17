/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IActionContext } from "@microsoft/vscode-azext-utils";
import { commands, ExtensionContext, window } from "vscode";
import { localize } from "../utils/localize";
import { getSettingValue } from "../utils/settingUtils";
import { AzureAccountLoginHelper } from "./AzureAccountLoginHelper";
import { cachedSettingKeys, SettingsCache, settingsCacheKey, SettingsCacheVerified } from "./SettingsCache";

export async function checkSettingsOnStartup(extensionContext: ExtensionContext, actionContext: IActionContext, loginHelper: AzureAccountLoginHelper): Promise<void> {
    const numSettings = cachedSettingKeys.length;

    const lastSeenSettingsCache: SettingsCache | undefined = extensionContext.globalState.get(settingsCacheKey);
    const valuesToCopy = lastSeenSettingsCache?.values?.length === numSettings ? lastSeenSettingsCache.values : [];
    const lastSeenSettingsCacheVerified: SettingsCacheVerified = { values: new Array<undefined>(numSettings) };
    lastSeenSettingsCacheVerified.values.splice(0, numSettings, ...valuesToCopy)

    const lastSeenSettingsCacheNew: SettingsCacheVerified = { values: new Array<string | undefined>(numSettings) };

    // Ask to sign out & reload if the cache is being reset.
    let shouldSignOutAndReload: boolean = false;

    for (let index = 0; index < numSettings; index++) {
        const settingKey: string = cachedSettingKeys[index];

        const settingValueOnStartup: string | undefined = getSettingValue(settingKey);
        addPropertyToTelemetry(actionContext, settingKey, 'OnStartup', settingValueOnStartup);

        const lastSeenSettingValue: string | undefined = lastSeenSettingsCacheVerified.values[index];
        addPropertyToTelemetry(actionContext, settingKey, 'LastSeen', lastSeenSettingValue)

        if (lastSeenSettingValue && settingValueOnStartup !== lastSeenSettingValue) {
            shouldSignOutAndReload = true;
        }

        lastSeenSettingsCacheNew.values[index] = settingValueOnStartup;
    }

    await extensionContext.globalState.update(settingsCacheKey, lastSeenSettingsCacheNew);

    if (shouldSignOutAndReload) {
        await askThenSignOutAndReload(actionContext, loginHelper);
    }
}

export async function askThenSignOutAndReload(actionContext: IActionContext, loginHelper: AzureAccountLoginHelper, forceLogout?: boolean): Promise<void> {
    actionContext.telemetry.properties.askThenSignOutAndReload = 'true';

    const signOutAndReloadRequired: string = localize('azure-account.signOutAndReloadRequired', 'Signing out and reloading the window is required for the modified setting(s) to take effect.');
    const signOutAndReload: string = localize('azure-account.signOutAndReload', 'Sign Out and Reload Window');

    // Purposefully await this message to block whatever command caused the extension to activate.
    await window.showInformationMessage(signOutAndReloadRequired, signOutAndReload).then(async value => {
        if (value === signOutAndReload) {
            actionContext.telemetry.properties.signOutAndReload = 'true';
            await loginHelper.logout(forceLogout);
            await commands.executeCommand('workbench.action.reloadWindow');
        }
    });
}

export async function askForSignIn(actionContext: IActionContext): Promise<void> {
    actionContext.telemetry.properties.askForSignIn = 'true';

    const signInAgainRequired: string = localize('azure-account.signInAgainRequired', 'Signing in again is required for the modified setting(s) to take effect.');
    const signIn: string = localize('azure-account.signIn', 'Sign In');

    // Purposefully await this message to block whatever command caused the extension to activate.
    await window.showInformationMessage(signInAgainRequired, signIn).then(async value => {
        if (value === signIn) {
            actionContext.telemetry.properties.signInAgain = 'true';
            await commands.executeCommand('azure-account.login');
        }
    });
}

function addPropertyToTelemetry(actionContext: IActionContext, eventPrefix: string, eventSuffix: string, value: string | undefined): void {
    actionContext.telemetry.properties[eventPrefix + eventSuffix] = String(value);
}
