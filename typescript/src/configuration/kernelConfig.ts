/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { AzureOpenAIConfig, OpenAIConfig } from '../ai';
import { Verify } from '../diagnostics';
import { IRetryMechanism, PassThroughWithoutRetry } from '../reliability';
import { BackendTypes, IBackendConfig } from './iBackendConfig';

export class KernelConfig {
    private _completionBackends: { [key: string]: IBackendConfig } = {};
    private _embeddingsBackends: { [key: string]: IBackendConfig } = {};
    private _defaultCompletionBackend?: string;
    private _defaultEmbeddingsBackend?: string;
    private _retryMechanism: IRetryMechanism = new PassThroughWithoutRetry();

    /**
     * Global retry logic used for all the backends.
     */
    public get retryMechanism(): IRetryMechanism {
        return this._retryMechanism;
    }

    /**
     * Adds an Azure OpenAI backend to the list.
     * See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
     *
     * @param {string} label An identifier used to map semantic functions to backend,
     * decoupling prompts configurations from the actual model used
     * @param {string} deploymentName Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
     * @param {string} endpoint Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param {string} apiKey Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param {string} apiVersion Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
     * @param {boolean} overwrite Whether to overwrite an existing configuration if the same label exists
     * @returns {Self} Self instance
     */
    public addAzureOpenAICompletionBackend(
        label: string,
        deploymentName: string,
        endpoint: string,
        apiKey: string,
        apiVersion: string = '2022-12-01',
        overwrite: boolean = false
    ): KernelConfig {
        if (!label) {
            throw new Error('The label is empty');
        }

        if (!overwrite && this._completionBackends[label]) {
            throw new Error(`The completion backend cannot be added twice: ${label}`);
        }

        this._completionBackends[label] = {
            backendType: BackendTypes.AzureOpenAI,
            azureOpenAI: AzureOpenAIConfig.create(deploymentName, endpoint, apiKey, apiVersion),
        };

        if (Object.keys(this._completionBackends).length === 1) {
            this._defaultCompletionBackend = label;
        }

        return this;
    }

    /**
     * Adds the OpenAI completion backend to the list.
     * See https://platform.openai.com/docs for service details.
     *
     * @param {string} label An identifier used to map semantic functions to backend,
     * decoupling prompts configurations from the actual model used
     * @param {string} modelId OpenAI model name, see https://platform.openai.com/docs/models
     * @param {string} apiKey OpenAI API key, see https://platform.openai.com/account/api-keys
     * @param {string} orgId OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
     * @param {boolean} overwrite Whether to overwrite an existing configuration if the same label exists
     * @returns {this} Self instance
     */
    public addOpenAICompletionBackend(
        label: string,
        modelId: string,
        apiKey: string,
        orgId?: string,
        overwrite: boolean = false
    ): KernelConfig {
        if (!label) {
            throw new Error('The label is empty');
        }

        if (!overwrite && this._completionBackends[label]) {
            throw new Error(`The completion backend cannot be added twice: ${label}`);
        }

        this._completionBackends[label] = {
            backendType: BackendTypes.OpenAI,
            openAI: OpenAIConfig.create(modelId, apiKey, orgId),
        };

        if (Object.keys(this._completionBackends).length === 1) {
            this._defaultCompletionBackend = label;
        }

        return this;
    }

    /**
     * Adds an Azure OpenAI embeddings backend to the list.
     * See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
     *
     * @param {string} label An identifier used to map semantic functions to backend,
     * decoupling prompts configurations from the actual model used
     * @param {string} deploymentName Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
     * @param {string} endpoint Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param {string} apiKey Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param {string} [apiVersion="2022-12-01"] Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
     * @param {boolean} [overwrite=false] Whether to overwrite an existing configuration if the same label exists
     * @returns {KernelConfig} Self instance
     */
    public addAzureOpenAIEmbeddingsBackend(
        label: string,
        deploymentName: string,
        endpoint: string,
        apiKey: string,
        apiVersion: string = '2022-12-01',
        overwrite: boolean = false
    ): KernelConfig {
        Verify.notEmpty(label, 'The label is empty');

        if (!overwrite && this._embeddingsBackends[label]) {
            throw new Error(`The embeddings backend cannot be added twice: ${label}`);
        }

        this._embeddingsBackends[label] = {
            backendType: BackendTypes.AzureOpenAI,
            azureOpenAI: AzureOpenAIConfig.create(deploymentName, endpoint, apiKey, apiVersion),
        };

        if (Object.keys(this._embeddingsBackends).length === 1) {
            this._defaultEmbeddingsBackend = label;
        }

        return this;
    }

    /**
     * Adds the OpenAI embeddings backend to the list.
     * See https://platform.openai.com/docs for service details.
     *
     * @param {string} label An identifier used to map semantic functions to backend,
     * decoupling prompts configurations from the actual model used
     * @param {string} modelId OpenAI model name, see https://platform.openai.com/docs/models
     * @param {string} apiKey OpenAI API key, see https://platform.openai.com/account/api-keys
     * @param {string} [orgId] OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
     * @param {boolean} [overwrite=false] Whether to overwrite an existing configuration if the same label exists
     * @returns {KernelConfig} Self instance
     */
    public addOpenAIEmbeddingsBackend(
        label: string,
        modelId: string,
        apiKey: string,
        orgId?: string,
        overwrite: boolean = false
    ): KernelConfig {
        Verify.notEmpty(label, 'The label is empty');

        if (!overwrite && this._embeddingsBackends[label]) {
            throw new Error(`The embeddings backend cannot be added twice: ${label}`);
        }

        this._embeddingsBackends[label] = {
            backendType: BackendTypes.OpenAI,
            openAI: OpenAIConfig.create(modelId, apiKey, orgId),
        };

        if (Object.keys(this._embeddingsBackends).length === 1) {
            this._defaultEmbeddingsBackend = label;
        }

        return this;
    }
    public hasCompletionBackend(label: string, condition?: (backendConfig: IBackendConfig) => boolean): boolean {
        return condition === undefined
            ? this._completionBackends.hasOwnProperty(label)
            : Object.keys(this._completionBackends).some(
                  (key) => key === label && condition(this._completionBackends[key])
              );
    }

    public hasEmbeddingsBackend(label: string, condition?: (backendConfig: IBackendConfig) => boolean): boolean {
        return condition === undefined
            ? this._embeddingsBackends.hasOwnProperty(label)
            : Object.keys(this._embeddingsBackends).some(
                  (key) => key === label && condition(this._embeddingsBackends[key])
              );
    }

    public setRetryMechanism(retryMechanism?: IRetryMechanism): this {
        this._retryMechanism = retryMechanism ?? new PassThroughWithoutRetry();
        return this;
    }

    public setDefaultCompletionBackend(label: string): this {
        if (!this._completionBackends.hasOwnProperty(label)) {
            throw new Error(`The completion backend doesn't exist: ${label}`);
        }

        this._defaultCompletionBackend = label;
        return this;
    }

    public get defaultCompletionBackend(): string | undefined {
        return this._defaultCompletionBackend;
    }

    public setDefaultEmbeddingsBackend(label: string): KernelConfig {
        if (!this._embeddingsBackends.hasOwnProperty(label)) {
            throw new Error(`The embeddings backend doesn't exist: ${label}`);
        }

        this._defaultEmbeddingsBackend = label;
        return this;
    }

    public get defaultEmbeddingsBackend(): string | undefined {
        return this._defaultEmbeddingsBackend;
    }

    public getCompletionBackend(name?: string): IBackendConfig {
        if (name === undefined || name === '') {
            if (this._defaultCompletionBackend === undefined) {
                throw new Error(`Completion backend not found: ${name}. No default backend available.`);
            }

            return this._completionBackends[this._defaultCompletionBackend];
        }

        if (this._completionBackends.hasOwnProperty(name)) {
            return this._completionBackends[name];
        }

        if (this._defaultCompletionBackend !== undefined) {
            return this._completionBackends[this._defaultCompletionBackend];
        }

        throw new Error(`Completion backend not found: ${name}. No default backend available.`);
    }

    public getEmbeddingsBackend(name?: string): IBackendConfig {
        if (name === undefined || name === '') {
            if (this._defaultEmbeddingsBackend === undefined) {
                throw new Error(`Embeddings backend not found: ${name}. No default backend available.`);
            }

            return this._embeddingsBackends[this._defaultEmbeddingsBackend];
        }

        if (this._embeddingsBackends.hasOwnProperty(name)) {
            return this._embeddingsBackends[name];
        }

        if (this._defaultEmbeddingsBackend !== undefined) {
            return this._embeddingsBackends[this._defaultEmbeddingsBackend];
        }

        throw new Error(`Embeddings backend not found: ${name}. No default backend available.`);
    }

    public getAllCompletionBackends(): IBackendConfig[] {
        return Object.values(this._completionBackends);
    }

    public getAllEmbeddingsBackends(): IBackendConfig[] {
        return Object.values(this._embeddingsBackends);
    }

    public removeAllBackends(): this {
        this.removeAllCompletionBackends();
        this.removeAllEmbeddingBackends();
        return this;
    }

    public removeAllCompletionBackends(): this {
        this._completionBackends = {};
        this._defaultCompletionBackend = undefined;
        return this;
    }

    public removeAllEmbeddingBackends(): this {
        this._embeddingsBackends = {};
        this._defaultEmbeddingsBackend = undefined;
        return this;
    }

    public removeCompletionBackend(label: string): this {
        delete this._completionBackends[label];
        if (this._defaultCompletionBackend === label) {
            this._defaultCompletionBackend = Object.keys(this._completionBackends)[0];
        }

        return this;
    }

    public removeEmbeddingsBackend(label: string): this {
        delete this._embeddingsBackends[label];
        if (this._defaultEmbeddingsBackend === label) {
            this._defaultEmbeddingsBackend = Object.keys(this._embeddingsBackends)[0];
        }

        return this;
    }
}
