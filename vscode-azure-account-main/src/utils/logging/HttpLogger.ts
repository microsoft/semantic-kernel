/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import { parseError } from "@microsoft/vscode-azext-utils";
import { LogLevel, LogOutputChannel } from "vscode";
import { DebugHttpStringifier, HttpStringifier, SimpleHttpStringifier, TraceHttpStringifier } from "./stringifyHttp";

/**
 * A normalized HTTP request for logging.
 */
export interface NormalizedHttpRequest {
    method?: string;
    url?: string;
    headers?: Record<string, unknown>;
    proxy?: {
        host?: string;
        port?: string;
        protocol?: string;
        password?: string;
        username?: string;
    };
    query?: Record<string, string>;
}

/**
 * A normalized HTTP response for logging.
 */
export interface NormalizedHttpResponse {
    status?: number;
    bodyAsText?: string;
    headers?: Record<string, unknown>;
    request: NormalizedHttpRequest;
}

export interface HttpNormalizer<TRequest, TResponse> {
    normalizeRequest(request: TRequest): NormalizedHttpRequest;
    normalizeResponse(response: TResponse): NormalizedHttpResponse;
}

export class HttpLogger<TRequest, TResponse> implements HttpLogger<TRequest, TResponse> {
    constructor(private readonly logOutputChannel: LogOutputChannel, private readonly source: string, private readonly normalizer: HttpNormalizer<TRequest, TResponse>) {}

    logRequest(request: TRequest): void {
        try {
            this.logNormalizedRequest(this.normalizer.normalizeRequest(request));
        } catch (e) {
            const error = parseError(e);
            this.logOutputChannel.error('Error logging request: ' + error.message);
        }
    }

    logResponse(response: TResponse): void {
        try {
            this.logNormalizedResponse(this.normalizer.normalizeResponse(response));
        } catch (e) {
            const error = parseError(e);
            this.logOutputChannel.error('Error logging response: ' + error.message);
        }
    }

    private logNormalizedRequest(request: NormalizedHttpRequest): void {
        if (request.proxy) {
            // if proxy is configured, always log proxy configuration
            this.logOutputChannel.info(new DebugHttpStringifier().stringifyRequest(request, this.source));
        } else {
            this.logOutputChannel.info(this.getStringifier().stringifyRequest(request, this.source));
        }
    }

    private logNormalizedResponse(response: NormalizedHttpResponse): void {
        this.logOutputChannel.info(this.getStringifier().stringifyResponse(response, this.source));
    }

    getStringifier(): HttpStringifier {
        switch(this.logOutputChannel.logLevel) {
            case LogLevel.Debug:
                return new DebugHttpStringifier();
            case LogLevel.Trace:
                return new TraceHttpStringifier();
            default:
                return new SimpleHttpStringifier();
        }
    }
}
