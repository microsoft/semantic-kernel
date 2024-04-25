package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum TextContentAnnotationType {

    FILE_CITATION("file_citation"),
    FILE_PATH("file_path");

    private final String value;

    private TextContentAnnotationType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
