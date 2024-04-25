package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Represents an error that occurred during the execution of a run.
 */
public interface RunError {

    /**
     * Get the error code.
     * @return the error code
     */
    RunErrorCode getCode();

    /**
     * Get the error message.
     * @return the error message
     */
    String getMessage();
}
