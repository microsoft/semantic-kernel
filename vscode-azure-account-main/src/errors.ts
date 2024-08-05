/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

export class AzureLoginError extends Error {
	// eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/explicit-module-boundary-types
	constructor(message: string, public reason?: any) {
		super(message);
	}
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/explicit-module-boundary-types
export function getErrorMessage(err: any): string | undefined {
	if (!err) {
		return;
	}

	/* eslint-disable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
	if (err.message && typeof err.message === 'string') {
		return err.message;
	}

	if (err.stack && typeof err.stack === 'string') {
		// eslint-disable-next-line  @typescript-eslint/no-unsafe-call
		return err.stack.split('\n')[0];
	}

	const str = String(err);
	if (!str || str === '[object Object]') {
		// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
		const ctr = err.constructor;
		if (ctr && ctr.name && typeof ctr.name === 'string') {
			return ctr.name;
		}
	}
	/* eslint-enable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */

	return str;
}
