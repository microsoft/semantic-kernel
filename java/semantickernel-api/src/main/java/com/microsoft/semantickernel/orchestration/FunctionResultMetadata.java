// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;

import java.time.OffsetDateTime;
import javax.annotation.Nullable;

/**
 * Metadata about the result of a function invocation.
 * <p>
 * This class is used to return metadata about the result of a function invocation.
 */
public class FunctionResultMetadata<UsageType> {

    /**
     * The key for id metadata.
     */
    public static final String ID = "id";

    /**
     * The key for usage metadata.
     */
    public static final String USAGE = "usage";

    /**
     * The key for createdAt metadata.
     */
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
     */
    public static FunctionResultMetadata<?> build(String id) {
        return build(id, null, null);
    }

    /**
     * Create a new instance of FunctionResultMetadata.
     *
     * @param id        The id of the result of the function invocation.
     * @param usage     The usage of the result of the function invocation.
     * @param createdAt The time the result was created.
     * @return A new instance of FunctionResultMetadata.
     */
    public static <UsageType> FunctionResultMetadata<UsageType> build(
        String id,
        @Nullable UsageType usage,
        @Nullable OffsetDateTime createdAt) {

        CaseInsensitiveMap<ContextVariable<?>> metadata = new CaseInsensitiveMap<>();

        metadata.put(ID, ContextVariable.of(id));

        if (usage != null) {
            metadata.put(USAGE, ContextVariable.of(usage,
                new ContextVariableTypeConverter.NoopConverter<>(Object.class)));
        }
        if (createdAt != null) {
            metadata.put(CREATED_AT, ContextVariable.of(createdAt));
        }

        return new FunctionResultMetadata<>(metadata);
    }

    /**
     * Create a new instance of FunctionResultMetadata with no metadata.
     *
     * @return A new instance of FunctionResultMetadata.
     */
    public static FunctionResultMetadata<?> empty() {
        return new FunctionResultMetadata<>(new CaseInsensitiveMap<>());
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
    public UsageType getUsage() {
        ContextVariable<?> usage = metadata.get(USAGE);
        if (usage == null) {
            return null;
        }
        return (UsageType) usage.getValue(Object.class);
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
