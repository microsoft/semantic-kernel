// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.azuresdk;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.ai.AIException;

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

    protected static void validateMaxTokens(int maxTokens) {
        if (maxTokens < 1) {
            throw new AIException(
                    AIException.ErrorCodes.InvalidRequest,
                    "MaxTokens "
                            + maxTokens
                            + " is not valid, the value must be greater than zero");
        }
    }
}
