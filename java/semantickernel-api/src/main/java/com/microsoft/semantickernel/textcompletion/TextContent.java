package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.KernelContent;
import com.microsoft.semantickernel.orchestration.FunctionResultMetadata;

public class TextContent extends KernelContent<TextContent> {

    private final String content;

    public TextContent(
        String content,
        String modelId,
        FunctionResultMetadata metadata) {
        super(content, modelId, metadata);
        this.content = content;
    }

    public String getValue() {
        return content;
    }

    @Override
    public String getContent() {
        return content;
    }
}
