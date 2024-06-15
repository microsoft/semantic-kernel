// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.audio;

import com.microsoft.semantickernel.exceptions.SKException;
import edu.umd.cs.findbugs.annotations.Nullable;

/**
 * Represents the settings for text to audio execution.
 */
public class TextToAudioExecutionSettings {

    private final String voice;
    private final String responseFormat;
    @Nullable
    private final Double speed;

    /**
     * Creates a new instance of the settings.
     *
     * @param voice          The voice.
     * @param responseFormat The response format.
     * @param speed          The speed.
     */
    public TextToAudioExecutionSettings(
        String voice,
        String responseFormat,
        @Nullable Double speed) {
        this.voice = voice;
        this.responseFormat = responseFormat;
        this.speed = speed;
    }

    /**
     * Gets the voice.
     *
     * @return The voice.
     */
    public String getVoice() {
        return voice;
    }

    /**
     * Gets the response format.
     *
     * @return The response format.
     */
    public String getResponseFormat() {
        return responseFormat;
    }

    /**
     * Gets the speed.
     *
     * @return The speed.
     */
    @Nullable
    public Double getSpeed() {
        return speed;
    }

    /**
     * Creates a new builder.
     *
     * @return The builder.
     */
    public static TextToAudioExecutionSettings.Builder builder() {
        return new Builder();
    }

    /**
     * Represents a builder for text to audio execution settings.
     */
    public static class Builder {

        @Nullable
        private String voice = null;
        @Nullable
        private String responseFormat = null;
        @Nullable
        private Double speed = null;

        /**
         * Sets the voice to use for the audio generation.
         *
         * @param voice The voice.
         * @return The builder.
         */
        public Builder withVoice(String voice) {
            this.voice = voice;
            return this;
        }

        /**
         * Sets the response format, e.g "mp3", "opus", "aac", "flak"
         *
         * @param responseFormat The response format.
         * @return The builder.
         */
        public Builder withResponseFormat(String responseFormat) {
            this.responseFormat = responseFormat;
            return this;
        }

        /**
         * Sets the speed of the audio generation.
         *
         * @param speed The speed.
         * @return The builder.
         */
        public Builder withSpeed(Double speed) {
            this.speed = speed;
            return this;
        }

        /**
         * Builds the settings.
         *
         * @return The settings.
         */
        public TextToAudioExecutionSettings build() {
            if (voice == null) {
                throw new SKException("Voice must be set");
            }
            if (responseFormat == null) {
                throw new SKException("Response format must be set");
            }
            return new TextToAudioExecutionSettings(voice, responseFormat, speed);
        }
    }

}
