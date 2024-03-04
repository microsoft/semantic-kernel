// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import java.nio.charset.Charset;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nullable;

public class OpenAIChatMessageContent<T> extends ChatMessageContent<T> {

    @Nullable
    private final List<OpenAIFunctionToolCall> toolCall;

    public OpenAIChatMessageContent(AuthorRole authorRole, String content, @Nullable String modelId,
        @Nullable T innerContent, @Nullable Charset encoding,
        @Nullable FunctionResultMetadata metadata) {
        super(authorRole, content, modelId, innerContent, encoding, metadata);
        toolCall = null;
    }

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

    @Nullable
    public List<OpenAIFunctionToolCall> getToolCall() {
        return toolCall;
    }
}
