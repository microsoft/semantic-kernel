// Copyright (c) Microsoft. All rights reserved.

import { IAsk } from '../model/Ask';
import { IAskResult } from '../model/AskResult';
import {
    IKeyConfig,
    SK_HTTP_HEADER_API_KEY,
    SK_HTTP_HEADER_COMPLETION,
    SK_HTTP_HEADER_ENDPOINT,
    SK_HTTP_HEADER_MODEL,
    SK_HTTP_HEADER_MSGRAPH
} from '../model/KeyConfig';

interface ServiceRequest {
    commandPath: string;
    method?: string;
    body?: unknown;
    keyConfig: IKeyConfig;
}

export class SemanticKernel {
    // eslint-disable-next-line @typescript-eslint/space-before-function-paren
    constructor(private readonly serviceUrl: string) {}

    public invokeAsync = async (
        keyConfig: IKeyConfig,
        ask: IAsk,
        skillName: string,
        functionName: string,
    ): Promise<IAskResult> => {
        const result = await this.getResponseAsync<IAskResult>({
            commandPath: `/api/skills/${skillName}/invoke/${functionName}`,
            method: 'POST',
            body: ask,
            keyConfig: keyConfig,
        });
        return result;
    };

    private readonly getResponseAsync = async <T>(request: ServiceRequest): Promise<T> => {
        const { commandPath, method, body, keyConfig } = request;

        const headers = new Headers();
        headers.append(SK_HTTP_HEADER_MODEL, keyConfig.deploymentOrModelId);
        headers.append(SK_HTTP_HEADER_ENDPOINT, keyConfig.endpoint);
        headers.append(SK_HTTP_HEADER_API_KEY, keyConfig.key);
        headers.append(SK_HTTP_HEADER_COMPLETION, keyConfig.completionBackend.toString());

        if (keyConfig.graphToken !== undefined) {
            headers.append(SK_HTTP_HEADER_MSGRAPH, keyConfig.graphToken);
        }

        try {
            const response = await fetch(`${this.serviceUrl}${commandPath}`, {
                method: method ?? 'GET',
                headers,
                body: JSON.stringify(body),
            });

            if (!response.ok) {
                throw response.statusText + " => " + await response.text();
            }

            return (await response.json()) as T;
        } catch (e) {
            var additional_error_msg = ''
            if (e instanceof TypeError) {
                // fetch() will reject with a TypeError when a network error is encountered.
                additional_error_msg = '\n\nPlease check you have the function running and that it is accessible by the app'
            }
            throw e + additional_error_msg;
        }
    };
}
