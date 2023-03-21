/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Verify } from '../../../diagnostics';

export interface IAzureOpenAIConfig {
    deploymentName: string;
    endpoint: string;
    apiKey: string;
    apiVersion: string;
}

/**
 * Azure OpenAI configuration.
 * TODO: support for AAD auth.
 */
export class AzureOpenAIConfig {
    public static create(
        deploymentName: string,
        endpoint: string,
        apiKey: string,
        apiVersion: string
    ): IAzureOpenAIConfig {
        Verify.notEmpty(deploymentName, 'The deployment name is empty');
        Verify.notEmpty(endpoint, 'The endpoint is empty');
        Verify.startsWith(endpoint, 'https://', 'The endpoint URL must start with https://');
        Verify.notEmpty(apiKey, 'The API key is empty');

        return { deploymentName, endpoint, apiKey, apiVersion };
    }
}
