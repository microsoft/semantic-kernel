package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import java.util.List;
import java.util.Map;
import java.util.Objects;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.azure.core.credential.TokenCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.chatcompletion.StreamingChatMessageContent;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class OpenAIChatCompletion implements com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion {
    
    private final OpenAIAsyncClient client;
    private final String modelId;

    public OpenAIChatCompletion(OpenAIAsyncClient client, String modelId) {
        this.client = client;
        this.modelId = modelId;
    }

    @Override
    public Map<String, ContextVariable<?>> getAttributes() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getAttributes'");
    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(ChatHistory chatHistory,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getChatMessageContentsAsync'");
    }

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(ChatHistory chatHistory,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getStreamingChatMessageContentsAsync'");
    }

      @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(String prompt,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getStreamingChatMessageContentsAsync'");
    }

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(String prompt,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getStreamingChatMessageContentsAsync'");
    }

    public static class Builder implements com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder {
            
        private OpenAIAsyncClient client;
        private String modelId;
        private String apiKey;
        private String organization;
        private TokenCredential tokenCredential;

        @Override
        public OpenAIChatCompletion build() {
            OpenAIAsyncClient asyncClient;
            if ((asyncClient = this.client) == null) {
                if (tokenCredential != null) {
                    asyncClient = new OpenAIClientBuilder()
                        .credential(tokenCredential)
                        .buildAsyncClient();
                } else {
                    Objects.requireNonNull(apiKey, "API key must be set");
                    asyncClient = new OpenAIClientBuilder()
                        .credential(new KeyCredential(apiKey))
                        .buildAsyncClient();
                }   
            }
            Objects.requireNonNull(modelId, "Model ID must be set");
            return new OpenAIChatCompletion(asyncClient, modelId);
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withOpenAIAsyncClient(
                OpenAIAsyncClient openAIClient) {
            this.client = openAIClient;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withApiKey(String apiKey) {
            this.apiKey = apiKey;
            return this;

        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withOrganization(
                String organization) {
            this.organization = organization;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withTokenCredential(
                TokenCredential tokenCredential) {
            this.tokenCredential = tokenCredential;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withModelId(
                String modelId) {
            this.modelId = modelId;
            return this;
        }
    }
}
