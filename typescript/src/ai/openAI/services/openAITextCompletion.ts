/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Verify } from '../../../diagnostics';
import { ILogger } from '../../../utils/logger';
import { CompleteRequestSettings } from '../../completeRequestSettings';
import { ITextCompletionClient } from '../../iTextCompletionClient';
import { OpenAIClientAbstract } from '../clients';

export class OpenAITextCompletion extends OpenAIClientAbstract implements ITextCompletionClient {
    // 3P OpenAI REST API endpoint
    private static readonly OpenaiEndpoint = 'https://api.openai.com/v1';

    private readonly _modelId: string;

    constructor(modelId: string, apiKey: string, organization?: string, log?: ILogger) {
        super(log);

        Verify.notEmpty(modelId, 'The OpenAI model ID cannot be empty');
        this._modelId = modelId;

        Verify.notEmpty(apiKey, 'The OpenAI API key cannot be empty');
        this.httpClient.defaults.headers.Authorization = `Bearer ${apiKey}`;

        if (organization !== undefined && organization !== null && organization !== '') {
            this.HTTPClient.defaults.headers['OpenAI-Organization'] = organization;
        }
    }

    public async completeAsync(text: string, requestSettings: CompleteRequestSettings): Promise<string> {
        Verify.notNull(requestSettings, 'Completion settings cannot be empty');

        const url = `${OpenAITextCompletion.OpenaiEndpoint}/engines/${this._modelId}/completions`;
        this.Log.logDebug(`Sending OpenAI completion request to ${url}`);

        if (requestSettings.MaxTokens < 1) {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                `MaxTokens ${requestSettings.MaxTokens} is not valid, the value must be greater than zero`
            );
        }

        const requestBody = JSON.stringify(
            new OpenAICompletionRequest({
                Prompt: text,
                Temperature: requestSettings.Temperature,
                TopP: requestSettings.TopP,
                PresencePenalty: requestSettings.PresencePenalty,
                FrequencyPenalty: requestSettings.FrequencyPenalty,
                MaxTokens: requestSettings.MaxTokens,
                Stop: requestSettings.StopSequences?.length > 0 ? requestSettings.StopSequences : null,
            })
        );

        return this.executeCompleteRequestAsync(url, requestBody);
    }

    // Use this URL if you prefer passing the model ID in the request payload
    // private static readonly OPENAI_COMPLETION_ENDPOINT = `${OpenAITextCompletion.OpenaiEndpoint}/completions`;
    // public async complete(text: string, requestSettings: CompleteRequestSettings): Promise<string> {
    //     Verify.notNull(requestSettings, "Completion settings cannot be empty");
    //
    //     this.Log.logDebug(`Sending OpenAI completion request to ${OpenAITextCompletion.OPENAI_COMPLETION_ENDPOINT}`);
    //
    //     const requestBody = JSON.stringify(new OpenAICompletionRequest({
    //         Model: this._modelId, // Set this only if using OPENAI_COMPLETION_ENDPOINT
    //         Prompt: text,
    //         Temperature: requestSettings.Temperature,
    //         TopP: requestSettings.TopP,
    //         PresencePenalty: requestSettings.PresencePenalty,
    //         FrequencyPenalty: requestSettings.FrequencyPenalty,
    //         MaxTokens: requestSettings.MaxTokens,
    //         Stop: requestSettings.StopSequences?.length > 0 ? requestSettings.StopSequences : null,
    //     }));
    //
    //     return this.executeCompleteRequest(OpenAITextCompletion.OPENAI_COMPLETION_ENDPOINT, requestBody);
    // }
}
