// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Spliterator;
import java.util.function.Consumer;

import com.microsoft.semantickernel.orchestration.ContextVariable;

/**
 * Provides a history of messages between the User, Assistant and System
 */
public class ChatHistory implements Iterable<ChatMessageContent> {

    private final List<ChatMessageContent> messages;

    public ChatHistory() {
        this.messages = new ArrayList<>();
    }

    public ChatHistory(List<ChatMessageContent> messages) {
        this.messages = new ArrayList<>(messages);
    }

    /**
     * Get the chat history
     *
     * @return List of messages in the chat
     */
    public List<ChatMessageContent> getMessages() {
        return Collections.unmodifiableList(messages);
    }

    /**
     * Get last message
     *
     * @return The most recent message in chat
     */
    public Optional<ChatMessageContent> getLastMessage() {
        if (messages.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(messages.get(messages.size() - 1));
    }

    public void addAll(ChatHistory value) {
        this.messages.addAll(value.getMessages());
    }

    @Override
    public Iterator<ChatMessageContent> iterator() {
        return messages.iterator();
    }

    @Override
    public void forEach(Consumer<? super ChatMessageContent> action) {
        messages.forEach(action);
    }

    @Override
    public Spliterator<ChatMessageContent> spliterator() {
        return messages.spliterator();
    }

    public void addMessage(AuthorRole authorRole, String content, Charset encoding, Map<String, ContextVariable<?>> metadata) {
        messages.add(new ChatMessageContent(authorRole, content, null, null, encoding, metadata));
    }

    public void addMessage(ChatMessageContent content) {
        messages.add(content);
    }

}
