export const SK_HTTP_HEADER_MODEL: string = 'x-ms-sk-model';
export const SK_HTTP_HEADER_ENDPOINT: string = 'x-ms-sk-endpoint';
export const SK_HTTP_HEADER_API_KEY: string = 'x-ms-sk-apikey';
export const SK_HTTP_HEADER_COMPLETION: string = 'x-ms-sk-completion-backend';
export const SK_HTTP_HEADER_MSGRAPH: string = 'x-ms-sk-msgraph';

export interface IKeyConfig {
    completionBackend: number; //OpenAI = 0, Azure OpenAI = 1
    deploymentOrModelId: string;
    label: string;
    endpoint: string;
    key: string;
    graphToken?: string;
}
