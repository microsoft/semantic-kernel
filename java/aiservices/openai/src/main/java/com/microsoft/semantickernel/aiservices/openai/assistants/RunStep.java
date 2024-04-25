package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.time.OffsetDateTime;
import java.util.Map;

public interface RunStep {

    /**
     * Get the identifier of the run step.
     *
     * @return The identifier of the run step.
     */
    String getId();

    /**
     * Get the object type of the run step.
     *
     * @return The object type of the run step.
     */
    ThreadType getObject();

    /**
     * Get the Unix timestamp for when the run step was created.
     *
     * @return The Unix timestamp for when the run step was created.
     */
    OffsetDateTime getCreatedAt();

    /**
     * Get the ID of the assistant associated with the run step.
     *
     * @return The ID of the assistant associated with the run step.
     */
    String getAssistantId();

    /**
     * Get the ID of the thread that was run.
     *
     * @return The ID of the thread that was run.
     */
    String getThreadId();

    /**
     * Get the ID of the run that this run step is a part of.
     *
     * @return The ID of the run that this run step is a part of.
     */
    String getRunId();

    /**
     * Get the type of run step.
     *
     * @return The type of run step.
     */
    RunStepType getType();

    /**
     * Get the status of the run step.
     *
     * @return The status of the run step.
     */
    RunStatus getStatus();

    /**
     * Get the details of the run step.
     *
     * @return The details of the run step.
     */
    StepDetails getStepDetails();

    /**
     * Get the last error associated with this run step.
     *
     * @return The last error associated with this run step, or null if there are no errors.
     */
    RunError getLastError();

    /**
     * Get the Unix timestamp for when the run step expired.
     *
     * @return The Unix timestamp for when the run step expired, or null if the step is not expired.
     */
    OffsetDateTime getExpiredAt();

    /**
     * Get the Unix timestamp for when the run step was cancelled.
     *
     * @return The Unix timestamp for when the run step was cancelled, or null if the step was not cancelled.
     */
    OffsetDateTime getCancelledAt();

    /**
     * Get the Unix timestamp for when the run step failed.
     *
     * @return The Unix timestamp for when the run step failed, or null if the step did not fail.
     */
    OffsetDateTime getFailedAt();

    /**
     * Get the Unix timestamp for when the run step completed.
     *
     * @return The Unix timestamp for when the run step completed, or null if the step is not completed.
     */
    OffsetDateTime getCompletedAt();

    /**
     * Get the metadata of the run step.
     *
     * @return The metadata of the run step.
     */
    Map<String, String> getMetadata();

    /**
     * Get the usage statistics related to the run step.
     *
     * @return The usage statistics related to the run step, or null if the status is in_progress.
     */
    Usage getUsage();
}