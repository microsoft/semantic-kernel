// Copyright (c) Microsoft. All rights reserved.

import { IAsk } from './model/Ask';
import { IAskResult } from './model/AskResult';

interface ServiceRequest {
    commandPath: string;
    method?: string;
    body?: unknown;
    token?: string;
}

export class SemanticKernel {
    // eslint-disable-next-line @typescript-eslint/space-before-function-paren
    constructor(private readonly serviceUrl: string) { }

    public invokeAsync = async (
        token: string,
        ask: IAsk,
        skillName: string,
        functionName: string,
    ): Promise<IAskResult> => {
        if (!token) {
           throw new Error("Missing valid AAD token");
        }
        const result = await this.getResponseAsync<IAskResult>({
            commandPath: `/api/skills/${skillName}/invoke/${functionName}`,
            method: 'POST',
            body: ask,
            token: token
        });
        return result;
    };

    private readonly getResponseAsync = async <T>(request: ServiceRequest): Promise<T> => {
        const { commandPath, method, body, token } = request;

        try {
            const response = await fetch(`${this.serviceUrl}${commandPath}`, {
                method: method ?? 'GET',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
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