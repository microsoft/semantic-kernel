// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.audio;

import javax.annotation.Nullable;

/**
 * Represents audio content.
 */
public class AudioToTextExecutionSettings {

    @Nullable
    private final String deploymentName;

    @Nullable
    private final String filename;

    private final String responseFormat;

    @Nullable
    private final String language;

    @Nullable
    private final String prompt;

    @Nullable
    private final Double temperature;

    /**
     * Creates an instance of audio to text execution settings.
     *
     * @param deploymentName The deployment name.
     * @param filename       The filename.
     * @param responseFormat The response format.
     * @param language       The language.
     * @param prompt         The prompt.
     * @param temperature    The temperature.
     */
    public AudioToTextExecutionSettings(
        @Nullable String deploymentName,
        @Nullable String filename,
        String responseFormat,
        @Nullable String language,
        @Nullable String prompt,
        @Nullable Double temperature) {
        this.deploymentName = deploymentName;
        this.filename = filename;
        this.responseFormat = responseFormat;
        this.language = language;
        this.prompt = prompt;
        this.temperature = temperature;
    }

    /**
     * The deployment name to use for audio transcription.
     * <p>
     * When making a request against Azure OpenAI, this should be the customizable name of the
     * "model deployment" (example: my-gpt4-deployment) and not the name of the model itself
     * (example: gpt-4).
     * <p>
     * When using non-Azure OpenAI, this corresponds to "model" in the request options and should
     * use the appropriate name of the model (example: gpt-4).
     *
     * @return The deployment name.
     */
    @Nullable
    public String getDeploymentName() {
        return deploymentName;
    }

    /**
     * The optional filename or descriptive identifier to associate with the audio data.
     *
     * @return The filename or descriptive identifier.
     */
    @Nullable
    public String getFilename() {
        return filename;
    }

    /**
     * The requested format of the transcription response data, which will influence the content and
     * detail of the result.
     *
     * @return The response format.
     */
    public String getResponseFormat() {
        return responseFormat;
    }

    /**
     * The language of the audio data as two-letter ISO-639-1 language code (e.g. 'en' or 'es').
     *
     * @return The language of the audio data.
     */
    @Nullable
    public String getLanguage() {
        return language;
    }

    /**
     * An optional hint to guide the model's style or continue from a prior audio segment. The
     * written language of the prompt should match the primary spoken language of the audio data.
     *
     * @return The prompt.
     */
    @Nullable
    public String getPrompt() {
        return prompt;
    }

    /**
     * The randomness of the generated text. Select a value from 0.0 to 1.0. 0 is the default.
     *
     * @return The temperature.
     */
    @Nullable
    public Double getTemperature() {
        return temperature;
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
     * Represents a builder for audio to text execution settings.
     */
    public static class Builder {

        @Nullable
        private String deploymentName = null;
        @Nullable
        private String filename = null;
        @Nullable
        private String responseFormat = null;
        @Nullable
        private String language = null;
        @Nullable
        private String prompt = null;
        @Nullable
        private Double temperature = null;

        /**
         * Sets the deployment name to use for audio transcription.
         *
         * @param deploymentName The deployment name.
         * @return The builder.
         */
        public Builder withDeploymentName(String deploymentName) {
            this.deploymentName = deploymentName;
            return this;
        }

        /**
         * Sets the filename or descriptive identifier to associate with the audio data.
         *
         * @param filename The filename or descriptive identifier.
         * @return The builder.
         */
        public Builder withFilename(String filename) {
            this.filename = filename;
            return this;
        }

        /**
         * The requested format of the transcription response data, which will influence the content
         * and detail of the result.
         *
         * @param responseFormat The response format. Supported formats are json, text, srt,
         *                       verbose_json, or vtt. Default is 'json'.
         * @return The builder.
         */
        public Builder withResponseFormat(String responseFormat) {
            this.responseFormat = responseFormat;
            return this;
        }

        /**
         * The language of the audio data as two-letter ISO-639-1 language code (e.g. 'en' or
         * 'es').
         *
         * @param language The language of the audio data.
         * @return The builder.
         */
        public Builder withLanguage(String language) {
            this.language = language;
            return this;
        }

        /**
         * An optional hint to guide the model's style or continue from a prior audio segment. The
         * written language of the prompt should match the primary spoken language of the audio
         * data.
         *
         * @param prompt The prompt.
         * @return The builder.
         */
        public Builder withPrompt(String prompt) {
            this.prompt = prompt;
            return this;
        }

        /**
         * The randomness of the generated text. Select a value from 0.0 to 1.0. 0 is the default.
         *
         * @param temperature The temperature.
         * @return The builder.
         */
        public Builder withTemperature(Double temperature) {
            this.temperature = temperature;
            return this;
        }

        /**
         * Builds the audio to text execution settings.
         *
         * @return The audio to text execution settings.
         */
        public AudioToTextExecutionSettings build() {
            if (responseFormat == null) {
                responseFormat = "json";
            }

            return new AudioToTextExecutionSettings(deploymentName, filename,
                responseFormat, language, prompt, temperature);
        }
    }
}
