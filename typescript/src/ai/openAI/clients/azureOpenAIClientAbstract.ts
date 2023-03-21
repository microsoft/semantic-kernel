/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger } from '../../../utils/logger';
import { IAzureDeployments } from '../httpSchema';
import { OpenAIClientAbstract } from './openAIClientAbstract';

export abstract class AzureOpenAIClientAbstract extends OpenAIClientAbstract {
    // Default Azure OpenAI REST API version
    protected static readonly DefaultAzureAPIVersion = '2022-12-01';

    // Azure endpoint of your models
    protected azureOpenAIApiVersion: string;

    // Azure endpoint of your models
    protected endpoint: string = '';

    constructor(log?: ILogger) {
        super(log);
        this.azureOpenAIApiVersion = AzureOpenAIClientAbstract.DefaultAzureAPIVersion;
    }

    protected async getDeploymentNameAsync(modelId: string): Promise<string | undefined> {
        const fullModelId = `${this.endpoint}:${modelId}`;

        // If the value is a deployment name
        if (s_deploymentToModel.has(fullModelId)) {
            return modelId;
        }

        // If the value is a model ID present in the cache
        if (s_modelToDeployment.has(fullModelId)) {
            return s_modelToDeployment.get(fullModelId);
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

        await this.cacheDeploymentsAsync();

        if (s_modelToDeployment.has(fullModelId)) {
            return s_modelToDeployment.get(fullModelId);
        }

        modelsAvailable = Array.from(s_modelToDeployment.keys()).join(', ');
        throw new Error(
            `Model '${modelId}' not available on ${this.endpoint}. ` +
                `Available models: ${modelsAvailable}. Deploy the model and restart the application.`
        );
    }

    protected async cacheDeploymentsAsync(): Promise<void> {
        const url = `${this.endpoint}/openai/deployments?api-version=${this.azureOpenAIApiVersion}`;
        const response = await this.httpClient.get<IAzureDeployments>(url);
        if (response.status >= 400) {
            throw new Error(
                `Unable to fetch the list of model deployments from Azure. Status code: ${response.status}`
            );
        }

        if (!response.data || !Array.isArray(response.data.data) || response.data.data.length == 0) {
            throw new Error('Model not available. Unable to fetch the list of models.');
        }

        try {
            for (const deployment of response.data.data) {
                if (deployment.status != 'succeeded' || !deployment.model || !deployment.id) {
                    continue;
                }

                s_deploymentToModel.set(`${this.endpoint}:${deployment.id}`, deployment.model);
                s_modelToDeployment.set(`${this.endpoint}:${deployment.model}`, deployment.id);
            }
        } catch (err: any) {
            throw new Error(`Model not available. Unable to fetch the list of models: ${(err as Error).toString()}`);
        }

        s_deploymentsCached.set(this.endpoint, true);
    }
}

// Caching Azure details across multiple instances so we don't have to use "deployment names"
const s_deploymentsCached = new Map<string, boolean>();
const s_deploymentToModel = new Map<string, string>();
const s_modelToDeployment = new Map<string, string>();
