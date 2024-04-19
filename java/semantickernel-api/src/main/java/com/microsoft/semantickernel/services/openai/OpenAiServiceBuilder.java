// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.openai;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import javax.annotation.Nullable;

/**
 * Builder for an OpenAI service.
 */
public abstract class OpenAiServiceBuilder<T, U extends OpenAiServiceBuilder<T, U>> implements
    SemanticKernelBuilder<T> {

    @Nullable
    protected String modelId;
    @Nullable
    protected OpenAIAsyncClient client;
    @Nullable
    protected String serviceId;

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
     * Sets the OpenAI client for the service
     *
     * @param client The OpenAI client
     * @return The builder
     */
    public U withOpenAIAsyncClient(OpenAIAsyncClient client) {
        this.client = client;
        return (U) this;
    }

    /**
     * Sets the service ID for the service
     *
     * @param serviceId The service ID
     * @return The builder
     */
    public U withServiceId(String serviceId) {
        this.serviceId = serviceId;
        return (U) this;
    }

    @Override
    public abstract T build();

}