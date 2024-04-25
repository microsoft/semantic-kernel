package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;

/**
 * Represents a message within a thread.
 */
public interface Message {
    
    /**
     * Get the identifier, which can be referenced in API endpoints.
     * 
     * @return The identifier.
     */
    String getId();
    
    /**
     * Get the object type, which is always {@code thread.message}.
     * 
     * @return The object type.
     */
    default ThreadType getType() { return ThreadType.THREAD_MESSAGE; };
    
    /**
     * Get the Unix timestamp (in seconds) for when the message was created.
     * 
     * @return The created timestamp.
     */
    OffsetDateTime getCreatedAt();
    
    /**
     * Get the thread ID that this message belongs to.
     * 
     * @return The thread ID.
     */
    String getThreadId();
    
    /**
     * Get the status of the message, which can be either in_progress, incomplete, or completed.
     * 
     * @return The message status.
     */
    MessageStatus getStatus();
    
    /**
     * Get details about why the message is incomplete.
     * 
     * @return The incomplete details.
     */
    String getIncompleteDetails();
    
    /**
     * Get the Unix timestamp (in seconds) for when the message was completed.
     * 
     * @return The completed timestamp.
     */
    OffsetDateTime getCompletedAt();
    
    /**
     * Get the Unix timestamp (in seconds) for when the message was marked as incomplete.
     * 
     * @return The incomplete timestamp.
     */
    OffsetDateTime getIncompleteAt();
    
    /**
     * Get the entity that produced the message. 
     * 
     * @return The message role.
     */
    AuthorRole getRole();
    
    /**
     * Get the content of the message in array of text and/or images.
     * 
     * @return The message content.
     */
    List<MessageContent> getContent();
    
    /**
     * Get the ID of the assistant that authored this message.
     * 
     * @return The assistant ID.
     */
    String getAssistantId();
    
    /**
     * Get the ID of the run associated with the creation of this message.
     * 
     * @return The run ID.
     */
    String getRunId();
    
    /**
     * Get the list of files attached to the message, and the tools they were added to.
     * 
     * @return The attachments.
     */
    List<MessageAttachments> getAttachments();
    
    /**
     * Get the set of key-value pairs that can be attached to an object.
     * 
     * @return The metadata.
     */
    Map<String, String> getMetadata();
}