// Copyright (c) Microsoft Corporation. All rights reserved.

export interface IEmbeddingRequest {
    input: string[];
}

export interface IOpenAIEmbeddingRequest extends IEmbeddingRequest {
    model: string;
}

export interface IAzureEmbeddingRequest extends IEmbeddingRequest {}
