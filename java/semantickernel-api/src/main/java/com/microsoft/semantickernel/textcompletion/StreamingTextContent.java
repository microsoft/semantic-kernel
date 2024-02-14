package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.StreamingKernelContent;

/**
 * StreamingTextContent is a wrapper for TextContent that allows for streaming.
 */
public class StreamingTextContent extends StreamingKernelContent<TextContent> {

    /**
     * Initializes a new instance of the {@code StreamingTextContent} class with a provided text content.
     *
     * @param content The text content.
     */
    public StreamingTextContent(TextContent content) {
        super(content, 0, null, null);
    }

    @Override
    public String getContent() {
        return ((TextContent) getInnerContent()).getContent();
    }

}
