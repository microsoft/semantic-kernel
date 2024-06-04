// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.audio;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.SpeechGenerationOptions;
import com.azure.ai.openai.models.SpeechGenerationResponseFormat;
import com.azure.ai.openai.models.SpeechVoice;
import com.microsoft.semantickernel.aiservices.openai.OpenAiService;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.services.audio.AudioContent;
import com.microsoft.semantickernel.services.audio.TextToAudioExecutionSettings;
import com.microsoft.semantickernel.services.audio.TextToAudioService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

/**
 * Provides OpenAi implementation of text to audio service.
 */
public class OpenAiTextToAudioService extends OpenAiService implements TextToAudioService {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenAiTextToAudioService.class);

    /**
     * Creates an instance of OpenAi text to audio service.
     *
     * @param client  OpenAI client.
     * @param modelId The model ID.
     */
    public OpenAiTextToAudioService(
        OpenAIAsyncClient client,
        String modelId,
        String deploymentName) {
        super(client, null, modelId, deploymentName);
    }

    @Override
    public Mono<AudioContent> getAudioContentAsync(
        String text,
        TextToAudioExecutionSettings executionSettings) {

        SpeechGenerationOptions options = convertOptions(text, executionSettings);

        return getClient().generateSpeechFromText(getDeploymentName(), options)
            .map(response -> new AudioContent(response.toBytes(), getModelId()));
    }

    private SpeechGenerationOptions convertOptions(
        String text,
        TextToAudioExecutionSettings executionSettings) {
        SpeechGenerationOptions options = new SpeechGenerationOptions(
            text,
            SpeechVoice.fromString(executionSettings.getVoice()));

        options.setModel(getModelId());

        if (executionSettings.getResponseFormat() != null) {
            options.setResponseFormat(
                SpeechGenerationResponseFormat.fromString(executionSettings.getResponseFormat()));
        }

        if (executionSettings.getSpeed() != null) {
            options.setSpeed(executionSettings.getSpeed());
        }

        return options;
    }

    /**
     * Creates a new builder.
     *
     * @return The builder.
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * Represents a builder for OpenAi text to audio service.
     */

    public static class Builder extends TextToAudioService.Builder {

        /**
         * Builds the OpenAi text to audio service.
         *
         * @return The OpenAi text to audio service.
         */
        @Override
        public TextToAudioService build() {
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

            return new OpenAiTextToAudioService(client, modelId, deploymentName);
        }
    }
}
