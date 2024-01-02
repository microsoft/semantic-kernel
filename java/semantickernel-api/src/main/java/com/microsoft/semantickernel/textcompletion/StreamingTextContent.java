package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.orchestration.StreamingContent;

public class StreamingTextContent extends StreamingContent<TextContent> {

    public StreamingTextContent(TextContent content) {
        super(content);
    }
}
