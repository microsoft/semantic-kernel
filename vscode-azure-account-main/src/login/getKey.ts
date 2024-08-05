/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

export function getKey(environment: string, userId: string, tenantId: string): string {
	return `${environment} ${userId} ${tenantId}`;
}
