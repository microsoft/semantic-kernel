// Copyright (c) Microsoft Corporation. All rights reserved.

import { Verify } from '../../../utils/verify';
import { ILogger } from '../../../utils/logger';
import { ITextCompletionClient } from '../../iTextCompletionClient';
import { OpenAIClientAbstract } from '../clients/openAIClientAbstract';
import { CompleteRequestSettings } from '../../completeRequestSettings';
import { IOpenAICompletionRequest } from '../httpSchema';

export class OpenAITextCompletion extends OpenAIClientAbstract implements ITextCompletionClient {
    // 3P OpenAI REST API endpoint
    private static readonly openAIEndpoint = 'https://api.openai.com/v1';
    // Model ID
    private readonly _modelId: string;

    /**
     * Creates a new OpenAITextCompletion with supplied values.
     *
     * @constructor
     * @param modelId OpenAI model name, see https://platform.openai.com/docs/models.
     * @param apiKey OpenAI API key, see https://platform.openai.com/account/api-keys.
     * @param organization OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
     * @param log Logger.
     * @param handlerFactory Retry handler.
     */
    public constructor(modelId: string, apiKey: string, organization?: string, log?: ILogger) {
        super(log);

        Verify.notEmpty(modelId, 'The OpenAI model ID cannot be empty');
        Verify.notEmpty(apiKey, 'The OpenAI API key cannot be empty');

        this._modelId = modelId;
        if (this.httpClient) {
            this.httpClient.defaults.headers.common['Authorization'] = `Bearer ${apiKey}`;
            if (organization) {
                this.httpClient.defaults.headers.common['OpenAI-Organization'] = organization;
            }
        }
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
        requestSettings: CompleteRequestSettings,
        _cancellationToken: unknown
    ): Promise<string> {
        if (!requestSettings) {
            throw new Error('Completion settings cannot be empty');
        }

        const url = `${OpenAITextCompletion.openAIEndpoint}/engines/${this._modelId}/completions`;
        this.log.debug(`Sending OpenAI completion request to ${url}`);

        if (requestSettings.maxTokens < 1) {
            throw new Error(`MaxTokens ${requestSettings.maxTokens} is not valid, the value must be greater than zero`);
        }

        const request: IOpenAICompletionRequest = {
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
