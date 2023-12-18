package com.microsoft.semantickernel.aiservices.azureopenai.chatcompletion;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.azure.core.credential.TokenCredential;
import com.azure.core.http.HttpClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.chatcompletion.StreamingChatMessageContent;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class AzureOpenAIChatCompletion implements com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion {
    
    private final OpenAIAsyncClient client;
    private final String modelId;
    private final Map<String, ContextVariable<?>> attributes;

    public AzureOpenAIChatCompletion(OpenAIAsyncClient client, String modelId) {
        this.client = client;
        this.modelId = modelId;
        this.attributes = new HashMap<>();
    }
    
    @Override
    public ChatHistory createNewChat(String instructions) {
        ChatHistory chatHistory = new ChatHistory(instructions);
        return chatHistory;
    }

    @Override
    public ChatHistory createNewChat() {
        ChatHistory chatHistory = new ChatHistory();
        return chatHistory;
    }

    @Override
    public Map<String, ContextVariable<?>> getAttributes() {
        return attributes;
    }

    @Override
    public Mono<List<ChatMessageContent>> getChatMessageContentsAsync(ChatHistory chatHistory,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        kernel.invokeAsync(function, arguments, resultType)
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
        throw new UnsupportedOperationException("Unimplemented method 'getChatMessageContentsAsync'");
    }

    @Override
    public Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(String prompt,
            PromptExecutionSettings promptExecutionSettings, Kernel kernel) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getStreamingChatMessageContentsAsync'");
    }

    public static class Builder implements com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion.Builder {
        
        private OpenAIAsyncClient client;
        private String modelId;
        private String apiKey;
        private String endpoint;
        private TokenCredential tokenCredential;

        @Override
        public AzureOpenAIChatCompletion build() {
            
            OpenAIAsyncClient asyncClient;
            if ((asyncClient = this.client) == null) {
                if (tokenCredential != null) {
                    Objects.requireNonNull(endpoint, "Endpoint must be set");
                    asyncClient = new OpenAIClientBuilder()
                        .credential(tokenCredential)
                        .endpoint(endpoint)
                        .buildAsyncClient();
                } else {
                    Objects.requireNonNull(apiKey, "API key must be set");
                    Objects.requireNonNull(endpoint, "Endpoint must be set");
                    asyncClient = new OpenAIClientBuilder()
                        .credential(new KeyCredential(apiKey))
                        .endpoint(endpoint)
                        .buildAsyncClient();
                }   
            }
            Objects.requireNonNull(modelId, "Model ID must be set");
            return new AzureOpenAIChatCompletion(asyncClient, modelId);
            
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion.Builder withModelId(
                String modelId) {
            this.modelId = modelId;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion.Builder withOpenAIAsyncClient(
                OpenAIAsyncClient openAIClient) {
            this.client = openAIClient;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion.Builder withApiKey(
                String apiKey) {
            this.apiKey = apiKey;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion.Builder withEndpoint(
                String endpoint) {
            this.endpoint = endpoint;
            return this;
        }

        @Override
        public com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion.Builder withTokenCredential(
                TokenCredential tokenCredential) {
            this.tokenCredential = tokenCredential;
            return this;
        }
    }
}
