package com.microsoft.semantickernel.aiservices.openai.assistants;

public interface FilePathAnnotation extends TextContentAnnotation {

    @Override
    default TextContentAnnotationType getType() { return TextContentAnnotationType.FILE_PATH; }

    /**
     * The text in the message content that needs to be replaced.
     * @return The text in the message content that needs to be replaced.
     */
    String getText();

    /**
     * The ID of the file that was generated.
     * @return The ID of the file that was generated.
     */
    String getFileId();

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
