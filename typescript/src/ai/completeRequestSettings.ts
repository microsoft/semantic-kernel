// Copyright (c) Microsoft Corporation. All rights reserved.

import { ICompletionConfig } from '../semanticFunctions';

export interface ICompleteRequestSettings {
    temperature: number;
    topP: number;
    presencePenalty: number;
    frequencyPenalty: number;
    maxTokens: number;
    stopSequences?: string[];
}

/**
 * Settings for a completion request.
 */
export class CompleteRequestSettings {
    // Temperature controls the randomness of the completion. The higher the temperature, the more random the completion.
    public temperature: number = 0.0;

    // TopP controls the diversity of the completion. The higher the TopP, the more diverse the completion.
    public topP: number = 0.0;

    // Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
    public presencePenalty: number = 0.0;

    // Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    public frequencyPenalty: number = 0.0;

    // The maximum number of tokens to generate in the completion.
    public maxTokens: number = 100;

    // Sequences where the completion will stop generating further tokens.
    public stopSequences: string[] = [];

    /**
     * Create a new settings object with the values from another settings object.
     * @param config Completion configuration
     * @returns Settings for completion request
     */
    public static fromCompletionConfig(config: ICompletionConfig): ICompleteRequestSettings {
        return {
            temperature: config.temperature,
            topP: config.top_p,
            presencePenalty: config.presence_penalty,
            frequencyPenalty: config.frequency_penalty,
            maxTokens: config.max_tokens,
            stopSequences: config.stop_sequences,
        };
    }
}
