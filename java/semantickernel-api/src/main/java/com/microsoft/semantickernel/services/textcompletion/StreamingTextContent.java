package com.microsoft.semantickernel.services.textcompletion;

import com.microsoft.semantickernel.services.StreamingKernelContent;
import javax.annotation.Nullable;

/**
 * StreamingTextContent is a wrapper for TextContent that allows for streaming.
 */
public class StreamingTextContent extends StreamingKernelContent<TextContent> {

    /**
     * Initializes a new instance of the {@code StreamingTextContent} class with a provided text
     * content.
     *
     * @param content The text content.
     */
    public StreamingTextContent(TextContent content) {
        super(content, 0, null, null);
    }

    @Override
    @Nullable
    public String getContent() {
        TextContent content = getInnerContent();
        if (content == null) {
            return null;
        }
        return content.getContent();
    }

}
