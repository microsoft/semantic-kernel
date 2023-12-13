package com.microsoft.semantickernel;

import java.util.Map;

import com.microsoft.semantickernel.orchestration.ContextVariable;

public abstract class StreamingKernelContent {
    
    protected StreamingKernelContent(Object innerContent, int choiceIndex, String modelId, Map<String, ContextVariable<?>> metadata) {
    }

    public abstract byte[] toByteArray();
}
