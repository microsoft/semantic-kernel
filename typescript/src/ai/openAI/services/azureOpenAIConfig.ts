// Copyright (c) Microsoft Corporation. All rights reserved.

import { Verify } from '../../../utils/verify';
import { BackendConfig } from './backendConfig';

export interface IAzureOpenAIConfig {
    // Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource.
    deploymentName: string;
    // Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart.
    endpoint: string;
    // Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart.
    apiKey: string;
    // Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference.
    apiVersion: string;
}

/**
 * Azure OpenAI configuration.
 */
export class AzureOpenAIConfig extends BackendConfig implements IAzureOpenAIConfig {
    // Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource.
    public deploymentName: string;

    // Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart.
    public endpoint: string;

    // Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart.
    public apiKey: string;

    // Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference.
    public apiVersion: string;

    /**
     * Creates a new AzureOpenAIConfig with supplied values.
     * @param label An identifier used to map semantic functions to backend, decoupling prompts configurations from the actual model used.
     * @param deploymentName Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
     * @param endpoint Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiKey Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiVersion Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
     */
    public constructor(label: string, deploymentName: string, endpoint: string, apiKey: string, apiVersion: string) {
        super(label);

        Verify.notEmpty(deploymentName, 'The deployment name is empty');
        Verify.notEmpty(endpoint, 'The endpoint is empty');
        Verify.startsWith(endpoint, 'https://', 'The endpoint URL must start with https://');
        Verify.notEmpty(apiKey, 'The API key is empty');

        this.deploymentName = deploymentName;
        this.endpoint = endpoint;
        this.apiKey = apiKey;
        this.apiVersion = apiVersion;
    }
}
