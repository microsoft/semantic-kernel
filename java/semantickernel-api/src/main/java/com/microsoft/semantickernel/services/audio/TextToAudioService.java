// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.audio;

import com.microsoft.semantickernel.implementation.ServiceLoadUtil;
import com.microsoft.semantickernel.services.AIService;
import com.microsoft.semantickernel.services.openai.OpenAiServiceBuilder;
import reactor.core.publisher.Mono;

/**
 * Provides audio to text service.
 */
public interface TextToAudioService extends AIService {

    /**
     * Get audio content from text.
     *
     * @param sampleText        The sample text.
     * @param executionSettings The AI execution settings.
     * @return Audio content from text.
     */
    Mono<AudioContent> getAudioContentAsync(String sampleText,
        TextToAudioExecutionSettings executionSettings);

    /**
     * Gets the builder for the TextToAudioService.
     *
     * @return The builder.
     */
    static Builder builder() {
        return ServiceLoadUtil.findServiceLoader(Builder.class,
            "com.microsoft.semantickernel.aiservices.openai.audio.OpenAiTextToAudioService$Builder")
            .get();
    }

    /**
     * Builder for the TextToAudioService.
     */
    abstract class Builder extends
        OpenAiServiceBuilder<TextToAudioService, Builder> {

    }
}
