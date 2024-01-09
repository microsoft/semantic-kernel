package com.microsoft.semantickernel.aiservices.openai.textcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.Choice;
import com.azure.ai.openai.models.Completions;
import com.azure.ai.openai.models.CompletionsOptions;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.textcompletion.StreamingTextContent;
import com.microsoft.semantickernel.textcompletion.TextContent;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class OpenAITextGenerationService implements TextGenerationService {

    private final OpenAIAsyncClient client;
    private final Map<String, ContextVariable<?>> attributes;

    /// <summary>
    /// Creates a new <see cref="OpenAITextGenerationService"/> client instance supporting AAD auth
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextGenerationService(
        OpenAIAsyncClient client,
        String modelId) {
        this.client = client;
        attributes = new HashMap<>();
        attributes.put(MODEL_ID_KEY, ContextVariable.of(modelId));
    }

    public static Builder builder() {
        return new Builder();
    }

    @Override
    public Map<String, ContextVariable<?>> getAttributes() {
        return attributes;
    }

    @Override
    public Mono<List<TextContent>> getTextContentsAsync(String prompt,
        @Nullable PromptExecutionSettings executionSettings, @Nullable Kernel kernel) {
        return null;
    }

    @Override
    public Flux<StreamingTextContent> getStreamingTextContentsAsync(
        String prompt,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable Kernel kernel) {
        return this
            .internalCompleteTextAsync(prompt, executionSettings)
            .flatMapMany(it -> {
                return Flux.fromStream(it.stream())
                    .map(TextContent::new)
                    .map(StreamingTextContent::new);
            });
    }

    protected Mono<List<String>> internalCompleteTextAsync(
        String text,
        PromptExecutionSettings requestSettings) {

        CompletionsOptions completionsOptions = getCompletionsOptions(text, requestSettings);

        return client
            .getCompletions(getModelId(), completionsOptions)
            .flatMapIterable(Completions::getChoices)
            .mapNotNull(Choice::getText)
            .collectList();
    }

    private CompletionsOptions getCompletionsOptions(
        String text, PromptExecutionSettings requestSettings) {
        if (requestSettings == null) {
            return new CompletionsOptions(Collections.singletonList(text))
                .setMaxTokens(PromptExecutionSettings.DEFAULT_MAX_TOKENS);
        }
        if (requestSettings.getMaxTokens() < 1) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST, "Max tokens must be >0");
        }

        CompletionsOptions options =
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
/*
        if (requestSettings instanceof ChatRequestSettings) {
            options = options.setStop(requestSettings.getStopSequences());
        }

 */
        return options;
    }

    /**
     * Builder for a TextGenerationService
     */
    public static class Builder {
        private String modelId;
        private OpenAIAsyncClient client;

        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        public Builder withOpenAIAsyncClient(OpenAIAsyncClient client) {
            this.client = client;
            return this;
        }

        public OpenAITextGenerationService build() {
            return new OpenAITextGenerationService(
                this.client,
                this.modelId
            );
        }
    }
}
