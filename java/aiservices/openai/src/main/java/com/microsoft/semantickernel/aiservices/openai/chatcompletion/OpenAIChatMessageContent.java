// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import java.nio.charset.Charset;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nullable;

/**
 * Represents the content of a chat message.
 *
 * @param <T> The type of the inner content.
 */
public class OpenAIChatMessageContent<T> extends ChatMessageContent<T> {

    @Nullable
    private final List<OpenAIFunctionToolCall> toolCall;

    /**
     * Creates a new instance of the {@link OpenAIChatMessageContent} class.
     *
     * @param authorRole   The author role that generated the content.
     * @param content      The content.
     * @param modelId      The model id.
     * @param innerContent The inner content.
     * @param encoding     The encoding.
     * @param metadata     The metadata.
     * @param toolCall     The tool call.
     */
    public OpenAIChatMessageContent(
        AuthorRole authorRole,
        String content,
        @Nullable String modelId,
        @Nullable T innerContent,
        @Nullable Charset encoding,
        @Nullable FunctionResultMetadata metadata,
        @Nullable List<OpenAIFunctionToolCall> toolCall) {
        super(authorRole, content, modelId, innerContent, encoding, metadata);

        if (toolCall == null) {
            this.toolCall = null;
        } else {
            this.toolCall = Collections.unmodifiableList(toolCall);
        }
    }

    /**
     * Gets any tool calls requested.
     *
     * @return The tool call.
     */
    @Nullable
    public List<OpenAIFunctionToolCall> getToolCall() {
        return toolCall;
    }
}
