package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.time.OffsetDateTime;
import java.util.Map;

/**
 * Represents a thread that contains messages.
 */
public interface Thread {
    /**
     * Gets the identifier, which can be referenced in API endpoints.
     *
     * @return The identifier.
     */
    String getId();

    /**
     * Gets the object type, which is always {@code thread}.
     *
     * @return The object type.
     */
    default String getObjectType() { return "thread"; };

    /**
     * Gets the Unix timestamp (in seconds) for when the thread was created.
     *
     * @return The creation timestamp.
     */
    OffsetDateTime getCreatedAt();

    /**
     * Gets the set of resources that are made available to the assistant's tools in this thread.
     * The resources are specific to the type of tool.
     * For example, the code_interpreter tool requires a list of file IDs,
     * while the file_search tool requires a list of vector store IDs.
     *
     * @return The tool resources or null if not available.
     */
    ToolResource getToolResources();

    /**
     * Gets the set of metadata attached to the object.
     * This can be useful for storing additional information about the object in a structured format.
     * Keys can be a maximum of 64 characters long and values can be a maximum of 512 characters long.
     *
     * @return The metadata.
     */
    Map<String, String> getMetadata();
}
