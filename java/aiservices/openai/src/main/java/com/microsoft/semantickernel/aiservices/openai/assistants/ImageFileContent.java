package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * References an image {@link com.microsoft.semantickernel.aiservices.openai.assistants.File}
 * in the content of a message.
 */
public interface ImageFileContent extends MessageContent {

    @Override
    default MessageContentType getType() {
        return MessageContentType.IMAGE_FILE;
    }

    /**
     * The ID of the image file.
     * @return The ID of the image file.
     */
    String getFileId();

}
