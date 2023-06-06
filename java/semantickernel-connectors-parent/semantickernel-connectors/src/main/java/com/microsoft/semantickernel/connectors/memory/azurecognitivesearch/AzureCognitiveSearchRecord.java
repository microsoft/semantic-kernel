package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.search.documents.indexes.SearchableField;
import com.azure.search.documents.indexes.SimpleField;
import com.azure.search.documents.indexes.models.LexicalAnalyzerName;
import com.azure.search.documents.indexes.models.SearchField;
import com.azure.search.documents.indexes.models.SearchFieldDataType;
import com.fasterxml.jackson.core.JacksonException;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.fasterxml.jackson.databind.deser.std.StdDeserializer;
import com.fasterxml.jackson.databind.ser.std.StdSerializer;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Azure Cognitive Search record and index definition.
 * Note: once defined, index cannot be modified.
 */
@JsonDeserialize(using = AzureCognitiveSearchRecord.Deserializer.class)
@JsonSerialize(using = AzureCognitiveSearchRecord.Serializer.class)
public final class AzureCognitiveSearchRecord
{
    @SimpleField(isKey = true, isFilterable = false)
    @Nonnull private final String id;

    @SearchableField(analyzerName = "standard.lucene")
    @Nullable private final String text;

    @SearchableField(analyzerName = "standard.lucene")
    @Nullable private final String description;

    @SearchableField(analyzerName = "standard.lucene")
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
    public String getId() { return id; }

    /**
     * Content is stored here.
     * @return Content is stored here,  {@code null} if not set.
     */
    public String getText() {
        return text;
    }

    /**
     * Optional description of the content, e.g. a title. This can be useful when
     * indexing external data without pulling in the entire content.
     * @return Optional description of the content,  {@code null} if not set.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Additional metadata. Currently, this is a String where you could store serialized data as JSON.
     * In future the design might change to allow storing named values and leverage filters.
     * @return Additional metadata,  {@code null} if not set.
     */
    public String getAdditionalMetadata() {
        return additionalMetadata;
    }

    /**
     * Name of the external source, in cases where the content and the Id are referenced to external information.
     * @return Name of the external source, in cases where the content and the Id are referenced to external information,  {@code null} if not set.
     */
    public String getExternalSourceName() {
        return externalSourceName;
    }

    /**
     * Whether the record references external information.
     * @return {@code true} if the record references external information, {@code false} otherwise.
     */
    public boolean isReference() { return isReference; }


    public static class Serializer extends StdSerializer<AzureCognitiveSearchRecord> {
        public Serializer() { this(null); }
        public Serializer(Class<AzureCognitiveSearchRecord> t) { super(t); }

        @Override
        public void serialize(AzureCognitiveSearchRecord azureCognitiveSearchRecord, JsonGenerator jsonGenerator, SerializerProvider serializerProvider) throws IOException {
            jsonGenerator.writeStartObject();
            jsonGenerator.writeStringField("Id", azureCognitiveSearchRecord.getId());
            jsonGenerator.writeStringField("Text", azureCognitiveSearchRecord.getText());
            jsonGenerator.writeStringField("Description", azureCognitiveSearchRecord.getDescription());
            jsonGenerator.writeStringField("AdditionalMetadata", azureCognitiveSearchRecord.getAdditionalMetadata());
            jsonGenerator.writeStringField("ExternalSourceName", azureCognitiveSearchRecord.getExternalSourceName());
            jsonGenerator.writeBooleanField("Reference", azureCognitiveSearchRecord.isReference());
            jsonGenerator.writeEndObject();
        }

    }

    public static class Deserializer extends StdDeserializer<AzureCognitiveSearchRecord> {

        public Deserializer() { this(null); }

        public Deserializer(Class<AzureCognitiveSearchRecord> t) {
            super(t);
        }

        @Override
        public AzureCognitiveSearchRecord deserialize(JsonParser jsonParser, DeserializationContext deserializationContext) throws IOException, JacksonException {
            JsonNode node = jsonParser.getCodec().readTree(jsonParser);
            String id = node.get("Id").asText();
            String text = node.get("Text").asText();
            String description = node.get("Description").asText();
            String additionalMetadata = node.get("AdditionalMetadata").asText();
            String externalSourceName = node.get("ExternalSourceName").asText();
            boolean isReference = node.get("Reference").asBoolean();
            return new AzureCognitiveSearchRecord(id, text, description, additionalMetadata, externalSourceName, isReference);
        }
    }

    // TODO: FieldBuilder.build(AzureCognitiveSearchRecord.class, null) gives an
    // NPE: Cannot invoke "c.f.j.d.i.TypeResoultionContext.resolveType(j.l.r.Type)" because "this._typeContext" is null
    // arising from com.azure.search.documents.implementation.util.FieldBuilder.buildSearchField
    // so we have to do it manually for now.
    static List<SearchField> searchFields() {
        List<SearchField> searchFields = new ArrayList<>();
        Collections.addAll(
                searchFields,
                new SearchField("Id", SearchFieldDataType.STRING)
                        .setKey(true)
                        .setFilterable(false),
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
                new SearchField("Reference", SearchFieldDataType.BOOLEAN)
                        .setFilterable(true)
        );
        return searchFields;
    }
    // TODO: add one more field with the vector, float array, mark it as searchable
}
