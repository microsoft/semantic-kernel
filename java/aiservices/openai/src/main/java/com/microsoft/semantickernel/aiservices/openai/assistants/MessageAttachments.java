package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.List;

/** 
 * Represents a file attached to the message, and the tools it was added to.
 */
public interface MessageAttachments {

    /**
     * The file's identifier.
     * @return The file's identifier.
     */
    public String getFileId();

    /**
     * The tools that the file was added to.
     * @return The tools that the file was added to.
     */
    List<ToolType> getTools();

}
