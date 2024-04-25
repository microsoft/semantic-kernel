package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

/**
 * Represents an execution run on a thread.
 */
public interface Run {
    
    /**
     * Get the identifier, which can be referenced in API endpoints.
     *
     * @return the identifier
     */
    String getId();

    /** 
     * Get the object type, which is always {@code thread.run}.
     * @return the object type, which is always {@code thread.run}
     */
    ThreadType getType();

    /**
     * Get the Unix timestamp for when the run was created.
     * @return the Unix timestamp for when the run was created. 
     */
    OffsetDateTime getCreatedAt();

    /**
     * Get the ID of the thread that was executed on as a part of this run.
     * @return the ID of the thread
     */
    String getThreadId();

    /**
     * Get the ID of the assistant used for execution of this run.
     * @return the ID of the assistant
     */
    String getAssistantId();

    /**
     * Get the status of the run.
     * @return the status of the run
     */
    RunStatus getStatus();

    /**
     * Get details on the action required to continue the run.
     * @return the details on the action required, or null if no action is required
     */
    RequiredAction getRequiredAction();

    /**
     * Get the last error associated with this run.
     * @return the last error, or null if there are no errors
     */
    RunError getLastError();

    /**
     * Get the Unix timestamp for when the run will expire.
     * @return the Unix timestamp for when the run will expire
     */
    OffsetDateTime getExpiresAt();

    /**
     * Get the Unix timestamp for when the run was started.
     * @return the Unix timestamp for when the run was started
     */
    OffsetDateTime getStartedAt();

    /**
     * Get the Unix timestamp for when the run was cancelled.
     * @return the Unix timestamp for when the run was cancelled
     */
    OffsetDateTime getCancelledAt();

    /**
     * Get the Unix timestamp for when the run failed.
     * @return the Unix timestamp for when the run failed
     */
    OffsetDateTime getFailedAt();

    /**
     * Get the Unix timestamp for when the run was completed.
     * @return the Unix timestamp for when the run was completed
     */
    OffsetDateTime getCompletedAt();

    /**
     * Get details on why the run is incomplete.
     * This will point to which specific token limit was reached over the course of the run.
     * @return the details on why the run is incomplete, or null if the run is not incomplete
     */
    String getIncompleteDetails();

    /**
     * Get the model that the assistant used for this run.
     * @return the model used for this run
     */
    String getModel();

    /**
     * Get the instructions that the assistant used for this run.
     * @return the instructions used for this run
     */
    String getInstructions();

    /**
     * Get the list of tools that the assistant used for this run.
     * @return the list of tools used for this run
     */
    List<ToolType> getTools();

    /**
     * Get the set of 16 key-value pairs that can be attached to an object.
     * @return the metadata attached to the object
     */
    Map<String, String> getMetadata();

    /**
     * Get usage statistics related to the run.
     * @return the usage statistics related to the run, or null if the run is not in a terminal state
     */
    Usage getUsage();

    /**
     * Get the sampling temperature used for this run.
     * @return the sampling temperature used for this run.
     */
    double getTemperature();

    /**
     * Get the nucleus sampling value used for this run.
     * @return the nucleus sampling value used for this run.
     */
    double getTopP();

    /**
     * Get the maximum number of prompt tokens specified to have been used over the course of the run.
     * @return the maximum number of prompt tokens used over the course of the run
     */
    int getMaxPromptTokens();

    /**
     * Get the maximum number of completion tokens specified to have been used over the course of the run.
     * @return the maximum number of completion tokens used over the course of the run
     */
    int getMaxCompletionTokens();

    /**
     * Get controls for how a thread will be truncated prior to the run.
     * @return the controls for truncation strategy
     */
    TruncationStrategy getTruncationStrategy();

    /**
     * Get controls which (if any) tool is called by the model.
     * @return the controls for tool choice
     */
    ToolChoice getToolChoice();

    /**
     * Get the format that the model must output.
     * @return the format for the model output
     */
    ResponseFormat getResponseFormat();
}
