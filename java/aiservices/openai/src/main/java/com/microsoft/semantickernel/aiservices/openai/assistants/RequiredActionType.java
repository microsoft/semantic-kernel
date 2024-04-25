package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum RequiredActionType {
    SUBMIT_TOOL_OUTPUTS("submit_tool_outputs");

    private final String value;

    RequiredActionType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }

}
