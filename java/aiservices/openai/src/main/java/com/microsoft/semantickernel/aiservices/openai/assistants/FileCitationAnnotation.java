package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * A citation within the message that points to a specific quote from 
 * a specific File associated with the assistant or the message. 
 * Generated when the assistant uses the "file_search" tool to search files.
 */
public interface FileCitationAnnotation extends TextContentAnnotation {

    @Override
    default TextContentAnnotationType getType() { return TextContentAnnotationType.FILE_CITATION; }

    /**
     * The text in the message content that needs to be replaced.
     * @return The text in the message content that needs to be replaced.
     */
    String getText();

    /**
     * The ID of the file that the citation is pointing to.
     * @return The ID of the file that the citation is pointing to.
     */
    String getFileId();

    /**
     * The quote from the file that the citation is pointing to.
     * @return The quote from the file that the citation is pointing to.
     */
    String getQuote();

    /**
     * The start index of the quote in the file.
     * @return The start index of the quote in the file.
     */
    int getStartIndex();

    /**
     * The end index of the quote in the file.
     * @return The end index of the quote in the file.
     */
    int getEndIndex();
}
