package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;

/**
 * Represents a message within a Thread.
 */
public interface AssistantMessage {


    /**
     * The identifier, which can be referenced in API endpoints.
     * @return string
     */
    String id();

    /**
     * The object type, which is always thread.message.
     * @return string
     */
    String getObject();

    /**
     * The Unix timestamp (in seconds) for when the message was created.
     * @return integer
     */
    int getCreatedAt();

    /**
     * The thread ID that this message belongs to.
     * @return string
     */
    String getThreadId();

    /**
     * The status of the message, which can be either in_progress, incomplete, or completed.
     * @return string
     */
    String getStatus();

    /**
     * On an incomplete message, details about why the message is incomplete.
     * @return object or null
     */
    @Nullable Object getIncompleteDetails();

    /**
     * The Unix timestamp (in seconds UTC) for when the message was completed.
     * @return epoch time in UTC, or null
     */
    @Nullable Long getCompletedAt();

    /**
     * The Unix timestamp (in seconds in UTC) for when the message was marked as incomplete.
     * @return epoch time in UTC, or null
     */
    @Nullable Long getIncompleteAt();

    /**
     * The entity that produced the message. One of user or assistant.
     * @return string
     */
    String getRole();

    /**
     * The content of the message in array of text and/or images.
     * @return array
     */
    List<String> getContent();

    /**
     * If applicable, the ID of the assistant that authored this message.
     * @return string or null
     */
    @Nullable String getAssistantId();

    /**
     * The ID of the run associated with the creation of this message. Value is null when messages are created manually using the create message or create thread endpoints.
     * @return string or null
     */
    @Nullable String getRunId();

    /**
     * A list of file IDs that the assistant should use. Useful for tools like retrieval and code_interpreter that can access files. A maximum of 10 files can be attached to a message.
     * @return array
     */
    List<String> getFileIds();

    /**
     * Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format. Keys can be a maximum of 64 characters long and values can be a maxium of 512 characters long.
     * @return map
     */
    Map<String, String> getMetadata();

}