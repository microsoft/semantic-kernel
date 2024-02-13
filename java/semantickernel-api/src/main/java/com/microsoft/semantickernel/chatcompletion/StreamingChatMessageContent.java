// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.microsoft.semantickernel.StreamingKernelContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import javax.annotation.Nullable;

public class StreamingChatMessageContent<T> extends StreamingKernelContent<T> {

    private final String content;
    private final AuthorRole role;
    private Charset encoding;

    public StreamingChatMessageContent(
        AuthorRole role,
        String content,
        @Nullable
        String modelId) {
        this(role, content, null, 0, modelId, null, null);
    }

    public StreamingChatMessageContent(
        AuthorRole role,
        String content,
        @Nullable
        T innerContent,
        int choiceIndex,
        @Nullable
        String modelId,
        @Nullable
        Charset encoding,
        @Nullable
        Map<String, ContextVariable<?>> metadata) {
        super(innerContent, choiceIndex, modelId, metadata);
        this.role = role;
        this.content = content;
        this.encoding = encoding != null ? encoding : StandardCharsets.UTF_8;
    }

    @Override
    public String toString() {
        return content != null ? content : "";
    }

    public String getContent() {
        return content;
    }

    public AuthorRole getRole() {
        return role;
    }

    public Charset getEncoding() {
        return encoding;
    }

    public StreamingChatMessageContent<T> setEncoding(Charset encoding) {
        this.encoding = encoding;
        return this;
    }
}

