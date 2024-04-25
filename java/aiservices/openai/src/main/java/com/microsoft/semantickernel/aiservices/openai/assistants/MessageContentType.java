package com.microsoft.semantickernel.aiservices.openai.assistants;

public enum MessageContentType {
    
    IMAGE_FILE("image_file"),
    TEXT("text");

    private final String value;
    private MessageContentType(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return value;
    }
}
