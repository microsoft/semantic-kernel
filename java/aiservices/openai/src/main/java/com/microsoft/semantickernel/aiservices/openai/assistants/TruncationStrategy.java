package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Controls for how a thread will be truncated prior to the run. Use this to control the intial context window of the run
 */
public interface TruncationStrategy {

    /**
     * The truncation strategy to use for the thread
     * @return the truncation strategy to use for the thread
     */
    TruncationStrategyType getType();

    /**
     * The number of most recent messages from the thread when constructing the context for the run
     * @return the number of most recent messages from the thread when constructing the context for the run
     */
    int getLastMessages();
}
