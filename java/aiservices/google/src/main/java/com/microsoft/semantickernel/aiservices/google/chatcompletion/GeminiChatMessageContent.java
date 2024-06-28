// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google.chatcompletion;

import com.google.cloud.vertexai.api.FunctionCall;
import com.google.cloud.vertexai.api.FunctionResponse;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.nio.charset.Charset;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Represents the content of a chat message.
 *
 * @param <T> The type of the inner content.
 */
public class GeminiChatMessageContent<T> extends ChatMessageContent<T> {
    @Nonnull
    private final List<GeminiFunctionCall> geminiFunctionCalls;

    /**
     * Creates a new instance of the {@link GeminiChatMessageContent} class.
     *
     * @param authorRole        The author role that generated the content.
     * @param content           The content.
     * @param modelId           The model id.
     * @param innerContent      The inner content.
     * @param encoding          The encoding.
     * @param metadata          The metadata.
     * @param geminiFunctionCalls  The function calls.
     */
    public GeminiChatMessageContent(
        AuthorRole authorRole,
        String content,
        @Nullable String modelId,
        @Nullable T innerContent,
        @Nullable Charset encoding,
        @Nullable FunctionResultMetadata metadata,
        @Nullable List<GeminiFunctionCall> geminiFunctionCalls) {
        super(authorRole, content, modelId, innerContent, encoding, metadata);
        if (geminiFunctionCalls == null) {
            this.geminiFunctionCalls = Collections.emptyList();
        } else {
            this.geminiFunctionCalls = Collections.unmodifiableList(geminiFunctionCalls);
        }
    }

    /**
     * Gets the function calls.
     *
     * @return The function calls.
     */
    @Nonnull
    public List<GeminiFunctionCall> getGeminiFunctionCalls() {
        return Collections.unmodifiableList(geminiFunctionCalls);
    }
}
