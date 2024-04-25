package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum RunStepType {

    MESSAGE_CREATION("message_creation"),
    TOOL_CALLS("tool_calls");

    private final String value;

    private RunStepType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
