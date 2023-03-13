// Copyright (c) Microsoft. All rights reserved.

export const SK_HTTP_HEADER_COMPLETION_MODEL: string = "x-ms-sk-completion-model";
export const SK_HTTP_HEADER_EMBEDDING_MODEL: string = "x-ms-sk-embedding-model";
export const SK_HTTP_HEADER_ENDPOINT: string = "x-ms-sk-endpoint";
export const SK_HTTP_HEADER_API_KEY: string = "x-ms-sk-apikey";
export const SK_HTTP_HEADER_COMPLETION: string = "x-ms-sk-completion-backend";
export const SK_HTTP_HEADER_EMBEDDING: string = "x-ms-sk-embedding-backend";
export const SK_HTTP_HEADER_MSGRAPH: string = "x-ms-sk-msgraph";

export interface IKeyConfig {
    embeddingBackend: number; //OpenAI = 0, Azure OpenAI = 1
    completionBackend: number; //OpenAI = 0, Azure OpenAI = 1
    completionDeploymentOrModelId: string;
    embeddingDeploymentOrModelId: string;
    label: string;
    endpoint: string;
    key: string;
    graphToken?: string;
}