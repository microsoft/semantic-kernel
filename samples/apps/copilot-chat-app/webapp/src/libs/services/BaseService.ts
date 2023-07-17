// Copyright (c) Microsoft. All rights reserved.

import { Plugin } from '../../redux/features/plugins/PluginsState';

interface ServiceRequest {
    commandPath: string;
    method?: string;
    body?: FormData | unknown;
}
const noResponseBodyStatusCodes = [202];

export class BaseService {
    // eslint-disable-next-line @typescript-eslint/space-before-function-paren
    constructor(protected readonly serviceUrl: string) {}

    protected readonly getResponseAsync = async <T>(
        request: ServiceRequest,
        accessToken: string,
        enabledPlugins?: Plugin[],
    ): Promise<T> => {
        const { commandPath, method, body } = request;
        const isFormData = body instanceof FormData;

        const headers = new Headers({
            Authorization: `Bearer ${accessToken}`,
        });

        if (!isFormData) {
            headers.append('Content-Type', 'application/json');
        }

        // API key auth for private hosted instances
        if (process.env.REACT_APP_SK_API_KEY) {
            headers.append('x-sk-api-key', process.env.REACT_APP_SK_API_KEY);
        }

        if (enabledPlugins && enabledPlugins.length > 0) {
            // For each enabled plugin, pass its auth information as a customer header
            // to the backend so the server can authenticate to the plugin
            for (const plugin of enabledPlugins) {
                headers.append(`x-sk-copilot-${plugin.headerTag}-auth`, plugin.authData ?? '');
            }
        }

        try {
            const requestUrl = new URL(commandPath, this.serviceUrl);
            const response = await fetch(requestUrl, {
                method: method ?? 'GET',
                body: isFormData ? body : JSON.stringify(body),
                headers,
            });

            if (!response.ok) {
                const responseText = await response.text();
                const errorMessage = `${response.status}: ${response.statusText}${
                    responseText ? ` => ${responseText}` : ''
                }`;

                throw Object.assign(new Error(errorMessage));
            }

            return (noResponseBodyStatusCodes.includes(response.status) ? {} : await response.json()) as T;
        } catch (e: any) {
            let additionalErrorMsg = '';
            if (e instanceof TypeError) {
                // fetch() will reject with a TypeError when a network error is encountered.
                additionalErrorMsg =
                    '\n\nPlease check that your backend is running and that it is accessible by the app';
            }
            throw Object.assign(new Error(`${e as string} ${additionalErrorMsg}`));
        }
    };
}
