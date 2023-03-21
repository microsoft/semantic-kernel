/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ICompletionConfig } from '../semanticFunctions';

export interface ICompleteRequestSettings {
    temperature: number;
    topP: number;
    presencePenalty: number;
    frequencyPenalty: number;
    maxTokens: number;
    stopSequences: string[];
}

export class CompleteRequestSettings {
    public static create(): ICompleteRequestSettings {
        return {
            temperature: 0,
            topP: 0,
            presencePenalty: 0,
            frequencyPenalty: 0,
            maxTokens: 100,
            stopSequences: [],
        };
    }

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

    public static updateFromCompletionConfig(settings: ICompleteRequestSettings, config: ICompletionConfig): void {
        settings.temperature = config.temperature;
        settings.topP = config.top_p;
        settings.presencePenalty = config.presence_penalty;
        settings.frequencyPenalty = config.frequency_penalty;
        settings.maxTokens = config.max_tokens;
        settings.stopSequences = config.stop_sequences;
    }
}
