// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.audio;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.AudioTranscription;
import com.azure.ai.openai.models.AudioTranscriptionFormat;
import com.azure.ai.openai.models.AudioTranscriptionOptions;
import com.microsoft.semantickernel.aiservices.openai.OpenAiService;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.services.audio.AudioContent;
import com.microsoft.semantickernel.services.audio.AudioToTextExecutionSettings;
import com.microsoft.semantickernel.services.audio.AudioToTextService;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

/**
 * Provides OpenAi implementation of audio to text service.
 */
public class OpenAiAudioToTextService extends OpenAiService implements AudioToTextService {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenAiAudioToTextService.class);

    /**
     * Creates an instance of OpenAi audio to text service.
     *
     * @param client  OpenAI client.
     * @param modelId The model ID.
     */
    public OpenAiAudioToTextService(
        OpenAIAsyncClient client,
        String modelId,
        String deploymentName) {
        super(client, null, modelId, deploymentName);
    }

    @Override
    public Mono<String> getTextContentsAsync(
        AudioContent content,
        @Nullable AudioToTextExecutionSettings executionSettings) {

        AudioTranscriptionOptions options = convertOptions(content, executionSettings);

        // TODO: Should use getAudioTranscriptionTextWithResponse, and OpenAIRequestSettings.getRequestOptions()
        // however currently this breaks the request
        return getClient()
            .getAudioTranscription(
                getDeploymentName(),
                options.getFilename(),
                options)
            .map(AudioTranscription::getText);
    }

    private AudioTranscriptionOptions convertOptions(
        AudioContent content,
        @Nullable AudioToTextExecutionSettings executionSettings) {
        AudioTranscriptionOptions options = new AudioTranscriptionOptions(content.getData());

        options.setModel(getModelId());
        if (executionSettings == null) {
            return options;
        }

        if (executionSettings.getResponseFormat() != null) {
            options.setResponseFormat(
                AudioTranscriptionFormat.fromString(executionSettings.getResponseFormat()));
        }

        if (executionSettings.getFilename() != null) {
            options.setFilename(executionSettings.getFilename());
        }

        if (executionSettings.getLanguage() != null) {
            options.setLanguage(executionSettings.getLanguage());
        }

        if (executionSettings.getPrompt() != null) {
            options.setPrompt(executionSettings.getPrompt());
        }

        if (executionSettings.getTemperature() != null) {
            options.setTemperature(executionSettings.getTemperature());
        }
        return options;
    }

    /**
     * Builder for OpenAiAudioToTextService.
     *
     * @return The builder.
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * Represents a builder for OpenAiAudioToTextService.
     */
    public static class Builder extends AudioToTextService.Builder {

        /**
         * builds the OpenAiAudioToTextService.
         */
        @Override
        public AudioToTextService build() {
            if (client == null) {
                throw new SKException("OpenAI client is required");
            }

            if (modelId == null) {
                throw new SKException("Model id is required");
            }

            if (deploymentName == null) {
                LOGGER.debug("Deployment name is not provided, using model id as deployment name");
                deploymentName = modelId;
            }

            return new OpenAiAudioToTextService(client, modelId, deploymentName);
        }
    }
}
