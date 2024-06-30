// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.audio;

import com.microsoft.semantickernel.implementation.ServiceLoadUtil;
import com.microsoft.semantickernel.services.AIService;
import com.microsoft.semantickernel.services.openai.OpenAiServiceBuilder;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Provides audio to text service.
 */
public interface AudioToTextService extends AIService {

    /**
     * Get text contents from audio content.
     *
     * @param content           Audio content.
     * @param executionSettings The AI execution settings (optional).
     * @return Text contents from audio content.
     */
    Mono<String> getTextContentsAsync(
        AudioContent content,
        @Nullable AudioToTextExecutionSettings executionSettings);

    static Builder builder() {
        return ServiceLoadUtil.findServiceLoader(Builder.class,
            "com.microsoft.semantickernel.aiservices.openai.audio.OpenAiAudioToTextService$Builder")
            .get();
    }

    /**
     * Builder for the AudioToTextService.
     */
    abstract class Builder extends OpenAiServiceBuilder<AudioToTextService, Builder> {

    }
}
