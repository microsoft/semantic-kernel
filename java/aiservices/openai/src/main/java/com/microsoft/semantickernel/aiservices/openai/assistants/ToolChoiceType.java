package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Controls which (if any) tool is called by the model. 
 * {@code none} means the model will not call any tools and instead
 * generates a message. {@code auto} is the default value and means 
 * the model can pick between generating a message or calling a tool. 
 * Specifying a particular tool like {"type": "file_search"} or {"type": "function", "function": {"name": "my_function"}} forces the model to call that tool.
 */
public enum ToolChoiceType {

    NONE("none"),
    AUTO("auto"),
    REQUIRED("required");

    private final String value;

    private ToolChoiceType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }

}
