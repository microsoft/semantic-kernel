package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum RunErrorCode {

    SERVER_ERROR("server_error"),
    RATE_LIMIT_EXCEEDED("rate_limit_exceeded"),
    INVALID_PROMPT("invalid_prompt");

    private final String value;

    private RunErrorCode(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
