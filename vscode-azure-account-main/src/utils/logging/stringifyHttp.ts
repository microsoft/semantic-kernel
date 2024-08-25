/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import { NormalizedHttpRequest, NormalizedHttpResponse } from "./HttpLogger";

export interface HttpStringifier {
    stringifyRequest(request: NormalizedHttpRequest, source: string): string;
    stringifyResponse(request: NormalizedHttpRequest, source: string): string;
}

/**
 * @param request Request to log
 * @param source Source of the request, ex: Axios
 * @param verbose Logs the headers and query parameters if true
 * @returns stringified request
 */
function stringifyRequest(request: NormalizedHttpRequest, source: string, verbose?: boolean): string {
    let message = `[${source} Request]`;
    message = `\n┌────── ${source} Request ${request.method} ${request.url}`;
    if (verbose) {
        message += stringifyRecord(request.headers ?? {}, 'Headers');
        message += stringifyRecord(request.query ?? {}, 'Query parameters');
    }
    message += stringifyRecord(request.proxy ?? {}, 'Proxy configuration', true);
    message += `\n└───────────────────────────────────────────────────`;
    return message;
}

/**
 * 
 * @param response Response to log
 * @param source Source of the response, ex: Axios
 * @param hideBody Hides the body and prints the string instead
 * @returns stringified request
 */
function stringifyResponse(response: NormalizedHttpResponse, source: string, hideBody?: string): string {
    let message = `[${source} Response]`;
    message += `\n┌────── ${source} Response ${response.request.method} - ${response.request.url}`;
    message += stringifyRecord(response.headers ?? {}, 'Headers');
    // only show the body if the log level is trace
    message += `\n\tBody: ${hideBody ?? `\n\t${response.bodyAsText?.split('\n').join('\n\t')}`}`;
    message += `\n└───────────────────────────────────────────────────`;
    return message;
}

function stringifyRecord(record: Record<string, unknown>, label: string, hideCount?: boolean): string {
    const entries = Object.entries(record).sort().filter(([_, value]) => typeof value !== 'object');
    const entriesString = '\n\t└ ' + entries.map(([name, value]) => `${name}: "${Array.isArray(value) ? value.join(', ') : String(value)}"`).join('\n\t└ ');
    return `\n\t${label}${entries.length && !hideCount ? ` (${entries.length})` : ''}:${entries.length === 0 ? ' None' : entriesString}`;
}

export class SimpleHttpStringifier implements HttpStringifier {
    stringifyRequest(request: NormalizedHttpRequest, source: string): string {
        return `[${source} Request] ${request.method} ${request.url}`;
    }

    stringifyResponse(response: NormalizedHttpResponse, source: string): string {
        return `[${source} Response] ${response.status} - ${response.request.method} ${response.request.url}`;
    }
}

export class DebugHttpStringifier implements HttpStringifier {
    stringifyRequest(request: NormalizedHttpRequest, source: string): string {
       return stringifyRequest(request, source, false);
    }

    stringifyResponse(response: NormalizedHttpResponse, source: string): string {
        return stringifyResponse(response, source, "Hidden. Set log level to 'Trace' to see body.");
    }

    protected stringifyRecord(record: Record<string, unknown>, label: string, hideCount?: boolean): string {
        const entries = Object.entries(record).sort().filter(([_, value]) => typeof value !== 'object');
        const entriesString = '\n\t└ ' + entries.map(([name, value]) => `${name}: "${Array.isArray(value) ? value.join(', ') : String(value)}"`).join('\n\t└ ');
        return `\n\t${label}${entries.length && !hideCount ? ` (${entries.length})` : ''}:${entries.length === 0 ? ' None' : entriesString}`;
    }
}

export class TraceHttpStringifier implements HttpStringifier {
    stringifyRequest(request: NormalizedHttpRequest, source: string): string {
        return stringifyRequest(request, source, true);
    }

    stringifyResponse(response: NormalizedHttpResponse, source: string): string {
        return stringifyResponse(response, source);
    }
}
