// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google;

import com.google.cloud.vertexai.VertexAI;
import com.microsoft.semantickernel.services.AIService;

import javax.annotation.Nullable;

public class GeminiService implements AIService {
    private final VertexAI client;
    private final String modelId;

    protected GeminiService(VertexAI client, String modelId) {
        this.client = client;
        this.modelId = modelId;
    }

    @Nullable
    @Override
    public String getModelId() {
        return modelId;
    }

    @Nullable
    @Override
    public String getServiceId() {
        return null;
    }

    protected VertexAI getClient() {
        return client;
    }
}
