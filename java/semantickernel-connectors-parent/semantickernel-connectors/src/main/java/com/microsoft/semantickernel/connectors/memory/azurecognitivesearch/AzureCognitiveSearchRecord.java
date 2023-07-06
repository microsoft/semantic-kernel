// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.search.documents.indexes.SearchableField;
import com.azure.search.documents.indexes.SimpleField;
import com.azure.search.documents.indexes.models.LexicalAnalyzerName;
import com.azure.search.documents.indexes.models.SearchField;
import com.azure.search.documents.indexes.models.SearchFieldDataType;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Arrays;
import java.util.List;

/**
 * Azure Cognitive Search record and index definition. Note: once defined, index cannot be modified.
 */
public final class AzureCognitiveSearchRecord {
    @SimpleField(isKey = true, isFilterable = false)
    private final String id;

    @SearchableField(analyzerName = "standard.lucene")
    private final String text;

    @SearchableField(analyzerName = "standard.lucene")
    private final String description;

    @SearchableField(analyzerName = "standard.lucene")
    private final String additionalMetadata;

    @SimpleField(isFilterable = false)
    private final String externalSourceName;

    @SimpleField(isFilterable = false)
    private final boolean isReference;

    @JsonCreator
    public AzureCognitiveSearchRecord(
            @JsonProperty("Id") String id,
            @JsonProperty("Text") String text,
            @JsonProperty("Description") String description,
            @JsonProperty("AdditionalMetadata") String additionalMetadata,
            @JsonProperty("ExternalSourceName") String externalSourceName,
            @JsonProperty("Reference") boolean isReference) {
        this.id = id;
        this.text = text;
        this.description = description;
        this.additionalMetadata = additionalMetadata;
        this.externalSourceName = externalSourceName;
        this.isReference = isReference;
    }

    /**
     * Record ID. The record is not filterable to save quota, also SK uses only semantic search.
     *
     * @return Record ID.
     */
    public String getId() {
        return id;
    }

    /**
     * Content is stored here.
     *
     * @return Content is stored here, {@code null} if not set.
     */
    public String getText() {
        return text;
    }

    /**
     * Optional description of the content, e.g. a title. This can be useful when indexing external
     * data without pulling in the entire content.
     *
     * @return Optional description of the content, {@code null} if not set.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Additional metadata. Currently, this is a String where you could store serialized data as
     * JSON. In future the design might change to allow storing named values and leverage filters.
     *
     * @return Additional metadata, {@code null} if not set.
     */
    public String getAdditionalMetadata() {
        return additionalMetadata;
    }

    /**
     * Name of the external source, in cases where the content and the Id are referenced to external
     * information.
     *
     * @return Name of the external source, in cases where the content and the Id are referenced to
     *     external information, {@code null} if not set.
     */
    public String getExternalSourceName() {
        return externalSourceName;
    }

    /**
     * Whether the record references external information.
     *
     * @return {@code true} if the record references external information, {@code false} otherwise.
     */
    public boolean isReference() {
        return isReference;
    }

    // TODO: Potentially remove after resolution of
    //  https://github.com/Azure/azure-sdk-for-java/issues/35584
    static List<SearchField> searchFields() {
        return Arrays.asList(
                new SearchField("Id", SearchFieldDataType.STRING).setKey(true).setFilterable(false),
                new SearchField("Text", SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField("Description", SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField("AdditionalMetadata", SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField("ExternalSourceName", SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField("Reference", SearchFieldDataType.BOOLEAN).setFilterable(true));
    }
    // TODO: add one more field with the vector, float array, mark it as searchable

}
