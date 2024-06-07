// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google.textcompletion;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.google.GeminiService;
import com.microsoft.semantickernel.aiservices.google.implementation.MonoConverter;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.exceptions.SKCheckedException;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.services.gemini.GeminiServiceBuilder;
import com.microsoft.semantickernel.services.textcompletion.StreamingTextContent;
import com.microsoft.semantickernel.services.textcompletion.TextContent;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.Nullable;
import java.io.IOException;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class GeminiTextGenerationService extends GeminiService implements TextGenerationService {
    private static final Logger LOGGER = LoggerFactory.getLogger(GeminiTextGenerationService.class);

    public GeminiTextGenerationService(VertexAI client, String modelId) {
        super(client, modelId);
    }

    public static Builder builder() {
        return new Builder();
    }

    @Override
    public Mono<List<TextContent>> getTextContentsAsync(
        String prompt,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable Kernel kernel) {
        return this.internalGetTextAsync(prompt, executionSettings);
    }

    @Override
    public Flux<StreamingTextContent> getStreamingTextContentsAsync(
        String prompt,
        @Nullable PromptExecutionSettings executionSettings,
        @Nullable Kernel kernel) {
        return this
            .internalGetTextAsync(prompt, executionSettings)
            .flatMapMany(it -> Flux.fromStream(it.stream())
                .map(StreamingTextContent::new));
    }

    private Mono<List<TextContent>> internalGetTextAsync(String prompt,
        @Nullable PromptExecutionSettings executionSettings) {

        try {
            GenerativeModel model = getGenerativeModel(executionSettings);
            return MonoConverter.fromApiFuture(model.generateContentAsync(prompt))
                .doOnError(e -> LOGGER.error("Error generating text", e))
                .flatMap(result -> {
                    List<TextContent> textContents = new ArrayList<>();

                    FunctionResultMetadata<GenerateContentResponse.UsageMetadata> metadata = FunctionResultMetadata
                        .build(
                            UUID.randomUUID().toString(),
                            result.getUsageMetadata(),
                            OffsetDateTime.now());

                    result.getCandidatesList().forEach(
                        candidate -> {
                            candidate.getContent().getPartsList().forEach(part -> {
                                if (!part.getText().isEmpty()) {
                                    textContents.add(
                                        new TextContent(part.getText(), getModelId(), metadata));
                                }
                            });
                        });

                    return Mono.just(textContents);
                });
        } catch (SKCheckedException | IOException e) {
            return Mono.error(new SKException("Error generating text", e));
        }
    }

    private GenerativeModel getGenerativeModel(
        @Nullable PromptExecutionSettings executionSettings) throws SKCheckedException {
        GenerativeModel.Builder modelBuilder = new GenerativeModel.Builder()
            .setModelName(getModelId())
            .setVertexAi(getClient());

        if (executionSettings != null) {
            if (executionSettings.getResultsPerPrompt() < 1
                || executionSettings.getResultsPerPrompt() > MAX_RESULTS_PER_PROMPT) {
                throw SKCheckedException.build("Error building generative model.",
                    new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                        String.format(
                            "Results per prompt must be in range between 1 and %d, inclusive.",
                            MAX_RESULTS_PER_PROMPT)));
            }

            GenerationConfig config = GenerationConfig.newBuilder()
                .setMaxOutputTokens(executionSettings.getMaxTokens())
                .setTemperature((float) executionSettings.getTemperature())
                .setTopP((float) executionSettings.getTopP())
                .setCandidateCount(executionSettings.getResultsPerPrompt())
                .build();

            modelBuilder.setGenerationConfig(config);
        }

        return modelBuilder.build();
    }

    public static class Builder extends
        GeminiServiceBuilder<GeminiTextGenerationService, GeminiTextGenerationService.Builder> {
        @Override
        public GeminiTextGenerationService build() {
            if (this.client == null) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "VertexAI client must be provided");
            }

            if (this.modelId == null || modelId.isEmpty()) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "Gemini model id must be provided");
            }

            return new GeminiTextGenerationService(client, modelId);
        }
    }
}
