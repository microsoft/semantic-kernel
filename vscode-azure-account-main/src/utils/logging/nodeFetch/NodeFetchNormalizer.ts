/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import type { Headers, Request, Response } from "node-fetch";
import type { HttpNormalizer, NormalizedHttpRequest, NormalizedHttpResponse } from "../HttpLogger";

type NodeFetchResponseInfo = {response: Response, request: Request, bodyAsText: string };

export class NodeFetchNormalizer implements HttpNormalizer<Request, NodeFetchResponseInfo> {
    normalizeRequest(request: Request): NormalizedHttpRequest {
        return {
            method: request.method,
            url: request.url,
            headers: this.convertNodeFetchHeaders(request.headers),
        };
    }

    normalizeResponse(info: NodeFetchResponseInfo): NormalizedHttpResponse {
        return {
            request: this.normalizeRequest(info.request),
            bodyAsText: info.bodyAsText,
            status: info.response.status,
            headers: this.convertNodeFetchHeaders(info.response.headers),
        }
    }

    private convertNodeFetchHeaders(headers: Headers): Record<string, string> {
        const headersRecord: Record<string, string> = {};
        Object.entries(headers.raw()).forEach(([key, value]) => {
            headersRecord[key] = value.join(', ');
        });
        return headersRecord;
    }
}