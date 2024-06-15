// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.chatcompletion;

import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.services.KernelContent;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nullable;

/**
 * Represents the content of a chat message
 *
 * @param <T> the type of the inner content within the messages
 */
public class ChatMessageContent<T> extends KernelContent<T> {

    private final AuthorRole authorRole;
    @Nullable
    private final String content;
    @Nullable
    private final List<KernelContent<T>> items;
    @Nullable
    private final Charset encoding;

    /**
     * Creates a new instance of the {@link ChatMessageContent} class.
     *
     * @param authorRole the author role that generated the content
     * @param content    the content
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
     *
     * @param authorRole   the author role that generated the content
     * @param content      the content
     * @param modelId      the model id
     * @param innerContent the inner content
     * @param encoding     the encoding
     * @param metadata     the metadata
     */
    public ChatMessageContent(
        AuthorRole authorRole,
        String content,
        @Nullable String modelId,
        @Nullable T innerContent,
        @Nullable Charset encoding,
        @Nullable FunctionResultMetadata metadata) {
        super(innerContent, modelId, metadata);
        this.authorRole = authorRole;
        this.content = content;
        this.encoding = encoding != null ? encoding : StandardCharsets.UTF_8;
        this.items = null;
    }

    /**
     * Creates a new instance of the {@link ChatMessageContent} class.
     *
     * @param authorRole   the author role that generated the content
     * @param items        the items
     * @param modelId      the model id
     * @param innerContent the inner content
     * @param encoding     the encoding
     * @param metadata     the metadata
     */
    public ChatMessageContent(
        AuthorRole authorRole,
        List<KernelContent<T>> items,
        String modelId,
        T innerContent,
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
     *
     * @return the author role that generated the content
     */
    public AuthorRole getAuthorRole() {
        return authorRole;
    }

    /**
     * Gets the content
     *
     * @return the content, which may be {@code null}
     */
    @Nullable
    @Override
    public String getContent() {
        return content;
    }

    /**
     * Gets the {@code KernelContent} items that comprise the content.
     *
     * @return the items, which may be {@code null}
     */
    public List<KernelContent<T>> getItems() {
        return Collections.unmodifiableList(items);
    }

    /**
     * Gets the encoding of the content
     *
     * @return the encoding, which may be {@code null}
     */
    @Nullable
    public Charset getEncoding() {
        return encoding;
    }

    @Override
    public String toString() {
        return content != null ? content : "";
    }
}
