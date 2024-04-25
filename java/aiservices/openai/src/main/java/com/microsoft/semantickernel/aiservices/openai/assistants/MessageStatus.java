package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum MessageStatus {
    IN_PROGRESS("in_progress"),
    INCOMPLETE("incomplete"),
    COMPLETED("completed");

    private final String value;

    MessageStatus(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
