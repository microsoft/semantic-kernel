// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.Choice;
import com.azure.ai.openai.models.Completions;
import com.azure.ai.openai.models.CompletionsOptions;
import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.connectors.ai.openai.azuresdk.ClientBase;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import jakarta.inject.Inject;

import reactor.core.publisher.Mono;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;

import javax.annotation.Nonnull;

/// <summary>
/// OpenAI text completion service.
/// TODO: forward ETW logging to ILogger, see
// https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public class OpenAITextCompletion extends ClientBase implements TextCompletion {
    /// <summary>
    /// Create an instance of the OpenAI text completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP
    /// requests.</param>
    /// <param name="log">Application logger</param>
    @Inject
    public OpenAITextCompletion(OpenAIAsyncClient client, String modelId) {
        super(client, modelId);
    }

    @Override
    public Mono<List<String>> completeAsync(
            @Nonnull String text, @Nonnull CompletionRequestSettings requestSettings) {
        return this.internalCompleteTextAsync(text, requestSettings);
    }

    protected Mono<List<String>> internalCompleteTextAsync(
            String text, CompletionRequestSettings requestSettings) {
        // TODO

        if (requestSettings.getMaxTokens() < 1) {
            throw new AIException(AIException.ErrorCodes.InvalidRequest, "Max tokens must be >0");
        }

        CompletionsOptions completionsOptions =
                new CompletionsOptions(Collections.singletonList(text))
                        .setMaxTokens(requestSettings.getMaxTokens())
                        .setTemperature(requestSettings.getTemperature())
                        .setTopP(requestSettings.getTopP())
                        .setFrequencyPenalty(requestSettings.getFrequencyPenalty())
                        .setPresencePenalty(requestSettings.getPresencePenalty())
                        .setModel(getModelId())
                        .setUser(requestSettings.getUser())
                        .setBestOf(requestSettings.getBestOf())
                        .setLogitBias(new HashMap<>());

        return getClient()
                .getCompletions(getModelId(), completionsOptions)
                .flatMapIterable(Completions::getChoices)
                .mapNotNull(Choice::getText)
                .collectList();
    }

    public static final class Builder extends TextCompletion.Builder {

        @Override
        public TextCompletion build(OpenAIAsyncClient client, String modelId) {
            return new OpenAITextCompletion(client, modelId);
        }
    }
}
