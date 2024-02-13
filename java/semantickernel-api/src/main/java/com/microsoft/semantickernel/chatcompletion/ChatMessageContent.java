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

public class ChatMessageContent extends KernelContent<ChatMessageContent> {

    private AuthorRole authorRole;
    @Nullable
    private String content;
    @Nullable
    private List<KernelContent> items;
    @Nullable
    private Charset encoding;

    public ChatMessageContent(
        AuthorRole authorRole,
        String content
    ) {
        this(
            authorRole,
            content,
            null,
            null,
            null,
            null);
    }

    public ChatMessageContent(
        AuthorRole authorRole,
        String content,
        @Nullable
        String modelId,
        @Nullable
        String innerContent,
        @Nullable
        Charset encoding,
        @Nullable
        FunctionResultMetadata metadata
    ) {
        super(innerContent, modelId, metadata);
        this.authorRole = authorRole;
        this.content = content;
        this.encoding = encoding != null ? encoding : StandardCharsets.UTF_8;
    }

    public ChatMessageContent(
        AuthorRole authorRole,
        List<KernelContent<?>> items,
        String modelId,
        String innerContent,
        Charset encoding,
        FunctionResultMetadata metadata
    ) {
        super(innerContent, modelId, metadata);
        this.content = null;
        this.authorRole = authorRole;
        this.encoding = encoding != null ? encoding : StandardCharsets.UTF_8;
        this.items = new ArrayList<>(items);
    }

    public AuthorRole getAuthorRole() {
        return authorRole;
    }

    public void setAuthorRole(AuthorRole authorRole) {
        this.authorRole = authorRole;
    }

    @Nullable
    @Override
    public String getContent() {
        return content;
    }

    public void setContent(@Nullable String content) {
        this.content = content;
    }

    public List<KernelContent> getItems() {
        return Collections.unmodifiableList(items);
    }

    public void setItems(List<KernelContent> items) {
        this.items = new ArrayList<>(items);
    }

    @Nullable
    public Charset getEncoding() {
        return encoding;
    }

    public void setEncoding(Charset encoding) {
        this.encoding = encoding;
    }

    @Override
    public String toString() {
        return content != null ? content : "";
    }
}
