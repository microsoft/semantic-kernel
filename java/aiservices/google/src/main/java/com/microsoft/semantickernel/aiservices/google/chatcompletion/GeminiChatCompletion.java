// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google.chatcompletion;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.Content;
import com.google.cloud.vertexai.api.FunctionDeclaration;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.api.Part;
import com.google.cloud.vertexai.api.Schema;
import com.google.cloud.vertexai.api.Tool;
import com.google.cloud.vertexai.api.Type;
import com.google.cloud.vertexai.generativeai.ContentMaker;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.google.implementation.GeminiRole;
import com.microsoft.semantickernel.aiservices.google.GeminiService;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
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

public class GeminiChatCompletion extends GeminiService implements ChatCompletionService {

    private static final Logger LOGGER = LoggerFactory.getLogger(GeminiChatCompletion.class);

    public GeminiChatCompletion(VertexAI client, String modelId) {
        super(client, modelId);
    }

    /**
     * Create a new instance of {@link GeminiChatCompletion.Builder}.
     *
     * @return a new instance of {@link GeminiChatCompletion.Builder}
     */
    public static Builder builder() {
        return new Builder();
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(ChatHistory chatHistory,
        @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        return internalChatMessageContentsAsync(getContents(chatHistory), kernel,
            invocationContext);
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(String prompt,
        @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        GeminiXMLPromptParser.GeminiParsedPrompt parsedPrompt = GeminiXMLPromptParser.parse(prompt);

        return this.getChatMessageContentsAsync(parsedPrompt.getChatHistory(), kernel,
            invocationContext);
    }

    private Mono<List<ChatMessageContent<?>>> internalChatMessageContentsAsync(
        List<Content> contents, @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext) {
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
                contents.add(ContentMaker.forRole(GeminiRole.USER.toString())
                    .fromMultiModalData(chatMessageContent.getContent()));
            } else if (chatMessageContent.getAuthorRole() == AuthorRole.ASSISTANT) {
                contents.add(ContentMaker.forRole(GeminiRole.MODEL.toString())
                    .fromMultiModalData(chatMessageContent.getContent()));
            } else if (chatMessageContent.getAuthorRole() == AuthorRole.TOOL) {
                contents.add(ContentMaker.forRole(GeminiRole.FUNCTION.toString())
                    .fromMultiModalData(chatMessageContent.getContent()));
            }
        });

        return contents;
    }

    private GenerativeModel getGenerativeModel(@Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext) {
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
                if (kernel != null) {
                    Tool.Builder tool = Tool.newBuilder();

                    kernel.getPlugins()
                        .forEach(plugin -> plugin.getFunctions().forEach((name, function) -> {
                            FunctionDeclaration.Builder functionBuilder = FunctionDeclaration
                                .newBuilder();
                            functionBuilder.setName(ToolCallBehavior
                                .formFullFunctionName(function.getPluginName(), name));
                            functionBuilder.setDescription(function.getDescription());

                            List<InputVariable> parameters = function.getMetadata().getParameters();
                            if (parameters != null && !parameters.isEmpty()) {
                                Schema.Builder parametersBuilder = Schema.newBuilder();

                                function.getMetadata().getParameters().forEach(parameter -> {
                                    parametersBuilder.setDescription(parameter.getDescription());
                                    parametersBuilder.setType(Type.OBJECT);
                                });

                                functionBuilder.setParameters(parametersBuilder.build());
                            }

                            tool.addFunctionDeclarations(functionBuilder.build());
                        }));

                    List<Tool> tools = new ArrayList<>();
                    tools.add(tool.build());

                    modelBuilder.setTools(tools);
                }
            }
        }

        return modelBuilder.build();
    }

    private List<ChatMessageContent<?>> getChatMessageContentsFromResponse(
        GenerateContentResponse response) {
        List<ChatMessageContent<?>> chatMessageContents = new ArrayList<>();

        response.getCandidatesList().forEach(
            candidate -> {
                chatMessageContents.add(new ChatMessageContent<>(
                    AuthorRole.ASSISTANT,
                    candidate.getContent().getPartsList().stream().map(Part::getText).reduce("",
                        String::concat)));
            });

        return chatMessageContents;
    }

    public static class Builder extends GeminiServiceBuilder<GeminiChatCompletion, Builder> {
        public GeminiChatCompletion build() {
            if (this.client == null) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "VertexAI client must be provided");
            }

            if (this.modelId == null || modelId.isEmpty()) {
                throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                    "Gemini model id must be provided");
            }

            return new GeminiChatCompletion(client, modelId);
        }
    }
}
