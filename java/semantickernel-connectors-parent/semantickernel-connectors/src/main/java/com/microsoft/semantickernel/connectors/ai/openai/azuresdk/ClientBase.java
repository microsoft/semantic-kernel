// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.azuresdk;

import com.microsoft.openai.OpenAIAsyncClient;

public abstract class ClientBase {
    private final String modelId;
    private final OpenAIAsyncClient client;

    public ClientBase(OpenAIAsyncClient client, String modelId) {
        this.modelId = modelId;
        this.client = client;
    }

    protected String getModelId() {
        return modelId;
    }

    protected OpenAIAsyncClient getClient() {
        return client;
    }
}
