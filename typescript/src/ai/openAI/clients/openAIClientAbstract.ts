// Copyright (c) Microsoft Corporation. All rights reserved.

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { HttpStatusCode } from '../../../utils/httpStatusCode';
import { ILogger, NullLogger } from '../../../utils/logger';
import { Verify } from '../../../utils/verify';
import { Embedding } from '../../embeddings';
import { ICompletionResponse, IEmbeddingResponse } from '../httpSchema';

/**
 * An abstract OpenAI Client.
 */
export abstract class OpenAIClientAbstract {
    private readonly _httpClientHandler: AxiosRequestConfig;

    // HTTP user agent sent to remote endpoints
    private readonly httpUserAgent: string = 'Microsoft Semantic Kernel';

    // Logger
    protected readonly log: ILogger;

    // HTTP client
    protected httpClient?: AxiosInstance;

    public constructor(log?: ILogger) {
        this.log = log ?? new NullLogger();
        this._httpClientHandler = { validateStatus: () => true };
        this.httpClient = axios.create(this._httpClientHandler);
        this.httpClient.defaults.headers.common['User-Agent'] = this.httpUserAgent;
    }

    /**
     * Explicit finalizer called by IDisposable
     */
    public dispose(): void {
        this.httpClient = undefined;
        Object.freeze(this);
    }

    /**
     * Asynchronously sends a completion request for the prompt.
     *
     * @param url URL for the completion request API.
     * @param requestBody Prompt to complete.
     * @returns
     */
    protected async executeCompleteRequest(url: string, requestBody: string): Promise<string> {
        try {
            this.log.debug(`Sending completion request to ${url}: ${requestBody}`);

            const result = await this.executePostRequest<ICompletionResponse>(url, requestBody);
            if (result.choices.length < 1) {
                throw new Error('Completions not found');
            }

            return result.choices[0].text;
        } catch (err: any) {
            throw new Error(`Something went wrong: ${(err as Error).toString()}`);
        }
    }

    /**
     * Asynchronously sends an embedding request for the text.
     *
     * @param url URL for the completion request API.
     * @param requestBody Prompt to complete.
     * @returns
     */
    protected async executeEmbeddingRequest(url: string, requestBody: string): Promise<Embedding[]> {
        try {
            const result = await this.executePostRequest<IEmbeddingResponse>(url, requestBody);
            if (!Array.isArray(result.data) || result.data.length < 1) {
                throw new Error('Embeddings not found');
            }

            return result.data.map((e) => new Embedding(e.embedding));
        } catch (err: any) {
            throw new Error(`Something went wrong: ${(err as Error).toString()}`);
        }
    }

    /**
     * Send prompt to LLM model at Open AI endpoint.
     *
     * @param url URL for the completion request API.
     * @param requestBody HTTP request body.
     * @returns Response JSON object.
     */
    private async executePostRequest<T>(url: string, requestBody: string): Promise<T> {
        let responseJson: string;

        try {
            const content = { data: requestBody };
            const response = await this.httpClient?.post(url, content);

            if (!response) {
                throw new Error('Empty response');
            }

            responseJson = response.data;
            if (!response.status) {
                this.log.trace(`HTTP response: ${response.status}`);
                switch (response.status) {
                    case HttpStatusCode.BadRequest:
                    case HttpStatusCode.NotFound:
                    case HttpStatusCode.MethodNotAllowed:
                    case HttpStatusCode.NotAcceptable:
                    case HttpStatusCode.Conflict:
                    case HttpStatusCode.Gone:
                    case HttpStatusCode.LengthRequired:
                    case HttpStatusCode.PreconditionFailed:
                    case HttpStatusCode.RequestEntityTooLarge:
                    case HttpStatusCode.RequestURITooLong:
                    case HttpStatusCode.UnsupportedMediaType:
                    case HttpStatusCode.RequestedRangeNotSatisfiable:
                    case HttpStatusCode.ExpectationFailed:
                    case HttpStatusCode.MisdirectedRequest:
                    case HttpStatusCode.UnprocessableEntity:
                    case HttpStatusCode.Locked:
                    case HttpStatusCode.FailedDependency:
                    case HttpStatusCode.UpgradeRequired:
                    case HttpStatusCode.PreconditionRequired:
                    case HttpStatusCode.RequestHeaderFieldsTooLarge:
                    case HttpStatusCode.HTTPVersionNotSupported:
                        throw new Error(`The request is not valid, HTTP status: ${response.status}`);

                    case HttpStatusCode.Unauthorized:
                    case HttpStatusCode.Forbidden:
                    case HttpStatusCode.ProxyAuthenticationRequired:
                    case HttpStatusCode.UnavailableForLegalReasons:
                    case HttpStatusCode.NetworkAuthenticationRequired:
                        throw new Error(`The request is not authorized, HTTP status: ${response.status}`);

                    case HttpStatusCode.RequestTimeout:
                        throw new Error(`The request timed out, HTTP status: ${response.status}`);

                    case HttpStatusCode.TooManyRequests:
                        throw new Error(`Too many requests, HTTP status: ${response.status}`);

                    case HttpStatusCode.InternalServerError:
                    case HttpStatusCode.NotImplemented:
                    case HttpStatusCode.BadGateway:
                    case HttpStatusCode.ServiceUnavailable:
                    case HttpStatusCode.GatewayTimeout:
                    case HttpStatusCode.InsufficientStorage:
                        throw new Error(`The service failed to process the request, HTTP status: ${response.status}`);

                    default:
                        throw new Error(`Unexpected HTTP response, status: ${response.status}`);
                }
            }
        } catch (err) {
            throw new Error(`Something went wrong: ${(err as Error).toString()}`);
        }

        try {
            const result = JSON.parse(responseJson);
            Verify.notNull(result, 'Response JSON parse error');

            return result;
        } catch (err) {
            throw new Error(`Something went wrong: ${(err as Error).toString()}`);
        }
    }
}
