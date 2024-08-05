/*---------------------------------------------------------------------------------------------
*  Copyright (c) Microsoft Corporation. All rights reserved.
*  Licensed under the MIT License. See License.txt in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import { AxiosRequestConfig, AxiosResponse, AxiosStatic } from 'axios';
import { LogOutputChannel } from "vscode";
import { HttpLogger, HttpNormalizer, NormalizedHttpRequest, NormalizedHttpResponse } from "../HttpLogger";

export class AxiosNormalizer implements HttpNormalizer<AxiosRequestConfig, AxiosResponse> {
    normalizeRequest(request: AxiosRequestConfig): NormalizedHttpRequest {
        const query = new URLSearchParams(request.data as string);
        const queryParams = Array.from(query.entries());
        const rec: Record<string, string> = {};
        queryParams.forEach(([name, value]) => rec[name] = value);
    
        const sanitizedHeaders: Record<string, string> = {};
        Object.entries(request.headers).forEach(([key, value]) => {
            if (typeof value !== 'object') {
                sanitizedHeaders[key] = String(value);
            }
        });
    
        return {
            url: request.url,
            method: request.method?.toUpperCase(),
            headers: sanitizedHeaders,
            query: rec,
            proxy: request.proxy ? {
                host: request.proxy.host,
                port: String(request.proxy.port),
                protocol: request.proxy.protocol,
                password: request.proxy.auth?.password,
                username: request.proxy.auth?.username,
            } : undefined,
        };
    }

    normalizeResponse(response: AxiosResponse): NormalizedHttpResponse {
        return {
            headers: response.headers as Record<string, string>,
            request: this.normalizeRequest(response.config),
            bodyAsText: JSON.stringify(response.data),
            status: response.status,
        };
    }
}

export function setupAxiosLogging(axios: AxiosStatic, logOutputChannel: LogOutputChannel): void {
    const axiosLogger = new HttpLogger(logOutputChannel, 'Axios', new AxiosNormalizer());

    axios.interceptors.request.use((requestConfig) => {
        axiosLogger.logRequest(requestConfig);
        return requestConfig;
    });
    
    axios.interceptors.response.use((response) => {
        axiosLogger.logResponse(response);
        return response;
    });
}