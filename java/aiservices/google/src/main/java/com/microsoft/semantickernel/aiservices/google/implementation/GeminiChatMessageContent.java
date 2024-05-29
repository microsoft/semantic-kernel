package com.microsoft.semantickernel.aiservices.google.implementation;

import com.google.cloud.vertexai.api.FunctionCall;
import com.google.cloud.vertexai.api.FunctionResponse;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.nio.charset.Charset;
import java.util.Collections;
import java.util.List;

/**
 * Represents the content of a chat message.
 *
 * @param <T> The type of the inner content.
 */
public class GeminiChatMessageContent<T> extends ChatMessageContent<T> {

    @Nonnull
    private final List<FunctionCall> functionCalls;
    @Nonnull
    private final List<FunctionResponse> functionResponses;

    /**
     * Creates a new instance of the {@link GeminiChatMessageContent} class.
     *
     * @param authorRole        The author role that generated the content.
     * @param content           The content.
     * @param modelId           The model id.
     * @param innerContent      The inner content.
     * @param encoding          The encoding.
     * @param metadata          The metadata.
     * @param functionCalls     The function calls.
     * @param functionResponses The function responses.
     */
    public GeminiChatMessageContent(
            AuthorRole authorRole,
            String content,
            @Nullable String modelId,
            @Nullable T innerContent,
            @Nullable Charset encoding,
            @Nullable FunctionResultMetadata metadata,
            @Nullable List<FunctionCall> functionCalls,
            @Nullable List<FunctionResponse> functionResponses) {
        super(authorRole, content, modelId, innerContent, encoding, metadata);
        if (functionCalls == null) {
            this.functionCalls = Collections.emptyList();
        } else {
            this.functionCalls = Collections.unmodifiableList(functionCalls);
        }
        if (functionResponses == null) {
            this.functionResponses = Collections.emptyList();
        } else {
            this.functionResponses = Collections.unmodifiableList(functionResponses);
        }
    }

    /**
     * Gets the function calls.
     *
     * @return The function calls.
     */
    @Nonnull
    public List<FunctionCall> getFunctionCalls() {
        return functionCalls;
    }

    /**
     * Gets the function responses.
     *
     * @return The function responses.
     */
    @Nonnull
    public List<FunctionResponse> getFunctionResponses() {
        return functionResponses;
    }
}
