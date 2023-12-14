package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.util.Map;
import javax.annotation.Nullable;

public class KernelContent {

    public KernelContent(
        Object innerContent,
        @Nullable
        String modelId,
        @Nullable
        Map<String, ContextVariable<?>> metadata
    ) {}

}
