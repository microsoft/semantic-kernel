package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.KernelContent;

public class TextContent extends KernelContent<TextContent> {

    private final String content;

    public TextContent(String content) {
        super(content, null, null);
        this.content = content;
    }

    public String getValue() {
        return content;
    }

    public String getContent() {
        return content;
    }
}
