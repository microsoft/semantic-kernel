/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from '@azure/ms-rest-azure-env';
import { AccountInfo } from '@azure/msal-common';
import { AzureSession } from "../azure-account.api";
import { AbstractCredentials, AbstractCredentials2, AuthProviderBase } from './AuthProviderBase';

export class AzureSessionInternal implements AzureSession {
	constructor(
		public environment: Environment,
		public userId: string,
		public tenantId: string,
		public accountInfo: AccountInfo | undefined,
		private _authProvider: AuthProviderBase<unknown>
	) {}

	public get credentials(): AbstractCredentials {
		return this._authProvider.getCredentials(this.environment.name, this.userId, this.tenantId);
	}

	public get credentials2(): AbstractCredentials2 {
		return this._authProvider.getCredentials2(this.environment, this.userId, this.tenantId, this.accountInfo);
	}
}
