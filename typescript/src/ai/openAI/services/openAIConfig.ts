// Copyright (c) Microsoft Corporation. All rights reserved.

import { Verify } from '../../../utils/verify';
import { BackendConfig } from './backendConfig';

export interface IOpenAIConfig {
    // OpenAI model name, see https://platform.openai.com/docs/models.
    modelId: string;
    // OpenAI API key, see https://platform.openai.com/account/api-keys.
    apiKey: string;
    // OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
    orgId?: string;
}

/**
 * OpenAI configuration.
 */
export class OpenAIConfig extends BackendConfig implements IOpenAIConfig {
    // OpenAI model name, see https://platform.openai.com/docs/models.
    public readonly modelId: string;

    // OpenAI API key, see https://platform.openai.com/account/api-keys.
    public readonly apiKey: string;

    // OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
    public readonly orgId?: string;

    /**
     * Creates a new OpenAIConfig with supplied values.
     * @param label An identifier used to map semantic functions to backend, decoupling prompts configurations from the actual model used.
     * @param modelId OpenAI model name, see https://platform.openai.com/docs/models.
     * @param apiKey OpenAI API key, see https://platform.openai.com/account/api-keys.
     * @param orgId OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
     */
    public constructor(label: string, modelId: string, apiKey: string, orgId?: string) {
        super(label);

        Verify.notEmpty(modelId, 'The model ID is empty');
        Verify.notEmpty(apiKey, 'The API key is empty');

        this.modelId = modelId;
        this.apiKey = apiKey;
        this.orgId = orgId;
    }
}
