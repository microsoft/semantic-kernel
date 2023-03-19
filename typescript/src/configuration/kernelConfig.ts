import { AzureOpenAIConfig, OpenAIConfig } from '../ai/openAI';
import { Verify } from '../utils/verify';
import { IBackendConfig } from './iBackendConfig';

export class KernelConfig {
    private _completionBackends: { [key: string]: IBackendConfig } = {};
    private _embeddingsBackends: { [key: string]: IBackendConfig } = {};
    private _defaultCompletionBackend?: string;
    private _defaultEmbeddingsBackend?: string;

    /**
     * Adds an Azure OpenAI backend to the list.
     *
     * @see https://learn.microsoft.com/azure/cognitive-services/openai for service details.
     * @param label An identifier used to map semantic functions to backend, decoupling prompts configurations from the actual model used
     * @param deploymentName Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
     * @param endpoint Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiKey Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiVersion Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
     * @param overwrite Whether to overwrite an existing configuration if the same label exists
     * @returns Self instance
     */
    public addAzureOpenAICompletionBackend(
        label: string,
        deploymentName: string,
        endpoint: string,
        apiKey: string,
        apiVersion: string = '2022-12-01',
        overwrite: boolean = false
    ): KernelConfig {
        Verify.notEmpty(label, 'The label is empty');

        if (!overwrite && this._completionBackends[label]) {
            throw new Error(`A completion backend already exists for the label: ${label}`);
        }

        this._completionBackends[label] = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        if (Object.keys(this._completionBackends).length === 1) {
            this._defaultCompletionBackend = label;
        }

        return this;
    }

    /**
     * Adds the OpenAI completion backend to the list.
     *
     * @see https://platform.openai.com/docs for service details.
     * @param label An identifier used to map semantic functions to backend, decoupling prompts configurations from the actual model used
     * @param modelId OpenAI model name, see https://platform.openai.com/docs/models
     * @param apiKey OpenAI API key, see https://platform.openai.com/account/api-keys
     * @param orgId OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
     * @param overwrite Whether to overwrite an existing configuration if the same label exists
     * @returns Self instance
     */
    public addOpenAICompletionBackend(
        label: string,
        modelId: string,
        apiKey: string,
        orgId?: string,
        overwrite: boolean = false
    ): KernelConfig {
        Verify.notEmpty(label, 'The backend label is empty');

        if (!overwrite && this._completionBackends[label]) {
            throw new Error(`A completion backend already exists for the label: ${label}`);
        }

        this._completionBackends[label] = new OpenAIConfig(label, modelId, apiKey, orgId);

        if (Object.keys(this._completionBackends).length === 1) {
            this._defaultCompletionBackend = label;
        }

        return this;
    }

    /**
     * Adds an Azure OpenAI embeddings backend to the list.
     *
     * @see https://learn.microsoft.com/azure/cognitive-services/openai for service details.
     * @param label An identifier used to map semantic functions to backend, decoupling prompts configurations from the actual model used
     * @param deploymentName Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
     * @param endpoint Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiKey Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
     * @param overwrite Whether to overwrite an existing configuration if the same label exists
     * @returns Self instance
     */
    public addAzureOpenAIEmbeddingsBackend(
        label: string,
        deploymentName: string,
        endpoint: string,
        apiKey: string,
        apiVersion: string = '2022-12-01',
        overwrite: boolean = false
    ): KernelConfig {
        Verify.notEmpty(label, 'The backend label is empty');

        if (!overwrite && this._embeddingsBackends[label]) {
            throw new Error(`An embeddings backend already exists for the label: ${label}`);
        }

        this._embeddingsBackends[label] = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        if (Object.keys(this._embeddingsBackends).length === 1) {
            this._defaultEmbeddingsBackend = label;
        }

        return this;
    }

    /**
     * Adds the OpenAI embeddings backend to the list.
     *
     * @see https://platform.openai.com/docs for service details.
     * @param label An identifier used to map semantic functions to backend, decoupling prompts configurations from the actual model used
     * @param modelId OpenAI model name, see https://platform.openai.com/docs/models
     * @param apiKey OpenAI API key, see https://platform.openai.com/account/api-keys
     * @param orgId OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
     * @param overwrite Whether to overwrite an existing configuration if the same label exists
     * @returns Self instance
     */
    public addOpenAIEmbeddingsBackend(
        label: string,
        modelId: string,
        apiKey: string,
        orgId?: string,
        overwrite: boolean = false
    ): KernelConfig {
        Verify.notEmpty(label, 'The backend label is empty');

        if (!overwrite && this._embeddingsBackends[label]) {
            throw new Error(`An embeddings backend already exists for the label: ${label}`);
        }

        this._embeddingsBackends[label] = new OpenAIConfig(label, modelId, apiKey, orgId);

        if (Object.keys(this._embeddingsBackends).length === 1) {
            this._defaultEmbeddingsBackend = label;
        }

        return this;
    }

    /**
     * Check whether a given completion backend is in the configuration.
     *
     * @param label Name of completion backend to look for.
     * @param condition Optional condition that must be met for a backend to be deemed present.
     * @returns true when a completion backend matching the giving label is present, false otherwise.
     */
    public hasCompletionBackend(label: string, condition?: (backendConfig: IBackendConfig) => boolean): boolean {
        return condition
            ? Object.keys(this._completionBackends).some(
                  (key) => key === label && condition(this._completionBackends[key])
              )
            : this._completionBackends.hasOwnProperty(label);
    }

    /**
     * Check whether a given embeddings backend is in the configuration.
     *
     * @param label Name of embeddings backend to look for.
     * @param condition Optional condition that must be met for a backend to be deemed present.
     * @returns true when an embeddings backend matching the giving label is present, false otherwise.
     */
    public hasEmbeddingsBackend(label: string, condition?: (backendConfig: IBackendConfig) => boolean): boolean {
        return condition
            ? Object.keys(this._embeddingsBackends).some(
                  (key) => key === label && condition(this._embeddingsBackends[key])
              )
            : this._embeddingsBackends.hasOwnProperty(label);
    }

    /**
     * Set the default completion backend to use for the kernel.
     *
     * @param label Label of completion backend to use.
     * @returns The updated kernel configuration.
     */
    public setDefaultCompletionBackend(label: string): this {
        if (!this._completionBackends.hasOwnProperty(label)) {
            throw new Error(`The completion backend doesn't exist with label: ${label}`);
        }

        this._defaultCompletionBackend = label;
        return this;
    }

    /**
     * Default completion backend.
     */
    public get defaultCompletionBackend(): string | undefined {
        return this._defaultCompletionBackend;
    }

    /**
     * Set the default embeddings backend to use for the kernel.
     *
     * @param label Label of embeddings backend to use.
     * @returns The updated kernel configuration.
     */
    public setDefaultEmbeddingsBackend(label: string): KernelConfig {
        if (!this._embeddingsBackends.hasOwnProperty(label)) {
            throw new Error(`The embeddings backend doesn't exist: ${label}`);
        }

        this._defaultEmbeddingsBackend = label;
        return this;
    }

    /**
     * Default embeddings backend.
     */
    public get defaultEmbeddingsBackend(): string | undefined {
        return this._defaultEmbeddingsBackend;
    }

    /**
     * Get the completion backend configuration matching the given label or the default if a label is not provided or not found.
     *
     * @param label Optional label of the desired backend.
     * @returns The completion backend configuration matching the given label or the default.
     */
    public getCompletionBackend(label?: string): IBackendConfig {
        if (!label) {
            if (!this._defaultCompletionBackend) {
                throw new Error(`A label was not provided and no default completion backend is available.`);
            }

            return this._completionBackends[this._defaultCompletionBackend];
        }

        if (this._completionBackends.hasOwnProperty(label)) {
            return this._completionBackends[label];
        }

        if (this._defaultCompletionBackend) {
            return this._completionBackends[this._defaultCompletionBackend];
        }

        throw new Error(
            `Completion backend not found with label: ${label} and no default completion backend is available.`
        );
    }

    /**
     * Get the embeddings backend configuration matching the given label or the default if a label is not provided or not found.
     *
     * @param label Optional label of the desired backend.
     * @returns The embeddings backend configuration matching the given label or the default.
     */
    public getEmbeddingsBackend(label?: string): IBackendConfig {
        if (!label) {
            if (!this._defaultEmbeddingsBackend) {
                throw new Error(`A label was not provided and no default embeddings backend is available.`);
            }

            return this._embeddingsBackends[this._defaultEmbeddingsBackend];
        }

        if (this._embeddingsBackends.hasOwnProperty(label)) {
            return this._embeddingsBackends[label];
        }

        if (this._defaultEmbeddingsBackend) {
            return this._embeddingsBackends[this._defaultEmbeddingsBackend];
        }

        throw new Error(
            `Embeddings backend not found with label: ${label} and no default embeddings backend is available.`
        );
    }

    /**
     * Get all completion backends.
     *
     * @returns IEnumerable of all completion backends in the kernel configuration.
     */
    public getAllCompletionBackends(): IBackendConfig[] {
        return Object.values(this._completionBackends);
    }

    /**
     * Get all embeddings backends.
     *
     * @returns IEnumerable of all embeddings backends in the kernel configuration.
     */
    public getAllEmbeddingsBackends(): IBackendConfig[] {
        return Object.values(this._embeddingsBackends);
    }

    /**
     * Remove the completion backend with the given label.
     *
     * @param label Label of backend to remove.
     * @returns The updated kernel configuration.
     */
    public removeCompletionBackend(label: string): this {
        delete this._completionBackends[label];
        if (this._defaultCompletionBackend === label) {
            this._defaultCompletionBackend = Object.keys(this._completionBackends)[0];
        }

        return this;
    }

    /**
     * Remove the embeddings backend with the given label.
     *
     * @param label Label of backend to remove.
     * @returns The updated kernel configuration.
     */
    public removeEmbeddingsBackend(label: string): this {
        delete this._embeddingsBackends[label];
        if (this._defaultEmbeddingsBackend === label) {
            this._defaultEmbeddingsBackend = Object.keys(this._embeddingsBackends)[0];
        }

        return this;
    }

    /**
     * Remove all completion backends.
     *
     * @returns The updated kernel configuration.
     */
    public removeAllCompletionBackends(): this {
        this._completionBackends = {};
        this._defaultCompletionBackend = undefined;
        return this;
    }

    /**
     * Remove all embeddings backends.
     *
     * @returns The updated kernel configuration.
     */
    public removeAllEmbeddingBackends(): this {
        this._embeddingsBackends = {};
        this._defaultEmbeddingsBackend = undefined;
        return this;
    }

    /**
     * Remove all backends.
     *
     * @returns The updated kernel configuration.
     */
    public removeAllBackends(): this {
        this.removeAllCompletionBackends();
        this.removeAllEmbeddingBackends();
        return this;
    }
}
