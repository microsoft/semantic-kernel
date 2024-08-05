/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as http from 'http';
import * as request from 'request-promise';
import type { HttpNormalizer, NormalizedHttpRequest, NormalizedHttpResponse } from "../HttpLogger";

type RequestResponseInfo = { response: http.IncomingMessage & { body?: unknown }, request: request.Options };

export class RequestNormalizer implements HttpNormalizer<request.Options, RequestResponseInfo> {
    normalizeRequest(options: request.Options): NormalizedHttpRequest {
        return { 
            ...options, 
            url: 'url' in options ? options.url.toString() : options.uri.toString() 
        };
    }

    normalizeResponse(info: RequestResponseInfo): NormalizedHttpResponse {
        return {
            request: this.normalizeRequest(info.request),
            status: info.response.statusCode,
            headers: info.response.headers,
            bodyAsText: 'body' in info.response ? JSON.stringify(info.response.body) : undefined,
        }
    }
}