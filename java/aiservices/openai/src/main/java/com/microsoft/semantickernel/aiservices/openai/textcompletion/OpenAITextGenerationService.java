package com.microsoft.semantickernel.aiservices.openai.textcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.CompletionsOptions;
import com.azure.ai.openai.models.CompletionsUsage;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.OpenAIRequestSettings;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.exceptions.AIException.ErrorCodes;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.services.textcompletion.StreamingTextContent;
import com.microsoft.semantickernel.services.textcompletion.TextContent;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;
import java.time.OffsetDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class OpenAITextGenerationService implements TextGenerationService {

    private final OpenAIAsyncClient client;
    @Nullable
    private final String serviceId;
    private final String modelId;

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
        String modelId,
        @Nullable String serviceId) {
        this.serviceId = serviceId;
        this.client = client;
        this.modelId = modelId;
    }

    public static Builder builder() {
        return new Builder();
    }

    @Override
    @Nullable
    public String getServiceId() {
        return serviceId;
    }

    @Override
    public Mono<List<TextContent>> getTextContentsAsync(
        String prompt,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable Kernel kernel) {
        return this.internalCompleteTextAsync(prompt, executionSettings);
    }

    @Override
    public Flux<StreamingTextContent> getStreamingTextContentsAsync(
        String prompt,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable Kernel kernel) {
        return this
            .internalCompleteTextAsync(prompt, executionSettings)
            .flatMapMany(it -> Flux.fromStream(it.stream())
                .map(StreamingTextContent::new));
    }

    protected Mono<List<TextContent>> internalCompleteTextAsync(
        String text,
        @Nullable PromptExecutionSettings requestSettings) {

        CompletionsOptions completionsOptions = getCompletionsOptions(text, requestSettings);

        return client
            .getCompletionsWithResponse(getModelId(), completionsOptions,
                OpenAIRequestSettings.getRequestOptions())
            .flatMap(completionsResult -> {
                if (completionsResult.getStatusCode() >= 400) {
                    return Mono.error(new AIException(ErrorCodes.SERVICE_ERROR,
                        "Request failed: " + completionsResult.getStatusCode()));
                }
                return Mono.just(completionsResult.getValue());
            })
            .map(completions -> {
                FunctionResultMetadata metadata = FunctionResultMetadata.build(
                    completions.getId(),
                    completions.getUsage(),
                    completions.getCreatedAt());

                return completions
                    .getChoices()
                    .stream()
                    .map(choice -> {
                        return new TextContent(
                            choice.getText(),
                            completionsOptions.getModel(),
                            metadata);
                    })
                    .collect(Collectors.toList());
            });
    }

    public static Map<String, ContextVariable<?>> buildMetadata(
        String id,
        CompletionsUsage usage,
        OffsetDateTime createdAt) {

        Map<String, ContextVariable<?>> metadata = new HashMap<>();
        metadata.put("id", ContextVariable.of(id));
        metadata.put("usage", ContextVariable.of(usage));
        metadata.put("created_at", ContextVariable.of(createdAt));

        return metadata;
    }

    private CompletionsOptions getCompletionsOptions(
        String text,
        @Nullable PromptExecutionSettings requestSettings) {
        if (requestSettings == null) {
            return new CompletionsOptions(Collections.singletonList(text))
                .setMaxTokens(PromptExecutionSettings.DEFAULT_MAX_TOKENS);
        }
        if (requestSettings.getMaxTokens() < 1) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST, "Max tokens must be >0");
        }
        if (requestSettings.getResultsPerPrompt() < 1
            || requestSettings.getResultsPerPrompt() > MAX_RESULTS_PER_PROMPT) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                String.format("Results per prompt must be in range between 1 and %d, inclusive.",
                    MAX_RESULTS_PER_PROMPT));
        }

        CompletionsOptions options = new CompletionsOptions(Collections.singletonList(text))
            .setMaxTokens(requestSettings.getMaxTokens())
            .setTemperature(requestSettings.getTemperature())
            .setTopP(requestSettings.getTopP())
            .setFrequencyPenalty(requestSettings.getFrequencyPenalty())
            .setPresencePenalty(requestSettings.getPresencePenalty())
            .setModel(getModelId())
            .setN(requestSettings.getResultsPerPrompt())
            .setUser(requestSettings.getUser())
            .setBestOf(requestSettings.getBestOf())
            .setLogitBias(new HashMap<>());
        return options;
    }

    @Nullable
    @Override
    public String getModelId() {
        return modelId;
    }

    /**
     * Builder for a TextGenerationService
     */
    public static class Builder extends TextGenerationService.Builder {

        @Override
        public TextGenerationService build() {

            if (this.client == null) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "OpenAI client must be provided");
            }
            if (this.modelId == null) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "OpenAI model id must be provided");
            }

            return new OpenAITextGenerationService(
                this.client,
                this.modelId,
                this.serviceId);
        }
    }
}
