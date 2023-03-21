/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export interface ICompletionConfig {
    temperature: number;
    top_p: number;
    presence_penalty: number;
    frequency_penalty: number;
    max_tokens: number;
    stop_sequences?: string[];
}

export interface IInputParameter {
    name: string;
    description: string;
    defaultValue: string;
}

export interface IInputConfig {
    parameters?: IInputParameter[];
}

export interface IPromptTemplateConfig {
    schema: number;
    type: string;
    description: string;
    completion: ICompletionConfig;
    default_backends?: string[];
    input?: IInputConfig;
}

export class PromptTemplateConfig {
    public static compact(config: IPromptTemplateConfig): IPromptTemplateConfig {
        if (config.completion.stop_sequences.length === 0) {
            config.completion.stop_sequences = undefined;
        }

        if (config.default_backends.length === 0) {
            config.default_backends = undefined;
        }

        return config;
    }

    public static fromJson(json: string): IPromptTemplateConfig {
        const result = JSON.parse(json) as IPromptTemplateConfig;
        if (!result) {
            throw new Error('Unable to deserialize prompt template config. The deserialized returned NULL.');
        }

        return result;
    }
}
