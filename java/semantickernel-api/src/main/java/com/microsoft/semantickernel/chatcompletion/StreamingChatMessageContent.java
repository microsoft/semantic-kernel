// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Map;

import com.microsoft.semantickernel.StreamingKernelContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

public class StreamingChatMessageContent extends StreamingKernelContent {

    private final String content;
    private final AuthorRole role;
    private Charset encoding;
    private String modelId;

    public StreamingChatMessageContent(
        AuthorRole role,
        String content) {
        this(role, content, null, 0, null, null, null);
    }

    public StreamingChatMessageContent(
        AuthorRole role,
        String content,
        Object innerContent,
        int choiceIndex,
        String modelId,
        Charset encoding,
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

    @Override
    public byte[] toByteArray() {
        return toString().getBytes(encoding);
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

    public StreamingChatMessageContent setEncoding(Charset encoding) {
        this.encoding = encoding;
        return this;
    }

    public StreamingChatMessageContent setModelId(String modelId) {
        this.modelId = modelId;
        return this;
    }

    public String getModelId() {
        return modelId;
    }
}

