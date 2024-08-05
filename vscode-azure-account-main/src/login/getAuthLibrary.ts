/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { callWithTelemetryAndErrorHandlingSync, IActionContext } from "@microsoft/vscode-azext-utils";
import { AuthLibrary, authLibrarySetting } from "../constants";
import { getSettingValue } from "../utils/settingUtils";

export function getAuthLibrary(): AuthLibrary {
	return callWithTelemetryAndErrorHandlingSync('getAuthLibrary', (context: IActionContext) => {
		let authLibrary: AuthLibrary | undefined = getSettingValue(authLibrarySetting);
		if (!authLibrary) {
			authLibrary = 'ADAL';
			context.telemetry.properties.failedToReadAuthLibrarySetting = 'true';
		}

		context.telemetry.properties.authLibrarySetting = authLibrary;
		return authLibrary;
	}) as AuthLibrary;
}
