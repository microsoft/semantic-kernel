/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Verify } from '../../../diagnostics';

export interface IOpenAIConfig {
    modelId: string;
    apiKey: string;
    orgId?: string;
}

/**
 * OpenAI configuration.
 * TODO: allow overriding endpoint.
 */
export class OpenAIConfig {
    public static create(modelId: string, apiKey: string, orgId?: string): IOpenAIConfig {
        Verify.notEmpty(modelId, 'The model ID is empty');
        Verify.notEmpty(apiKey, 'The API key is empty');

        return { modelId, apiKey, orgId };
    }
}
