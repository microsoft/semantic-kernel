// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.huggingface.services;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.huggingface.HuggingFaceClient;
import com.microsoft.semantickernel.aiservices.huggingface.models.TextGenerationRequest;
import com.microsoft.semantickernel.aiservices.huggingface.models.TextGenerationRequest.HuggingFaceTextOptions;
import com.microsoft.semantickernel.aiservices.huggingface.models.TextGenerationRequest.HuggingFaceTextParameters;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.services.textcompletion.StreamingTextContent;
import com.microsoft.semantickernel.services.textcompletion.TextContent;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class HuggingFaceTextGenerationService implements TextGenerationService {

    private final String modelId;
    private final String serviceId;
    private final HuggingFaceClient client;

    public HuggingFaceTextGenerationService(
        String modelId,
        String serviceId,
        HuggingFaceClient client) {
        this.modelId = modelId;
        this.serviceId = serviceId;
        this.client = client;
    }

    public Mono<List<TextContent>> getTextContentsAsync(
        String prompt,
        @Nullable HuggingFacePromptExecutionSettings huggingFacePromptExecutionSettings,
        @Nullable Kernel kernel) {

        HuggingFaceTextParameters textParameters = getHuggingFaceTextParameters(
            huggingFacePromptExecutionSettings);

        TextGenerationRequest textGenerationRequest = new TextGenerationRequest(
            prompt,
            false,
            textParameters,
            new HuggingFaceTextOptions());

        return client
            .getTextContentsAsync(modelId, textGenerationRequest)
            .map(result -> result
                .stream()
                .map(item -> new TextContent(
                    item.getGeneratedText() != null ? item.getGeneratedText() : "",
                    modelId,
                    FunctionResultMetadata.build(UUID.randomUUID().toString())))
                .collect(Collectors.toList()));
    }

    @Override
    public Mono<List<TextContent>> getTextContentsAsync(
        String prompt,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable Kernel kernel) {

        HuggingFacePromptExecutionSettings huggingFacePromptExecutionSettings = null;

        if (executionSettings != null) {
            huggingFacePromptExecutionSettings = HuggingFacePromptExecutionSettings
                .fromExecutionSettings(
                    executionSettings);
        }

        return getTextContentsAsync(
            prompt,
            huggingFacePromptExecutionSettings,
            kernel);

    }

    @Override
    public Flux<StreamingTextContent> getStreamingTextContentsAsync(String prompt,
        @Nullable PromptExecutionSettings executionSettings, @Nullable Kernel kernel) {
        throw new SKException("Streaming text content is not supported");
    }

    private static @Nullable HuggingFaceTextParameters getHuggingFaceTextParameters(
        @Nullable HuggingFacePromptExecutionSettings executionSettings) {
        HuggingFaceTextParameters textParameters = null;
        if (executionSettings != null) {
            textParameters = new HuggingFaceTextParameters(
                executionSettings.getTopK(),
                executionSettings.getTopP(),
                executionSettings.getTemperature(),
                executionSettings.getRepetitionPenalty(),
                executionSettings.getMaxTokens(),
                executionSettings.getMaxTime(),
                true,
                executionSettings.getResultsPerPrompt(),
                null,
                executionSettings.getDetails());
        }
        return textParameters;
    }

    @Nullable
    @Override
    public String getModelId() {
        return modelId;
    }

    @Nullable
    @Override
    public String getServiceId() {
        return serviceId;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {

        @Nullable
        protected String modelId;
        @Nullable
        protected HuggingFaceClient client;
        @Nullable
        protected String serviceId;

        /**
         * Sets the model ID for the service
         *
         * @param modelId The model ID
         * @return The builder
         */
        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        /**
         * Sets the service ID for the service
         *
         * @param serviceId The service ID
         * @return The builder
         */
        public Builder withServiceId(String serviceId) {
            this.serviceId = serviceId;
            return this;
        }

        public Builder withHuggingFaceClient(HuggingFaceClient client) {
            this.client = client;
            return this;
        }

        public HuggingFaceTextGenerationService build() {

            if (this.modelId == null) {
                throw new SKException(
                    "Model ID is required to build HuggingFaceTextGenerationService");
            }

            if (this.serviceId == null) {
                throw new SKException(
                    "Service ID is required to build HuggingFaceTextGenerationService");
            }

            if (this.client == null) {
                throw new SKException(
                    "HuggingFaceClient is required to build HuggingFaceTextGenerationService");
            }

            return new HuggingFaceTextGenerationService(
                this.modelId,
                this.serviceId,
                this.client);
        }
    }
}
