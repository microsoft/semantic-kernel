package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Represents the type of message.
 */
public enum ThreadType {
    THREAD_MESSAGE("thread.message"),
    THREAD_RUN("thread.run"),
    THREAD_RUN_STEP("thread.run.step");

    private final String value;

    ThreadType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
