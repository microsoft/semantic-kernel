/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import { HttpOperationResponse, WebResourceLike } from "@azure/ms-rest-js";
import { HttpNormalizer, NormalizedHttpRequest, NormalizedHttpResponse } from "../HttpLogger";

export class MsRestNormalizer implements HttpNormalizer<WebResourceLike, HttpOperationResponse> {
    normalizeRequest(request: WebResourceLike): NormalizedHttpRequest {
        return {
            method: request.method,
            url: request.url,
            headers: request.headers.rawHeaders(),
            query: request.query,
            proxy: request.proxySettings ? {
                password: request.proxySettings.password,
                username: request.proxySettings.username,
                host: request.proxySettings.host,
                port: String(request.proxySettings.port),
            } : undefined,
        };
    }

    normalizeResponse(response: HttpOperationResponse): NormalizedHttpResponse {
        return {
            headers: response.headers.rawHeaders(),
            request: this.normalizeRequest(response.request),
            bodyAsText: response.bodyAsText ?? undefined,
            status: response.status,
        };
    }
}