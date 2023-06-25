// Copyright (c) Microsoft. All rights reserved.

export const SK_HTTP_HEADER_COMPLETION_MODEL = 'x-ms-sk-completion-model';
export const SK_HTTP_HEADER_COMPLETION_ENDPOINT = 'x-ms-sk-completion-endpoint';
export const SK_HTTP_HEADER_COMPLETION_BACKEND = 'x-ms-sk-completion-backend';
export const SK_HTTP_HEADER_COMPLETION_KEY = 'x-ms-sk-completion-key';

export const SK_HTTP_HEADER_EMBEDDING_MODEL = 'x-ms-sk-embedding-model';
export const SK_HTTP_HEADER_EMBEDDING_ENDPOINT = 'x-ms-sk-embedding-endpoint';
export const SK_HTTP_HEADER_EMBEDDING_BACKEND = 'x-ms-sk-embedding-backend';
export const SK_HTTP_HEADER_EMBEDDING_KEY = 'x-ms-sk-embedding-key';

export const SK_HTTP_HEADER_MSGRAPH = 'x-ms-sk-msgraph';

export interface IBackendConfig {
    backend: number; // OpenAI = 1, Azure OpenAI = 0
    label: string;
    deploymentOrModelId: string;
    endpoint: string;
    key: string;
}

export interface IKeyConfig {
    graphToken?: string;

    embeddingConfig: IBackendConfig;
    completionConfig: IBackendConfig;
}
