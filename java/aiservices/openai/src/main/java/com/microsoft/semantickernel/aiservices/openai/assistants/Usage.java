package com.microsoft.semantickernel.aiservices.openai.assistants;

public interface Usage {
    /**
     * Get the number of completion tokens used over the course of the run step.
     *
     * @return The number of completion tokens used.
     */
    int getCompletionTokens();

    /**
     * Get the number of prompt tokens used over the course of the run step.
     *
     * @return The number of prompt tokens used.
     */
    int getPromptTokens();

    /**
     * Get the total number of tokens used (prompt + completion) over the course of the run step.
     *
     * @return The total number of tokens used.
     */
    int getTotalTokens();
}