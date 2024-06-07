// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google.chatcompletion;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.Content;
import com.google.cloud.vertexai.api.FunctionCall;
import com.google.cloud.vertexai.api.FunctionDeclaration;
import com.google.cloud.vertexai.api.FunctionResponse;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.api.Part;
import com.google.cloud.vertexai.api.Schema;
import com.google.cloud.vertexai.api.Tool;
import com.google.cloud.vertexai.api.Type;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.google.GeminiService;
import com.microsoft.semantickernel.aiservices.google.implementation.MonoConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.exceptions.AIException;
import com.microsoft.semantickernel.exceptions.SKCheckedException;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.InvocationReturnMode;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.services.gemini.GeminiServiceBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import javax.annotation.Nullable;
import java.io.IOException;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

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
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(String prompt,
        @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        GeminiXMLPromptParser.GeminiParsedPrompt parsedPrompt = GeminiXMLPromptParser.parse(prompt);

        return this.getChatMessageContentsAsync(parsedPrompt.getChatHistory(), kernel,
            invocationContext);
    }

    @Override
    public Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(ChatHistory chatHistory,
        @Nullable Kernel kernel, @Nullable InvocationContext invocationContext) {
        return internalChatMessageContentsAsync(
            new ChatHistory(chatHistory.getMessages()),
            new ChatHistory(),
            kernel,
            invocationContext,
            Math.min(MAXIMUM_INFLIGHT_AUTO_INVOKES,
                invocationContext != null && invocationContext.getToolCallBehavior() != null
                    ? invocationContext.getToolCallBehavior().getMaximumAutoInvokeAttempts()
                    : 0));
    }

    private Mono<List<ChatMessageContent<?>>> internalChatMessageContentsAsync(
        ChatHistory fullHistory, ChatHistory newHistory, @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext, int invocationAttempts) {

        List<Content> contents = getContents(fullHistory);

        try {
            GenerativeModel model = getGenerativeModel(kernel, invocationContext);
            return MonoConverter.fromApiFuture(model.generateContentAsync(contents))
                .doOnError(e -> LOGGER.error("Error generating chat completion", e))
                .flatMap(result -> {
                    // Get ChatMessageContent from the response
                    GeminiChatMessageContent<?> response = getGeminiChatMessageContentFromResponse(
                        result);

                    // Add assistant response to the chat history
                    fullHistory.addMessage(response);
                    newHistory.addMessage(response);

                    // Just return the result:
                    // If we don't want to attempt to invoke any functions or if we have no function calls
                    if (invocationAttempts <= 0 || response.getGeminiFunctionCalls().isEmpty()) {
                        if (invocationContext != null && invocationContext
                            .returnMode() == InvocationReturnMode.FULL_HISTORY) {
                            return Mono.just(fullHistory.getMessages());
                        }
                        if (invocationContext != null && invocationContext
                            .returnMode() == InvocationReturnMode.LAST_MESSAGE_ONLY) {
                            ChatHistory lastMessage = new ChatHistory();
                            lastMessage.addMessage(response);

                            return Mono.just(lastMessage.getMessages());
                        }

                        return Mono.just(newHistory.getMessages());
                    }

                    // Perform the function calls
                    List<Mono<GeminiFunctionCall>> functionResults = response
                        .getGeminiFunctionCalls().stream()
                        .map(geminiFunctionCall -> performFunctionCall(kernel, invocationContext,
                            geminiFunctionCall))
                        .collect(Collectors.toList());

                    Mono<List<GeminiFunctionCall>> combinedResults = Flux
                        .fromIterable(functionResults)
                        .flatMap(mono -> mono)
                        .collectList();

                    // Add the function responses to the chat history
                    return combinedResults.flatMap(results -> {
                        ChatMessageContent<?> functionResponsesMessage = new GeminiChatMessageContent<>(
                            AuthorRole.USER,
                            "", null, null, null, null, results);

                        fullHistory.addMessage(functionResponsesMessage);
                        newHistory.addMessage(functionResponsesMessage);

                        return internalChatMessageContentsAsync(fullHistory, newHistory, kernel,
                            invocationContext, invocationAttempts - 1);
                    });
                });
        } catch (SKCheckedException | IOException e) {
            return Mono.error(new SKException("Error generating chat completion", e));
        }
    }

    // Convert from ChatHistory to List<Content>
    private List<Content> getContents(ChatHistory chatHistory) {
        List<Content> contents = new ArrayList<>();
        chatHistory.forEach(chatMessageContent -> {
            Content.Builder contentBuilder = Content.newBuilder();

            if (chatMessageContent.getAuthorRole() == AuthorRole.USER) {
                contentBuilder.setRole(GeminiRole.USER.toString());

                if (chatMessageContent instanceof GeminiChatMessageContent) {
                    GeminiChatMessageContent<?> message = (GeminiChatMessageContent<?>) chatMessageContent;

                    message.getGeminiFunctionCalls().forEach(geminiFunction -> {
                        FunctionResponse functionResponse = FunctionResponse.newBuilder()
                            .setName(geminiFunction.getFunctionCall().getName())
                            .setResponse(Struct.newBuilder().putFields("result",
                                Value.newBuilder()
                                    .setStringValue(
                                        (String) geminiFunction.getFunctionResult().getResult())
                                    .build()))
                            .build();

                        contentBuilder
                            .addParts(Part.newBuilder().setFunctionResponse(functionResponse));
                    });
                }
            } else if (chatMessageContent.getAuthorRole() == AuthorRole.ASSISTANT) {
                contentBuilder.setRole(GeminiRole.MODEL.toString());

                if (chatMessageContent instanceof GeminiChatMessageContent) {
                    GeminiChatMessageContent<?> message = (GeminiChatMessageContent<?>) chatMessageContent;

                    message.getGeminiFunctionCalls().forEach(geminiFunctionCall -> {
                        contentBuilder.addParts(Part.newBuilder()
                            .setFunctionCall(geminiFunctionCall.getFunctionCall()));
                    });
                }
            }

            if (chatMessageContent.getContent() != null
                && !chatMessageContent.getContent().isEmpty()) {
                contentBuilder.addParts(Part.newBuilder().setText(chatMessageContent.getContent()));
            }

            contents.add(contentBuilder.build());
        });

        return contents;
    }

    private GeminiChatMessageContent<?> getGeminiChatMessageContentFromResponse(
        GenerateContentResponse response) {
        StringBuilder message = new StringBuilder();
        List<GeminiFunctionCall> functionCalls = new ArrayList<>();

        response.getCandidatesList().forEach(
            candidate -> {
                Content content = candidate.getContent();
                if (content.getPartsCount() == 0) {
                    return;
                }

                content.getPartsList().forEach(part -> {
                    if (!part.getFunctionCall().getName().isEmpty()) {
                        // We only care about the function call here
                        // Execution of the function call will be done later
                        functionCalls.add(new GeminiFunctionCall(part.getFunctionCall(), null));
                    }
                    if (!part.getText().isEmpty()) {
                        message.append(part.getText());
                    }
                });
            });

        FunctionResultMetadata<GenerateContentResponse.UsageMetadata> metadata = FunctionResultMetadata
            .build(UUID.randomUUID().toString(), response.getUsageMetadata(), OffsetDateTime.now());

        return new GeminiChatMessageContent<>(AuthorRole.ASSISTANT,
            message.toString(), null, null, null, metadata, functionCalls);
    }

    private GenerativeModel getGenerativeModel(@Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext) throws SKCheckedException {
        GenerativeModel.Builder modelBuilder = new GenerativeModel.Builder()
            .setModelName(getModelId())
            .setVertexAi(getClient());

        if (invocationContext != null) {
            if (invocationContext.getPromptExecutionSettings() != null) {
                PromptExecutionSettings settings = invocationContext.getPromptExecutionSettings();

                if (settings.getResultsPerPrompt() < 1
                    || settings.getResultsPerPrompt() > MAX_RESULTS_PER_PROMPT) {
                    throw SKCheckedException.build("Error building generative model.",
                        new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                            String.format(
                                "Results per prompt must be in range between 1 and %d, inclusive.",
                                MAX_RESULTS_PER_PROMPT)));
                }

                GenerationConfig config = GenerationConfig.newBuilder()
                    .setMaxOutputTokens(settings.getMaxTokens())
                    .setTemperature((float) settings.getTemperature())
                    .setTopP((float) settings.getTopP())
                    .setCandidateCount(settings.getResultsPerPrompt())
                    .build();

                modelBuilder.setGenerationConfig(config);
            }

            if (invocationContext.getToolCallBehavior() != null && kernel != null) {
                List<Tool> tools = new ArrayList<>();
                Tool tool = getTool(kernel, invocationContext.getToolCallBehavior());
                if (tool != null) {
                    tools.add(tool);
                }
                modelBuilder.setTools(tools);
            }
        }

        return modelBuilder.build();
    }

    private FunctionDeclaration buildFunctionDeclaration(KernelFunction<?> function) {
        FunctionDeclaration.Builder functionBuilder = FunctionDeclaration.newBuilder();
        functionBuilder.setName(
            ToolCallBehavior.formFullFunctionName(function.getPluginName(), function.getName()));
        functionBuilder.setDescription(function.getDescription());

        List<InputVariable> parameters = function.getMetadata().getParameters();
        if (parameters != null && !parameters.isEmpty()) {
            Schema.Builder parametersBuilder = Schema.newBuilder();

            function.getMetadata().getParameters().forEach(parameter -> {
                parametersBuilder.setType(Type.OBJECT);
                parametersBuilder.putProperties(
                    parameter.getName(),
                    Schema.newBuilder().setType(Type.STRING)
                        .setDescription(parameter.getDescription()).build());
            });

            functionBuilder.setParameters(parametersBuilder.build());
        }

        return functionBuilder.build();
    }

    @Nullable
    private Tool getTool(@Nullable Kernel kernel, @Nullable ToolCallBehavior toolCallBehavior) {
        if (kernel == null || toolCallBehavior == null) {
            return null;
        }

        Tool.Builder toolBuilder = Tool.newBuilder();

        // If a specific function is required to be called
        if (toolCallBehavior instanceof ToolCallBehavior.RequiredKernelFunction) {
            KernelFunction<?> kernelFunction = ((ToolCallBehavior.RequiredKernelFunction) toolCallBehavior)
                .getRequiredFunction();

            toolBuilder.addFunctionDeclarations(buildFunctionDeclaration(kernelFunction));
        }
        // If a set of functions are enabled to be called
        if (toolCallBehavior instanceof ToolCallBehavior.AllowedKernelFunctions) {
            ToolCallBehavior.AllowedKernelFunctions enabledKernelFunctions = (ToolCallBehavior.AllowedKernelFunctions) toolCallBehavior;

            kernel.getPlugins()
                .forEach(plugin -> plugin.getFunctions().forEach((name, function) -> {
                    // check if all kernel functions are enabled or if the specific function is enabled
                    if (enabledKernelFunctions.isAllKernelFunctionsAllowed() ||
                        enabledKernelFunctions.isFunctionAllowed(function.getPluginName(),
                            function.getName())) {
                        toolBuilder.addFunctionDeclarations(buildFunctionDeclaration(function));
                    }
                }));
        }

        return toolBuilder.build();
    }

    public Mono<GeminiFunctionCall> performFunctionCall(@Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext, GeminiFunctionCall geminiFunction) {
        if (kernel == null) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                "Kernel must be provided to perform function call");
        }

        String[] name = geminiFunction.getFunctionCall().getName()
            .split(ToolCallBehavior.FUNCTION_NAME_SEPARATOR);

        String pluginName = name[0];
        String functionName = name[1];

        KernelFunction<?> function = kernel.getPlugin(pluginName).get(functionName);

        if (function == null) {
            throw new AIException(AIException.ErrorCodes.INVALID_REQUEST,
                String.format("Kernel function %s not found in plugin %s", functionName,
                    pluginName));
        }

        ContextVariableTypes contextVariableTypes = invocationContext == null
            ? new ContextVariableTypes()
            : invocationContext.getContextVariableTypes();

        KernelFunctionArguments.Builder arguments = KernelFunctionArguments.builder();
        geminiFunction.getFunctionCall().getArgs().getFieldsMap().forEach((key, value) -> {
            arguments.withVariable(key, value.getStringValue());
        });

        return function
            .invokeAsync(kernel)
            .withArguments(arguments.build())
            .withResultType(contextVariableTypes.getVariableTypeForClass(String.class))
            .map(result -> new GeminiFunctionCall(geminiFunction.getFunctionCall(), result));
    }

    public static class Builder extends GeminiServiceBuilder<GeminiChatCompletion, Builder> {
        @Override
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
