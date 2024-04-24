package com.microsoft.semantickernel.aiservices.google.chatcompletion;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.Content;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.generativeai.ContentMaker;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseStream;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.google.VertexAIService;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.services.gemini.GeminiServiceBuilder;
import com.microsoft.semantickernel.services.openai.OpenAiServiceBuilder;
import reactor.core.publisher.Mono;

import javax.annotation.Nullable;
import java.io.IOException;
import java.util.List;

public class VertexAIChatCompletion extends VertexAIService implements ChatCompletionService {

    public VertexAIChatCompletion(VertexAI client, String modelId) {
        super(client, modelId);
    }

    public static Builder builder() {
        return new Builder();
    }
    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(ChatHistory chatHistory, @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        GenerationConfig generationConfig =
                GenerationConfig.newBuilder()
                        .setMaxOutputTokens(8192)
                        .setTemperature(1F)
                        .setTopP(0.95F)
                        .build();

        GenerativeModel model =
                new GenerativeModel.Builder()
                        .setModelName("gemini-1.5-pro-preview-0409")
                        .setVertexAi(getClient())
                        .setGenerationConfig(generationConfig)
                        .build();

        Content content = ContentMaker.fromMultiModalData("Recommend me 3 books");

        try {
            GenerateContentResponse response = model.generateContent(content);
            System.out.println("");
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        return null;
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(String prompt, @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        return null;
    }

    public static class Builder extends GeminiServiceBuilder<VertexAIChatCompletion, Builder> {
        public VertexAIChatCompletion build() {
            if (this.client == null) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                        "VertexAI client must be provided");
            }

            if (this.modelId == null || modelId.isEmpty()) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                        "Gemini model id must be provided");
            }

            return new VertexAIChatCompletion(client, modelId);
        }
    }
}
