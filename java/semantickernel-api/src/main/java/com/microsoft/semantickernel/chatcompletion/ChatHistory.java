// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

/** Provides a history of messages between the User, Assistant and System */
public class ChatHistory {

    private final List<Message> messages;

    public ChatHistory() {
        this.messages = new ArrayList<>();
    }

    /**
     * Get the chat history
     *
     * @return List of messages in the chat
     */
    public List<Message> getMessages() {
        return Collections.unmodifiableList(messages);
    }

    /**
     * Get last message
     *
     * @return The most recent message in chat
     */
    public Optional<Message> getLastMessage() {
        if (messages.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(messages.get(messages.size() - 1));
    }

    /** Role of the author of a chat message */
    public enum AuthorRoles {
        Unknown,
        System,
        User,
        Assistant
    }

    /** Chat message representation */
    public static class Message {
        private final AuthorRoles authorRoles;

        private final String content;

        /**
         * Create a new instance
         *
         * @param authorRoles Role of message author
         * @param content Message content
         */
        public Message(AuthorRoles authorRoles, String content) {
            this.authorRoles = authorRoles;
            this.content = content;
        }

        /**
         * Get the role of the message author
         *
         * @return Role of the message author, e.g. user/assistant/system
         */
        public AuthorRoles getAuthorRoles() {
            return authorRoles;
        }

        /**
         * Get the message content
         *
         * @return Message content
         */
        public String getContent() {
            return content;
        }
    }

    /**
     * Add a message to the chat history
     *
     * @param authorRole Role of the message author
     * @param content Message content
     */
    public void addMessage(AuthorRoles authorRole, String content) {
        this.messages.add(new Message(authorRole, content));
    }
}
