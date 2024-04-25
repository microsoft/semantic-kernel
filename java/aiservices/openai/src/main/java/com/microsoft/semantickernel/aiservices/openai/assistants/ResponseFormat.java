package com.microsoft.semantickernel.aiservices.openai.assistants;

/** 
 * Types for the Assistant response format.
 * An object describing the expected output of the model. 
 * If json_object only function type tools are allowed to 
 * be passed to the Run. If text the model can return text 
 * or any value needed
 */
public enum ResponseFormat {
    AUTO("auto"),
    JSON("json"),
    TEXT("text");

    private final String value;
    private ResponseFormat(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }

}
