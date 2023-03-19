// Copyright (c) Microsoft Corporation. All rights reserved.

export interface ICompletionRequest {
    temperature?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
    max_tokens?: number;
    stop?: string | string[];
    n?: number;
    best_of?: number;
    prompt: string;
}

export interface IOpenAICompletionRequest extends ICompletionRequest {
    model?: string;
}

export interface IAzureOpenAICompletionRequest extends ICompletionRequest {}
