/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

export interface IEmbeddingRequest {
    input: string[];
}

export interface IOpenAIEmbeddingRequest extends IEmbeddingRequest {
    model: string;
}

export interface IAzureEmbeddingRequest extends IEmbeddingRequest {}
