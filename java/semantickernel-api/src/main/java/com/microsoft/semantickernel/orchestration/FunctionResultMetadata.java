package com.microsoft.semantickernel.orchestration;

import com.azure.ai.openai.models.CompletionsUsage;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.time.OffsetDateTime;

public class FunctionResultMetadata {

    public static final String ID = "id";
    public static final String USAGE = "usage";
    public static final String CREATED_AT = "createdAt";


    private final CaseInsensitiveMap<ContextVariable<?>> metadata;

    public FunctionResultMetadata(CaseInsensitiveMap<ContextVariable<?>> metadata) {
        this.metadata = new CaseInsensitiveMap<>(metadata);
    }

    public static FunctionResultMetadata build(
        String id,
        CompletionsUsage usage,
        OffsetDateTime createdAt) {

        CaseInsensitiveMap<ContextVariable<?>> metadata = new CaseInsensitiveMap<>();
        metadata.put(ID, ContextVariable.of(id));
        metadata.put(USAGE, ContextVariable.of(usage));
        metadata.put(CREATED_AT, ContextVariable.of(createdAt));

        return new FunctionResultMetadata(metadata);
    }

    public static FunctionResultMetadata empty() {
        return new FunctionResultMetadata(new CaseInsensitiveMap<>());
    }

    public CaseInsensitiveMap<ContextVariable<?>> getMetadata() {
        return new CaseInsensitiveMap<>(metadata);
    }

    public String getId() {
        return metadata.get(ID).getValue(String.class);
    }

    public CompletionsUsage getUsage() {
        return metadata.get(USAGE).getValue(CompletionsUsage.class);
    }

    public OffsetDateTime getCreatedAt() {
        return metadata.get(CREATED_AT).getValue(OffsetDateTime.class);
    }
}
