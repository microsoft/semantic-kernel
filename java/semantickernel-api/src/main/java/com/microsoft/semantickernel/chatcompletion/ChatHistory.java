// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Optional;
import java.util.Spliterator;
import java.util.function.Consumer;

/**
 * Provides a history of messages between the User, Assistant and System
 */
public class ChatHistory implements Iterable<ChatMessageContent> {

    private final List<ChatMessageContent> chatMessageContents;

    public ChatHistory() {
        this.chatMessageContents = new ArrayList<>();
    }

    public ChatHistory(List<ChatMessageContent> chatMessageContents) {
        this.chatMessageContents = new ArrayList<>(chatMessageContents);
    }

    /**
     * Get the chat history
     *
     * @return List of messages in the chat
     */
    public List<ChatMessageContent> getMessages() {
        return Collections.unmodifiableList(chatMessageContents);
    }

    /**
     * Get last message
     *
     * @return The most recent message in chat
     */
    public Optional<ChatMessageContent> getLastMessage() {
        if (chatMessageContents.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(chatMessageContents.get(chatMessageContents.size() - 1));
    }

    public void addAll(ChatHistory value) {
        this.chatMessageContents.addAll(value.getMessages());
    }

    @Override
    public Iterator<ChatMessageContent> iterator() {
        return chatMessageContents.iterator();
    }

    @Override
    public void forEach(Consumer<? super ChatMessageContent> action) {
        chatMessageContents.forEach(action);
    }

    @Override
    public Spliterator<ChatMessageContent> spliterator() {
        return chatMessageContents.spliterator();
    }


    /**
     * Add a message to the chat history
     *
     * @param authorRole Role of the message author
     * @param content    Message content
     */
    @Deprecated
    public void addMessage(AuthorRoles authorRole, String content) {
        this.chatMessageContents.add(new ChatMessageContent(authorRole, content));
    }

    /**
     * Add a message to the chat history with the user as the author
     *
     * @param content Message content
     * @since 1.0.0 @
     */
    public void addUserMessage(String content) {
        this.chatMessageContents.add(new ChatMessageContent(AuthorRoles.User, content));
    }

    /**
     * Add a message to the chat history with the assistat as the author
     *
     * @param content Message content
     * @since 1.0.0
     */
    public void addAssistantMessage(String content) {
        this.chatMessageContents.add(new ChatMessageContent(AuthorRoles.Assistant, content));
    }
}
