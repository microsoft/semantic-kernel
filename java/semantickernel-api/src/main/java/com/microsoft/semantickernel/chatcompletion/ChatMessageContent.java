// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.microsoft.semantickernel.KernelContent;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;

import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.annotation.Nullable;

/**
 * Represents the content of a chat message
 */
public class ChatMessageContent extends KernelContent<ChatMessageContent> {

    private AuthorRole authorRole;
    @Nullable
    private String content;
    @Nullable
    private List<KernelContent<?>> items;
    @Nullable
    private Charset encoding;

    /**
     * Creates a new instance of the {@link ChatMessageContent} class.
     * @param authorRole the author role that generated the content
     * @param content the content
     */
    public ChatMessageContent(
        AuthorRole authorRole,
        String content) {
        this(
            authorRole,
            content,
            null,
            null,
            null,
            null);
    }

    /**
     * Creates a new instance of the {@link ChatMessageContent} class.
     * @param authorRole the author role that generated the content
     * @param content the content
     * @param modelId the model id
     * @param innerContent the inner content
     * @param encoding the encoding
     * @param metadata the metadata
     */
    public ChatMessageContent(
        AuthorRole authorRole,
        String content,
        @Nullable String modelId,
        @Nullable String innerContent,
        @Nullable Charset encoding,
        @Nullable FunctionResultMetadata metadata) {
        super(innerContent, modelId, metadata);
        this.authorRole = authorRole;
        this.content = content;
        this.encoding = encoding != null ? encoding : StandardCharsets.UTF_8;
    }

    /**
     * Creates a new instance of the {@link ChatMessageContent} class.
     * @param authorRole the author role that generated the content
     * @param items the items
     * @param modelId the model id
     * @param innerContent the inner content
     * @param encoding the encoding
     * @param metadata the metadata
     */
    public ChatMessageContent(
        AuthorRole authorRole,
        List<KernelContent<?>> items,
        String modelId,
        String innerContent,
        Charset encoding,
        FunctionResultMetadata metadata) {
        super(innerContent, modelId, metadata);
        this.content = null;
        this.authorRole = authorRole;
        this.encoding = encoding != null ? encoding : StandardCharsets.UTF_8;
        this.items = new ArrayList<>(items);
    }

    /**
     * Gets the author role that generated the content
     * @return the author role that generated the content
     */
    public AuthorRole getAuthorRole() {
        return authorRole;
    }

    /**
     * Sets the author role that generated the content
     * @param authorRole the author role that generated the content
     */
    public void setAuthorRole(AuthorRole authorRole) {
        this.authorRole = authorRole;
    }

    /**
     * Gets the content
     * @return the content, which may be {@code null}
     */
    @Nullable
    @Override
    public String getContent() {
        return content;
    }

    /**
     * Sets the content
     * @param content the content
     */
    public void setContent(@Nullable String content) {
        this.content = content;
    }

    /**
     * Gets the {@code KernelContent} items that comprise the content.
     * @return the items, which may be {@code null}
     */
    public List<KernelContent<?>> getItems() {
        return Collections.unmodifiableList(items);
    }

    /**
     * Sets the {@code KernelContent} items that comprise the content.
     * @param items the items
     */
    public void setItems(List<KernelContent<?>> items) {
        this.items = new ArrayList<>(items);
    }

    /**
     * Gets the encoding of the content
     * @return the encoding, which may be {@code null}
     */
    @Nullable
    public Charset getEncoding() {
        return encoding;
    }

    /**
     * Sets the encoding of the content
     * @param encoding the encoding
     */
    public void setEncoding(Charset encoding) {
        this.encoding = encoding;
    }

    @Override
    public String toString() {
        return content != null ? content : "";
    }
}
