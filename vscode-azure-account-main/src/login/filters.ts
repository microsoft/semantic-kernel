/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { AzureResourceFilter, AzureSubscription } from "../azure-account.api";
import { ISubscriptionItem } from "./subscriptionTypes";

export function addFilter(resourceFilter: string[], item: ISubscriptionItem): void {
	const { session, subscription } = item.subscription;
	resourceFilter.push(`${session.tenantId}/${subscription.subscriptionId}`);
	item.picked = true;
}

export function removeFilter(resourceFilter: string[], item: ISubscriptionItem): void {
	const { session, subscription } = item.subscription;
	const indexToRemove: number = resourceFilter.indexOf(`${session.tenantId}/${subscription.subscriptionId}`);
	resourceFilter.splice(indexToRemove, 1);
	item.picked = false;
}

export function getNewFilters(subscriptions: AzureSubscription[], resourceFilter: string[] | undefined): AzureResourceFilter[] {
	if (resourceFilter && !Array.isArray(resourceFilter)) {
		resourceFilter = [];
	}
	const filters = resourceFilter && resourceFilter.reduce((f, s) => {
		if (typeof s === 'string') {
			f[s] = true;
		}
		return f;
	}, <Record<string, boolean>>{});

	return filters ? subscriptions.filter(s => filters[`${s.session.tenantId}/${s.subscription.subscriptionId}`]) : subscriptions;
}
