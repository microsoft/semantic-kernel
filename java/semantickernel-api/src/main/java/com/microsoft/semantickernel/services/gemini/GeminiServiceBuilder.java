// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.gemini;

import com.google.cloud.vertexai.VertexAI;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import javax.annotation.Nullable;

/**
 * Builder for a Gemini service.
 */
public abstract class GeminiServiceBuilder<T, U extends GeminiServiceBuilder<T, U>> implements
    SemanticKernelBuilder<T> {

    @Nullable
    protected String modelId;
    @Nullable
    protected VertexAI client;

    /**
     * Sets the model ID for the service
     *
     * @param modelId The model ID
     * @return The builder
     */
    public U withModelId(String modelId) {
        this.modelId = modelId;
        return (U) this;
    }

    /**
     * Sets the VertexAI client for the service
     *
     * @param client The VertexAI client
     * @return The builder
     */
    public U withVertexAIClient(VertexAI client) {
        this.client = client;
        return (U) this;
    }

    @Override
    public abstract T build();
}