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

import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;

/**
 * Provides a history of messages between the User, Assistant and System
 */
public class ChatHistory implements Iterable<ChatMessageContent> {

    private final static String DEFAULT_CHAT_SYSTEM_PROMPT = "Assistant is a large language model.";

    private final List<ChatMessageContent> chatMessageContents;

    public ChatHistory() {
        this(DEFAULT_CHAT_SYSTEM_PROMPT);
    }

    public ChatHistory(String instructions) {
        this.chatMessageContents = new ArrayList<>();
        this.chatMessageContents.add(
            new ChatMessageContent(
                AuthorRole.ASSISTANT, 
                instructions == null || instructions.isEmpty() ? DEFAULT_CHAT_SYSTEM_PROMPT : instructions
            )
        );
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

    public void addMessage(AuthorRole authorRole, String content, Charset encoding,
        FunctionResultMetadata metadata) {
        chatMessageContents.add(
            new ChatMessageContent(authorRole, content, null, null, encoding, metadata));
    }


    public void addMessage(AuthorRole authorRole, String content) {
        chatMessageContents.add(
            new ChatMessageContent(authorRole, content, null, null, null, null));
    }

    public void addMessage(ChatMessageContent content) {
        chatMessageContents.add(content);
    }

    public void addUserMessage(String content) {
        addMessage(AuthorRole.USER, content);
    }

    public void addAssistantMessage(String content) {
        addMessage(AuthorRole.ASSISTANT, content);
    }
}
