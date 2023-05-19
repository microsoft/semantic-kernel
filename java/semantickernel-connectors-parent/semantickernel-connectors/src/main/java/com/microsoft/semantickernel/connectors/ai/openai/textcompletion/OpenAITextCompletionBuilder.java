// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textcompletion;

import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

public class OpenAITextCompletionBuilder implements TextCompletion.Builder {
    @Override
    public TextCompletion build(OpenAIAsyncClient client, String modelId) {
        return new OpenAITextCompletion(client, modelId);
    }
}
