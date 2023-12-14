// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

/**
 * Role of the author of a chat message
 */
public enum AuthorRole {

    SYSTEM("system"),
    ASSISTANT("assistant"),
    USER("user"),
    TOOL("tool");

    @Override
    public String toString() {
        return role;
    }

    public AuthorRole fromString(String role) {
        for (AuthorRole authorRole : AuthorRole.values()) {
            if (authorRole.role.equalsIgnoreCase(role)) {
                return authorRole;
            }
        }
        return null;
    }

    private final String role;

    private AuthorRole(String role) {
        this.role = role;
    }
}
