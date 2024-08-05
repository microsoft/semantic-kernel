/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { authLibrarySetting, cloudSetting, tenantSetting } from "../constants";

// Keys corresponding to `values` in `SettingsCache` and `SettingsCacheVerified`
export const cachedSettingKeys: string[] = [authLibrarySetting, cloudSetting, tenantSetting];

// The cache key under which a `SettingsCache` is stored
export const settingsCacheKey: string = 'lastSeenSettingsCache';

export interface SettingsCache {
    values: (string | undefined)[] | undefined;
}

export interface SettingsCacheVerified extends SettingsCache {
    values: (string | undefined)[];
}
