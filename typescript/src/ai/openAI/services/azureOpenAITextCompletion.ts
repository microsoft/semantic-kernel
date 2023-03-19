// Copyright (c) Microsoft. All rights reserved.

import { ILogger } from '../../../utils/logger';
import { Verify } from '../../../utils/verify';
import { ICompleteRequestSettings } from '../../completeRequestSettings';
import { ITextCompletionClient } from '../../iTextCompletionClient';
import { AzureOpenAIClientAbstract } from '../clients/AzureOpenAIClientAbstract';
import { IAzureOpenAICompletionRequest } from '../httpSchema';

/**
 * Azure OpenAI text completion client.
 */
export class AzureOpenAITextCompletion extends AzureOpenAIClientAbstract implements ITextCompletionClient {
    // Model ID
    private readonly _modelId: string;

    /**
     * Creates a new {@link AzureOpenAITextCompletion} client instance.
     *
     * @param modelId Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
     * @param endpoint Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiKey Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
     * @param apiVersion Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
     * @param log Application logger
     */
    public constructor(modelId: string, endpoint: string, apiKey: string, apiVersion: string, log: ILogger) {
        super(log);

        Verify.notEmpty(modelId, 'The ID cannot be empty, you must provide a Model ID or a Deployment name.');
        Verify.notEmpty(endpoint, 'The Azure endpoint cannot be empty');
        Verify.startsWith(endpoint, 'https://', "The Azure OpenAI endpoint must start with 'https://'");
        Verify.notEmpty(apiKey, 'The Azure API key cannot be empty');

        this._modelId = modelId;
        this.endpoint = endpoint;
        if (this.httpClient) {
            this.httpClient.defaults.headers.common['api-key'] = apiKey;
        }
        this.azureOpenAIApiVersion = apiVersion;
    }

    /**
     * Creates a new completion for the prompt and settings.
     *
     * @param text The prompt to complete.
     * @param requestSettings Request settings for the completion API
     * @param cancellationToken Cancellation token
     * @returns The completed text
     */
    public async complete(
        text: string,
        requestSettings: ICompleteRequestSettings,
        _cancellationToken: unknown
    ): Promise<string> {
        if (!requestSettings) {
            throw new Error('Completion settings cannot be empty');
        }

        const deploymentName = await this.getDeploymentName(this._modelId);
        const url = `${this.endpoint}/openai/deployments/${deploymentName}/completions?api-version=${this.azureOpenAIApiVersion}`;

        this.log.debug(`Sending Azure OpenAI completion request to ${url}`);

        if (requestSettings.maxTokens < 1) {
            throw new Error(`MaxTokens ${requestSettings.maxTokens} is not valid, the value must be greater than zero`);
        }

        const request: IAzureOpenAICompletionRequest = {
            prompt: text,
            temperature: requestSettings.temperature,
            top_p: requestSettings.topP,
            presence_penalty: requestSettings.presencePenalty,
            frequency_penalty: requestSettings.frequencyPenalty,
            max_tokens: requestSettings.maxTokens,
            stop:
                Array.isArray(requestSettings.stopSequences) && requestSettings.stopSequences.length > 0
                    ? requestSettings.stopSequences
                    : undefined,
        };
        const requestBody = JSON.stringify(request);

        return this.executeCompleteRequest(url, requestBody);
    }
}
