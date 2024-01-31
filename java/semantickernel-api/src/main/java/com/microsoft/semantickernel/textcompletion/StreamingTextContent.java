package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.StreamingKernelContent;

public class StreamingTextContent extends StreamingKernelContent<TextContent> {

    public StreamingTextContent(TextContent content) {
        super(content, 0, null, null);
    }

}
