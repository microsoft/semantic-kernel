package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum RunStatus {

    QUEUED("queued"),
    IN_PROGRESS("in_progress"),
    REQUIRES_ACTION("requires_action"),
    CANCELLING("cancelling"),
    CANCELLED("cancelled"),
    FAILED("failed"),
    COMPLETED("completed"),
    EXPIRED("expired");

    private final String value;

    RunStatus(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
