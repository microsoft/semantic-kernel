// Copyright (c) Microsoft Corporation. All rights reserved.

import { ILogger } from '../../../utils/logger';
import { Verify } from '../../../utils/verify';
import { IAzureOpenAIDeployment } from '../httpSchema';
import { OpenAIClientAbstract } from './openAIClientAbstract';

// Caching Azure details across multiple instances so we don't have to use "deployment names"
const s_deploymentsCached = new Map<string, boolean>();
const s_deploymentToModel = new Map<string, string>();
const s_modelToDeployment = new Map<string, string>();

/**
 * An abstract Azure OpenAI Client.
 */
export abstract class AzureOpenAIClientAbstract extends OpenAIClientAbstract {
    private _azureOpenAIApiVersion: string;

    // Default Azure OpenAI REST API version
    protected static readonly defaultAzureAPIVersion = '2022-12-01';
    // Azure endpoint of your models
    protected get azureOpenAIApiVersion(): string {
        return this._azureOpenAIApiVersion;
    }
    protected set azureOpenAIApiVersion(value: string) {
        Verify.notEmpty(value, 'Invalid Azure OpenAI API version, the value is empty');
    }
    // Azure endpoint of your models
    protected endpoint: string = '';

    /**
     * Construct an AzureOpenAIClientAbstract object.
     *
     * @constructor
     * @param log Logger.
     */
    public constructor(log?: ILogger) {
        super(log);
        this._azureOpenAIApiVersion = AzureOpenAIClientAbstract.defaultAzureAPIVersion;
    }

    /**
     * Returns the deployment name of the model ID.
     *
     * @param modelId Azure OpenAI model ID.
     * @returns Name of the deployment for the model ID.
     */
    protected async getDeploymentName(modelId: string): Promise<string> {
        const fullModelId = `${this.endpoint}:${modelId}`;

        // If the value is a deployment name
        if (s_deploymentToModel.has(fullModelId)) {
            return modelId;
        }

        // If the value is a model ID present in the cache
        if (s_modelToDeployment.has(fullModelId)) {
            return s_modelToDeployment.get(fullModelId) as string;
        }

        // If the cache has already been warmed up
        let modelsAvailable: string;
        if (s_deploymentsCached.has(this.endpoint)) {
            modelsAvailable = Array.from(s_modelToDeployment.keys()).join(', ');
            throw new Error(
                `Model '${modelId}' not available on ${this.endpoint}. ` +
                    `Available models: ${modelsAvailable}. Deploy the model and restart the application.`
            );
        }

        await this.cacheDeployments();

        if (s_modelToDeployment.has(fullModelId)) {
            return s_modelToDeployment.get(fullModelId) as string;
        }

        modelsAvailable = Array.from(s_modelToDeployment.keys()).join(', ');
        throw new Error(
            `Model '${modelId}' not available on ${this.endpoint}. ` +
                `Available models: ${modelsAvailable}. Deploy the model and restart the application.`
        );
    }

    /**
     * Caches the list of deployments in Azure OpenAI.
     */
    protected async cacheDeployments(): Promise<void> {
        const url = `${this.endpoint}/openai/deployments?api-version=${this._azureOpenAIApiVersion}`;
        const response = await this.httpClient?.get<IAzureOpenAIDeployment>(url);
        if (response?.status && response.status >= 400) {
            throw new Error(
                `Unable to fetch the list of model deployments from Azure. Status code: ${response.status}`
            );
        }

        if (!response?.data || !Array.isArray(response.data) || response.data.length == 0) {
            throw new Error('Model not available. Unable to fetch the list of models.');
        }

        try {
            for (const deployment of response.data) {
                if (deployment.status != 'succeeded' || !deployment.model || !deployment.id) {
                    continue;
                }

                s_deploymentToModel.set(`${this.endpoint}:${deployment.id}`, deployment.model);
                s_modelToDeployment.set(`${this.endpoint}:${deployment.model}`, deployment.id);
            }
        } catch (err) {
            throw new Error(`Model not available. Unable to fetch the list of models: ${(err as Error).toString()}`);
        }

        s_deploymentsCached.set(this.endpoint, true);
    }
}
