/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { ILogger, NullLogger } from '../../../utils/logger';
import { Embedding } from '../../embeddings';
import { ICompletionResponse, IEmbeddingResponse } from '../httpSchema';

export abstract class OpenAIClientAbstract {
    private _httpClientHandler: AxiosRequestConfig;

    // HTTP user agent sent to remote endpoints
    private readonly HTTPUseragent = 'Microsoft Semantic Kernel';

    constructor(log?: ILogger) {
        this.log = log ?? new NullLogger();

        // TODO: allow injection of retry logic, e.g. Polly
        this._httpClientHandler = { validateStatus: () => true };
        this.httpClient = axios.create(this._httpClientHandler);
        this.httpClient.defaults.headers.common['User-Agent'] = this.HTTPUseragent;
    }

    protected log: ILogger;
    protected httpClient: AxiosInstance;

    async executeCompleteRequest(url: string, requestBody: string): Promise<string> {
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

    async executeEmbeddingRequest(url: string, requestBody: string): Promise<Embedding[]> {
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

    // Explicit finalizer called by IDisposable
    public dispose(): void {
        this.httpClient = undefined;
        Object.freeze(this);
    }

    private async executePostRequest<T>(url: string, requestBody: string): Promise<T> {
        let responseJson: string;

        try {
            const content = { data: requestBody };
            const response = await this.httpClient.post(url, content);

            if (!response) {
                throw new Error('Empty response');
            }

            responseJson = response.data;
            if (!response.status) {
                this.log.trace(`HTTP response: ${response.status}`);
                switch (response.status) {
                    case 400:
                    case 405:
                    case 404:
                    case 406:
                    case 409:
                    case 410:
                    case 411:
                    case 412:
                    case 413:
                    case 414:
                    case 415:
                    case 416:
                    case 417:
                    case 422:
                    case 423:
                    case 424:
                    case 428:
                    case 429:
                    case 431:
                    case 451:
                        throw new Error(`The request is not valid, HTTP status: ${response.status}`);

                    case 401:
                    case 403:
                    case 407:
                    case 451:
                        throw new Error(`The request is not authorized, HTTP status: ${response.status}`);

                    case 408:
                        throw new Error(`The request timed out, HTTP status: ${response.status}`);

                    case 429:
                        throw new Error(`Too many requests, HTTP status: ${response.status}`);

                    case 500:
                    case 501:
                    case 502:
                    case 503:
                    case 504:
                    case 507:
                        throw new Error(`The service failed to process the request, HTTP status: ${response.status}`);

                    default:
                        throw new Error(`Unexpected HTTP response, status: ${response.status}`);
                }
            }
        } catch (err: any) {
            throw new Error(`Something went wrong: ${(err as Error).toString()}`);
        }

        try {
            const result = JSON.parse(responseJson);
            if (result) {
                return result;
            }

            throw new Error('Response JSON parse error');
        } catch (err: any) {
            throw new Error(`Something went wrong: ${(err as Error).toString()}`);
        }
    }
}
