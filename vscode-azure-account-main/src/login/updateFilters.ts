/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { AzureResourceFilter, AzureSubscription } from "../azure-account.api";
import { resourceFilterSetting } from "../constants";
import { ext } from "../extensionVariables";
import { getSettingValue } from "../utils/settingUtils";
import { getNewFilters } from "./filters";

export function updateFilters(configChange = false): void {
	const resourceFilter: string[] | undefined = getSettingValue(resourceFilterSetting);
	if (configChange && JSON.stringify(resourceFilter) === ext.loginHelper.oldResourceFilter) {
		return;
	}
	ext.loginHelper.filtersTask = (async () => {
		await ext.loginHelper.api.waitForSubscriptions();
		const subscriptions: AzureSubscription[] = await ext.loginHelper.subscriptionsTask;
		ext.loginHelper.oldResourceFilter = JSON.stringify(resourceFilter);
		const newFilters: AzureResourceFilter[] = getNewFilters(subscriptions, resourceFilter);
		ext.loginHelper.api.filters.splice(0, ext.loginHelper.api.filters.length, ...newFilters);
		ext.loginHelper.onFiltersChanged.fire();
		return ext.loginHelper.api.filters;
	})();
}
