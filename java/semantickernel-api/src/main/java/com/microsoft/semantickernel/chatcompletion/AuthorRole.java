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

    private final String role;

    AuthorRole(String role) {
        this.role = role;
    }
}
