// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.audio;

import com.microsoft.semantickernel.exceptions.SKException;
import java.util.Arrays;
import java.util.Map;
import javax.annotation.Nullable;

/**
 * Represents audio content.
 */
public class AudioContent {

    private final byte[] data;
    @Nullable
    private final String modelId;

    /**
     * Creates an instance of audio content.
     *
     * @param data    The audio data.
     * @param modelId The model ID.
     */
    public AudioContent(byte[] data, @Nullable String modelId) {
        this.data = Arrays.copyOf(data, data.length);
        this.modelId = modelId;
    }

    /**
     * Gets the audio data.
     *
     * @return The audio data.
     */
    public byte[] getData() {
        return Arrays.copyOf(data, data.length);
    }

    /**
     * Gets the model ID.
     *
     * @return The model ID.
     */
    @Nullable
    public String getModelId() {
        return modelId;
    }

    /**
     * Gets the inner content.
     *
     * @return The inner content.
     */
    @Nullable
    public String getInnerContent() {
        return null;
    }

    /**
     * Gets the metadata.
     *
     * @return The metadata.
     */
    @Nullable
    public Map<String, Object> getMetadata() {
        return null;
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
     * Represents a builder for audio content.
     */
    public static class Builder {

        @Nullable
        private byte[] data = null;
        @Nullable
        private String modelId = null;

        /**
         * Sets the audio data.
         *
         * @param data The audio data.
         * @return The builder.
         */
        public Builder withData(byte[] data) {
            this.data = Arrays.copyOf(data, data.length);
            return this;
        }

        /**
         * Sets the model ID.
         *
         * @param modelId The model ID.
         * @return The builder.
         */
        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        /**
         * Builds the audio content.
         *
         * @return The audio content.
         */
        public AudioContent build() {
            if (data == null) {
                throw new SKException("Data is required");
            }

            if (modelId == null) {
                throw new SKException("Model ID is required");
            }

            return new AudioContent(data, modelId);
        }
    }
}
