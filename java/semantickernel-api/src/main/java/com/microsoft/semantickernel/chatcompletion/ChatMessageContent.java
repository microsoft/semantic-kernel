package com.microsoft.semantickernel.chatcompletion;

/**
 * Chat message representation
 */
public class ChatMessageContent {

    private final AuthorRoles authorRoles;

    private final String content;

    /**
     * Create a new instance
     *
     * @param authorRoles Role of message author
     * @param content     Message content
     */
    public ChatMessageContent(AuthorRoles authorRoles, String content) {
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