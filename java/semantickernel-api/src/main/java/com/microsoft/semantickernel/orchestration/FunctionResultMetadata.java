package com.microsoft.semantickernel.orchestration;

import com.azure.ai.openai.models.CompletionsUsage;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import java.time.OffsetDateTime;
import javax.annotation.Nullable;

/**
 * Metadata about the result of a function invocation.
 * <p>
 * This class is used to return metadata about the result of a function invocation.
 */
public class FunctionResultMetadata {

    /** The key for id metadata. */
    public static final String ID = "id";

    /** The key for usage metadata. */
    public static final String USAGE = "usage";

    /** The key for createdAt metadata. */
    public static final String CREATED_AT = "createdAt";

    private final CaseInsensitiveMap<ContextVariable<?>> metadata;

    /**
     * Create a new instance of FunctionResultMetadata.
     */
    public FunctionResultMetadata() {
        this.metadata = new CaseInsensitiveMap<>();
    }

    /**
     * Create a new instance of FunctionResultMetadata.
     *
     * @param metadata Metadata about the result of the function invocation.
     */
    public FunctionResultMetadata(CaseInsensitiveMap<ContextVariable<?>> metadata) {
        this.metadata = new CaseInsensitiveMap<>(metadata);
    }

    /**
     * Create a new instance of FunctionResultMetadata.
     *
     * @param id       The id of the result of the function invocation.
     * @param usage    The usage of the result of the function invocation.
     * @param createdAt The time the result was created.
     * @return A new instance of FunctionResultMetadata.
     */
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

    /**
     * Create a new instance of FunctionResultMetadata with no metadata.
     *
     * @return A new instance of FunctionResultMetadata.
     */
    public static FunctionResultMetadata empty() {
        return new FunctionResultMetadata(new CaseInsensitiveMap<>());
    }

    /**
     * Get the metadata about the result of the function invocation.
     *
     * @return The metadata about the result of the function invocation.
     */
    public CaseInsensitiveMap<ContextVariable<?>> getMetadata() {
        return new CaseInsensitiveMap<>(metadata);
    }

    /**
     * Get the id of the result of the function invocation.
     *
     * @return The id of the result of the function invocation.
     */
    @Nullable
    public String getId() {
        ContextVariable<?> id = metadata.get(ID);
        if (id == null) {
            return null;
        }
        return id.getValue(String.class);
    }

    /**
     * Get the usage of the result of the function invocation.
     *
     * @return The usage of the result of the function invocation.
     */
    @Nullable
    public CompletionsUsage getUsage() {
        ContextVariable<?> usage = metadata.get(USAGE);
        if (usage == null) {
            return null;
        }
        return usage.getValue(CompletionsUsage.class);
    }

    /**
     * Get the time the result was created.
     *
     * @return The time the result was created.
     */
    @Nullable
    public OffsetDateTime getCreatedAt() {
        ContextVariable<?> createdAt = metadata.get(CREATED_AT);
        if (createdAt == null) {
            return null;
        }
        return createdAt.getValue(OffsetDateTime.class);
    }
}
