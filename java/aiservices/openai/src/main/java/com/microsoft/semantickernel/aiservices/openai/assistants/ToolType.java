package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum ToolType {
    CODE_INTERPRETER("code_interpreter"),
    FILE_SEARCH("file_search"),
    FUNCTION("function");

    private final String value;

    ToolType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
