package com.microsoft.semantickernel.aiservices.gemini.chatcompletion;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.Content;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.api.Part;
import com.google.cloud.vertexai.api.Tool;
import com.google.cloud.vertexai.generativeai.ContentMaker;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.gemini.implementation.GeminiRole;
import com.microsoft.semantickernel.aiservices.gemini.VertexAIService;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.services.gemini.GeminiServiceBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

import javax.annotation.Nullable;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class VertexAIChatCompletion extends VertexAIService implements ChatCompletionService {

    private static final Logger LOGGER = LoggerFactory.getLogger(VertexAIChatCompletion.class);

    public VertexAIChatCompletion(VertexAI client, String modelId) {
        super(client, modelId);
    }

    public static Builder builder() {
        return new Builder();
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(ChatHistory chatHistory, @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        return internalChatMessageContentsAsync(getContents(chatHistory), kernel, invocationContext);
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(String prompt, @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        return null;
    }

    private Mono<List<ChatMessageContent<?>>> internalChatMessageContentsAsync(List<Content> contents, @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        GenerativeModel model = getGenerativeModel(kernel, invocationContext);

        try {
            GenerateContentResponse response = model.generateContent(contents);
            return Mono.just(getChatMessageContentsFromResponse(response));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private List<Content> getContents(ChatHistory chatHistory) {
        List<Content> contents = new ArrayList<>();
        chatHistory.forEach(chatMessageContent -> {
            if (chatMessageContent.getAuthorRole() == AuthorRole.USER) {
                contents.add(ContentMaker.forRole(GeminiRole.USER.toString()).fromMultiModalData(chatMessageContent.getContent()));
            } else if (chatMessageContent.getAuthorRole() == AuthorRole.ASSISTANT) {
                contents.add(ContentMaker.forRole(GeminiRole.MODEL.toString()).fromMultiModalData(chatMessageContent.getContent()));
            } else if (chatMessageContent.getAuthorRole() == AuthorRole.TOOL) {
                contents.add(ContentMaker.forRole(GeminiRole.FUNCTION.toString()).fromMultiModalData(chatMessageContent.getContent()));
            }
        });

        return contents;
    }

    private GenerativeModel getGenerativeModel(@Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        GenerativeModel.Builder modelBuilder = new GenerativeModel.Builder()
                .setModelName(getModelId())
                .setVertexAi(getClient());

        if (invocationContext != null) {
            if (invocationContext.getPromptExecutionSettings() != null) {
                PromptExecutionSettings settings = invocationContext.getPromptExecutionSettings();

                GenerationConfig config = GenerationConfig.newBuilder()
                        .setMaxOutputTokens(settings.getMaxTokens())
                        .setTemperature((float) settings.getTemperature())
                        .setTopP((float) settings.getTopP())
                        .build();

                modelBuilder.setGenerationConfig(config);
            }

            if (invocationContext.getToolCallBehavior() != null) {
                ToolCallBehavior toolCallBehavior = invocationContext.getToolCallBehavior();

                Tool.Builder tool = Tool.newBuilder();

                // TODO: Add tool call
            }
        }

        return modelBuilder.build();
    }

    private List<ChatMessageContent<?>> getChatMessageContentsFromResponse(GenerateContentResponse response) {
        List<ChatMessageContent<?>> chatMessageContents = new ArrayList<>();

        response.getCandidatesList().forEach(
                candidate -> {
                    chatMessageContents.add(new ChatMessageContent<>(
                            AuthorRole.ASSISTANT,
                            candidate.getContent().getPartsList().stream().map(Part::getText).reduce("", String::concat)));
                }
        );

        return chatMessageContents;
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
