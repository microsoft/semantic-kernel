// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.microsoft.semantickernel.KernelContent;
import com.microsoft.semantickernel.StreamingKernelContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Map;

import javax.annotation.Nullable;

/**
 * Represents the content of a chat message that is streamed.
 * @param <T> the type of the inner content
 */
public class StreamingChatMessageContent<T extends KernelContent<T>> extends StreamingKernelContent<T> {

    private final String content;
    private final AuthorRole role;
    private Charset encoding;

    /**
     * Creates a new instance of the {@link StreamingChatMessageContent} class.
     * @param role the author role that generated the content
     * @param content the content
     * @param modelId the model id
     */
    public StreamingChatMessageContent(
        AuthorRole role,
        String content,
        @Nullable
        String modelId) {
        this(role, content, null, 0, modelId, null, null);
    }

    /**
     * Creates a new instance of the {@link StreamingChatMessageContent} class.
     * @param role the author role that generated the content
     * @param content the content
     * @param innerContent the inner content
     * @param choiceIndex the choice index
     * @param modelId the model id
     * @param encoding the encoding
     * @param metadata the metadata
     */
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

    @Override
    public String getContent() {
        return content;
    }

    /**
     * Gets the role of the author of the message
     * @return the role of the author of the message
     */
    public AuthorRole getRole() {
        return role;
    }

    /**
     * Gets the encoding of the message
     * @return the encoding of the message
     */
    public Charset getEncoding() {
        return encoding;
    }

    /**
     * Sets the encoding of the message
     * @param encoding the encoding of the message
     * @return this instance
     */
    public StreamingChatMessageContent<T> setEncoding(Charset encoding) {
        this.encoding = encoding;
        return this;
    }
}

