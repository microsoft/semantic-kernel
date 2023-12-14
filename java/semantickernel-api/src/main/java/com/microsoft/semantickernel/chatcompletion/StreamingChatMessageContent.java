// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.microsoft.semantickernel.StreamingKernelContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public class StreamingChatMessageContent extends StreamingKernelContent {

    private String content;
    private AuthorRole role;
    private Charset encoding;

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

    public void setContent(String content) {
        this.content = content;
    }

    public AuthorRole getRole() {
        return role;
    }

    public void setRole(AuthorRole role) {
        this.role = role;
    }

    public Charset getEncoding() {
        return encoding;
    }

    public void setEncoding(Charset encoding) {
        this.encoding = encoding;
    }
}

