package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.search.documents.indexes.SearchableField;
import com.azure.search.documents.indexes.SimpleField;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Azure Cognitive Search record and index definition.
 * Note: once defined, index cannot be modified.
 */
public final class AzureCognitiveSearchRecord
{
    @SimpleField(isKey = true, isFilterable = false)
    @Nonnull private final String id;

    @SearchableField(analyzerName = "en.lucene")
    @Nullable private final String text;

    @SearchableField(analyzerName = "en.lucene")
    @Nullable private final String description;
    @SearchableField(analyzerName = "en.lucene")
    @Nullable private final String additionalMetadata;

    @SimpleField(isFilterable = false)
    @Nullable private final String externalSourceName;

    @SimpleField(isFilterable = false)
    private final boolean isReference;

    public AzureCognitiveSearchRecord(
            @Nonnull String id,
            @Nullable String text,
            @Nullable String description,
            @Nullable String additionalMetadata,
            @Nullable String externalSourceName,
            boolean isReference) {
        this.id = id;
        this.text = text;
        this.description = description;
        this.additionalMetadata = additionalMetadata;
        this.externalSourceName = externalSourceName;
        this.isReference = isReference;
    }
    /**
     * Record ID.
     * The record is not filterable to save quota, also SK uses only semantic search.
     * @return Record ID.
     */
    public @Nonnull String getId() { return id; }

    /**
     * Content is stored here.
     * @return Content is stored here,  {@code null} if not set.
     */
    public @Nullable String getText() {
        return text;
    }

    /**
     * Optional description of the content, e.g. a title. This can be useful when
     * indexing external data without pulling in the entire content.
     * @return Optional description of the content,  {@code null} if not set.
     */
    public @Nullable String getDescription() {
        return description;
    }

    /**
     * Additional metadata. Currently, this is a String where you could store serialized data as JSON.
     * In future the design might change to allow storing named values and leverage filters.
     * @return Additional metadata,  {@code null} if not set.
     */
    public @Nullable String getAdditionalMetadata() {
        return additionalMetadata;
    }

    /**
     * Name of the external source, in cases where the content and the Id are referenced to external information.
     * @return Name of the external source, in cases where the content and the Id are referenced to external information,  {@code null} if not set.
     */
    public @Nullable String getExternalSourceName() {
        return externalSourceName;
    }

    /**
     * Whether the record references external information.
     * @return {@code true} if the record references external information, {@code false} otherwise.
     */
    public boolean isReference() { return isReference; }

    // TODO: add one more field with the vector, float array, mark it as searchable
}
