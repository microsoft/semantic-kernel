package com.microsoft.semantickernel;

import java.util.Map;

import com.microsoft.semantickernel.orchestration.ContextVariable;

public class KernelContent {

    public KernelContent(
        Object innerContent,
        String modelId,
        Map<String, ContextVariable<?>> metadata
    ) {}

}
