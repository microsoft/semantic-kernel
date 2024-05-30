// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.services.AIService;
import javax.annotation.Nullable;

/**
 * Provides OpenAI service.
 */
public abstract class OpenAiService implements AIService {

    private final OpenAIAsyncClient client;
    @Nullable
    private final String serviceId;
    private final String modelId;
    private final String deploymentName;

    protected OpenAiService(
        OpenAIAsyncClient client,
        @Nullable String serviceId,
        String modelId,
        String deploymentName) {
        this.client = client;
        this.serviceId = serviceId;
        this.modelId = modelId;
        this.deploymentName = deploymentName;
    }

    @Nullable
    @Override
    public String getModelId() {
        return modelId;
    }

    @Override
    @Nullable
    public String getServiceId() {
        return serviceId;
    }

    protected OpenAIAsyncClient getClient() {
        return client;
    }

    public String getDeploymentName() {
        return deploymentName;
    }
}
