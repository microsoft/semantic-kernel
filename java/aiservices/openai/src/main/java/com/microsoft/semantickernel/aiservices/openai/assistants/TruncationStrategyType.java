package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * The truncation strategy to use for the thread.
 * The default is {@code auto}. 
 * If set to {@code last_messages}, the thread will be truncated to the 
 * {@code n}  most recent messages in the thread. 
 * When set to {@code auto}, messages in the middle of the thread will 
 * be dropped to fit the context length of the model, 
 * {@code max_prompt_tokens}.
*/
public enum TruncationStrategyType {
    AUTO("auto"),
    LAST_MESSAGES("last_messages");

    private final String value;

    private TruncationStrategyType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}