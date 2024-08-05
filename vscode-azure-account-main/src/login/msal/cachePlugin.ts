/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { ICachePlugin, TokenCacheContext } from '@azure/msal-node';
import { ext } from '../../extensionVariables';
import { getSelectedEnvironment } from '../environments';

const beforeCacheAccess = async (cacheContext: TokenCacheContext): Promise<void> => {
	const cachedValue: string | undefined = await ext.context.secrets.get((await getSelectedEnvironment()).name);
	cachedValue && cacheContext.tokenCache.deserialize(cachedValue);
};

const afterCacheAccess = async (cacheContext: TokenCacheContext): Promise<void> => {
    if(cacheContext.cacheHasChanged) {
		await ext.context.secrets.store((await getSelectedEnvironment()).name, cacheContext.tokenCache.serialize());
    }
};

export const cachePlugin: ICachePlugin = {
	beforeCacheAccess,
	afterCacheAccess
};
