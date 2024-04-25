package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

/**
 * Represents an OpenAI Assistant object.  
 */
public interface Assistant {

    /**
     * Get the identifier of the assistant.
     *
     * @return The identifier of the assistant.
     */
    String getId();

    /**
     * Get the object type of the assistant, which is always {@code assistant}.
     *
     * @return The object type of the assistant.
     */
    default String getObjectType() { return "assistant"; };

    /**
     * Get the Unix timestamp for when the assistant was created.
     *
     * @return The Unix timestamp for when the assistant was created.
     */
    OffsetDateTime getCreatedAt();

    /**
     * Get the name of the assistant.
     *
     * @return The name of the assistant.
     */
    @Nullable
    String getName();

    /**
     * Get the description of the assistant.
     *
     * @return The description of the assistant.
     */
    @Nullable
    String getDescription();

    /**
     * Get the ID of the model used by the assistant.
     *
     * @return The ID of the model used by the assistant.
     */
    String getModel();

    /**
     * Get the system instructions used by the assistant.
     *
     * @return The system instructions used by the assistant.
     */
    @Nullable
    String getInstructions();

    /**
     * Get the list of tools enabled on the assistant.
     *
     * @return The list of tools enabled on the assistant.
     */
    List<Tool> getTools();

    /**
     * Get the set of resources used by the assistant's tools.
     *
     * @return The set of resources used by the assistant's tools.
     */
    @Nullable
    Map<ToolType, ToolResource> getToolResources();

    /**
     * Get the metadata attached to the assistant.
     *
     * @return The metadata attached to the assistant.
     */
    Map<String, String> getMetadata();

    /**
     * Get the sampling temperature used by the assistant.
     *
     * @return The sampling temperature used by the assistant.
     */
    @Nullable
    Double getTemperature();

    /**
     * Get the top p value used by the assistant.
     *
     * @return The top p value used by the assistant.
     */
    @Nullable
    Double getTopP();

    /**
     * Get the response format used by the assistant.
     *
     * @return The response format used by the assistant.
     */
    String getResponseFormat();
}