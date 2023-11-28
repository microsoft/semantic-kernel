// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import javax.annotation.Nullable;

/** Request settings for an AI request. */
public class AIRequestSettings {

    /**
     * Service identifier. This identifies a service and is set when the AI service is registered.
     */
    @JsonProperty("service_id")
    @Nullable
    private final String serviceId;

    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    @JsonProperty("model_id")
    @Nullable
    private final String modelId;

    @JsonCreator
    public AIRequestSettings(
            @JsonProperty("service_id") @Nullable String serviceId,
            @JsonProperty("model_id") @Nullable String modelId) {
        this.serviceId = serviceId;
        this.modelId = modelId;
    }

    @Nullable
    public String getServiceId() {
        return serviceId;
    }

    @Nullable
    public String getModelId() {
        return modelId;
    }
}
