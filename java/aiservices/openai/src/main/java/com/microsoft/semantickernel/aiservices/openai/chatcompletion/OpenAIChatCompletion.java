package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import java.util.List;
import java.util.Map;
import java.util.Objects;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.azure.core.credential.TokenCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
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

    public OpenAIChatCompletion(TokenCredential tokenCredential, String modelId, String endpoint) {
        this.modelId = modelId;
        this.client = new OpenAIClientBuilder()
            .credential(tokenCredential)
            .endpoint(endpoint)
            .buildAsyncClient();   
    }

    public OpenAIChatCompletion(String modelId, String apiKey, String endpoint, String organization) {
        this.modelId = modelId;
        this.client = new OpenAIClientBuilder()
            .credential(new KeyCredential(apiKey))
            .endpoint(endpoint)
            .buildAsyncClient();
    }
    
    @Override
    public ChatHistory createNewChat(String instructions) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'createNewChat'");
    }

    @Override
    public ChatHistory createNewChat() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'createNewChat'");
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
        throw new UnsupportedOperationException("Unimplemented method 'getChatMessageContentsAsync'");
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
                Objects.requireNonNull(client, "OpenAI client must be set");
                Objects.requireNonNull(modelId, "Model ID must be set");
                return new OpenAIChatCompletion(client, modelId);
            }

            @Override
            public com.microsoft.semantickernel.chatcompletion.ChatCompletionService.Builder withOpenAIAsyncClient(
                    OpenAIAsyncClient openAIClient) {
                // TODO Auto-generated method stub
                throw new UnsupportedOperationException("Unimplemented method 'withOpenAIClient'");
            }

            @Override
            public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withApiKey(String apiKey) {
                // TODO Auto-generated method stub
                throw new UnsupportedOperationException("Unimplemented method 'withApiKey'");
            }

            @Override
            public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withOrganization(
                    String organization) {
                // TODO Auto-generated method stub
                throw new UnsupportedOperationException("Unimplemented method 'withOrganization'");
            }

            @Override
            public com.microsoft.semantickernel.chatcompletion.OpenAIChatCompletion.Builder withTokenCredential(
                    TokenCredential tokenCredential) {
                // TODO Auto-generated method stub
                throw new UnsupportedOperationException("Unimplemented method 'withTokenCredential'");
            }

            @Override
            public com.microsoft.semantickernel.chatcompletion.ChatCompletionService.Builder withModelId(
                    String modelId) {
                // TODO Auto-generated method stub
                throw new UnsupportedOperationException("Unimplemented method 'withModelId'");
            }
    }
}
