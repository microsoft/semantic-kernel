// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.TextAIService;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.builders.ServiceLoadUtil;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

public interface ChatCompletionService extends Buildable, TextAIService {

    Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        ChatHistory chatHistory,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext
    );

    Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        String prompt,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext
    );

    static Builder builder() {
        return ServiceLoadUtil.findServiceLoader(Builder.class,
                "com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion$Builder")
            .get();
    }

    abstract class Builder implements SemanticKernelBuilder<ChatCompletionService> {

        @Nullable
        protected OpenAIAsyncClient client;

        @Nullable
        protected String modelId;

        @Nullable
        protected String serviceId;


        /**
         * Sets the model ID to use with the ChatCompletion service.
         *
         * @param modelId the model ID to use with the ChatCompletion service
         * @return this builder
         */
        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        /**
         * Sets the {@link OpenAIClient} to use for communication with the ChatCompletion service.
         *
         * @param openAIClient the {@link OpenAIClient} to use for communication with the
         *                     ChatCompletion service
         * @return this builder
         */
        public Builder withOpenAIAsyncClient(OpenAIAsyncClient openAIClient) {
            this.client = openAIClient;
            return this;
        }

        public Builder withServiceId(String serviceId) {
            this.serviceId = serviceId;
            return this;
        }
    }

}
