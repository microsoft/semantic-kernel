// Copyright (c) Microsoft Corporation. All rights reserved.

export interface IEmbeddingResponseIndex {
    embedding: number[];
    index: number;
}

export interface IEmbeddingResponse {
    data: IEmbeddingResponseIndex[];
}
