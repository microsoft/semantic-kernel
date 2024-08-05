/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import { BaseRequestPolicy, HttpOperationResponse, RequestPolicy, RequestPolicyOptionsLike, WebResourceLike } from "@azure/ms-rest-js";
import { LogOutputChannel } from "vscode";
import { HttpLogger } from "../HttpLogger";
import { MsRestNormalizer } from "./MsRestNormalizer";

export class LogRequestPolicy extends BaseRequestPolicy {
    private readonly logger: HttpLogger<WebResourceLike, HttpOperationResponse>;

	constructor(outputChannel: LogOutputChannel, clientName: string, nextPolicy: RequestPolicy, options: RequestPolicyOptionsLike) {
		super(nextPolicy, options);
        this.logger = new HttpLogger(outputChannel, clientName, new MsRestNormalizer());
	}

	sendRequest(webResource: WebResourceLike): Promise<HttpOperationResponse> {
		this.logger.logRequest(webResource);
		
        const result = this._nextPolicy.sendRequest(webResource);
        void result.then((response) => {
			this.logger.logResponse(response);
		});
		return result;
	}
}