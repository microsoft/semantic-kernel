// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import java.time.ZonedDateTime;
import java.util.Arrays;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

class MemoryRecordTests {
    private static final boolean _isReference = false;
    private static final String _id = "Id";
    private static final String _text = "text";
    private static final String _description = "description";
    private static final String _externalSourceName = "externalSourceName";
    private static final String _additionalMetadata = "value";
    private static final Embedding _embedding = new Embedding(Arrays.asList(1f, 2f, 3f));

    @Test
    void itCanBeConstructedFromMetadataAndVector() {
        // Arrange
        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        _isReference,
                        _id,
                        _text,
                        _description,
                        _externalSourceName,
                        _additionalMetadata);

        // Act
        MemoryRecord memoryRecord =
                new MemoryRecord(metadata, _embedding, "key", ZonedDateTime.now());

        // Assert
        assertEquals(_isReference, memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals(_text, memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_embedding.getVector(), memoryRecord.getEmbedding().getVector());
    }

    @Test
    void itCanBeConstructedFromMetadata() {
        // Arrange
        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        _isReference,
                        _id,
                        _text,
                        _description,
                        _externalSourceName,
                        _additionalMetadata);

        // Act
        MemoryRecord memoryRecord =
                MemoryRecord.fromMetadata(metadata, _embedding, "key", ZonedDateTime.now());

        // Assert
        assertEquals(_isReference, memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals(_text, memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_embedding.getVector(), memoryRecord.getEmbedding().getVector());
    }

    @Test
    void itCanBeConstructedFromMetadataAndNulls() {
        // Arrange
        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        _isReference,
                        _id,
                        _text,
                        _description,
                        _externalSourceName,
                        _additionalMetadata);

        // Act
        MemoryRecord memoryRecord = MemoryRecord.fromMetadata(metadata, null, null, null);

        // Assert
        assertEquals(_isReference, memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals(_text, memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(Embedding.empty().getVector(), memoryRecord.getEmbedding().getVector());
        assertEquals("", memoryRecord.getKey());
        assertEquals(null, memoryRecord.getTimestamp());
    }

    @Test
    void itCanBeCreatedToRepresentLocalData() {
        // Arrange
        MemoryRecord memoryRecord =
                MemoryRecord.localRecord(_id, _text, _description, _embedding, null, null, null);

        // Assert
        assertFalse(memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals(_text, memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals("", memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_embedding.getVector(), memoryRecord.getEmbedding().getVector());
    }

    @Test
    void itCanBeCreatedToRepresentExternalData() {
        // Arrange
        MemoryRecord memoryRecord =
                MemoryRecord.referenceRecord(
                        _id, _externalSourceName, _description, _embedding, null, null, null);

        // Assert
        assertTrue(memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals("", memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_embedding.getVector(), memoryRecord.getEmbedding().getVector());
    }

    @Test
    @Disabled("fromJsonMetadata is not implemented")
    void itCanBeCreatedFromSerializedMetadata() {
        // Arrange
        String jsonString =
                "{"
                        + "\"is_reference\" : false"
                        + "\"id\" : \"Id\""
                        + "\"text\" : \"text\""
                        + "\"description\" : \"description\""
                        + "\"external_source_name\" : \"externalSourceName\""
                        + "\"additional_metadata\" : \"value\""
                        + "}";

        // Act
        MemoryRecord memoryRecord = null; // MemoryRecord.fromJsonMetadata(jsonString, _embedding);

        // Assert
        assertEquals(_isReference, memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals(_text, memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_additionalMetadata, memoryRecord.getMetadata().getAdditionalMetadata());
        assertEquals(_embedding.getVector(), memoryRecord.getEmbedding().getVector());
    }

    @Test
    @Disabled("JSON deserialization is not implemented")
    void itCanBeDeserializedFromJson() {
        // Arrange
        String jsonString =
                "{"
                        + "  \"metadata\" : {"
                        + "    \"is_reference\" : false"
                        + "    \"id\" : \"Id\""
                        + "    \"text\" : \"text\""
                        + "    \"description\" : \"description\""
                        + "    \"external_source_name\" : \"externalSourceName\""
                        + "    \"additional_metadata\" : \"value\""
                        + "  }"
                        + "  \"embedding\" : {"
                        + "    \"vector\" : [ 1, 2, 3 ]"
                        + "  }"
                        + "}";

        // Act
        MemoryRecord memoryRecord = null; // JsonSerializer.Deserialize<MemoryRecord>(jsonString);

        // Assert
        assertNotNull(memoryRecord);
        assertEquals(_isReference, memoryRecord.getMetadata().isReference());
        assertEquals(_id, memoryRecord.getMetadata().getId());
        assertEquals(_text, memoryRecord.getMetadata().getText());
        assertEquals(_description, memoryRecord.getMetadata().getDescription());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_externalSourceName, memoryRecord.getMetadata().getExternalSourceName());
        assertEquals(_embedding.getVector(), memoryRecord.getEmbedding().getVector());
    }

    @Test
    @Disabled("JSON serialization is not implemented")
    void itCanBeSerialized() {
        // Arrange
        String jsonString =
                "{"
                        + "  \"metadata\" : {"
                        + "    \"is_reference\" : false"
                        + "    \"id\" : \"Id\""
                        + "    \"text\" : \"text\""
                        + "    \"description\" : \"description\""
                        + "    \"external_source_name\" : \"externalSourceName\""
                        + "    \"additional_metadata\" : \"value\""
                        + "  }"
                        + "  \"embedding\" : {"
                        + "    \"vector\" : [ 1, 2, 3 ]"
                        + "  }"
                        + "\"key\" : \"key\""
                        + "\"timestamp\": null"
                        + "}";

        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        _isReference,
                        _id,
                        _text,
                        _description,
                        _externalSourceName,
                        _additionalMetadata);
        MemoryRecord memoryRecord =
                new MemoryRecord(metadata, _embedding, "key", ZonedDateTime.now());

        // Act
        String serializedRecord = null; // JsonSerializer.Serialize(memoryRecord);
        jsonString = jsonString.replaceAll("\n", "");
        jsonString = jsonString.replaceAll(" ", "");

        // Assert
        assertEquals(jsonString, serializedRecord);
    }

    @Test
    @Disabled("JSON serialization is not implemented")
    void itsMetadataCanBeSerialized() {
        // Arrange
        String jsonString =
                "{"
                        + "  \"is_reference\" : false"
                        + "  \"id\" : \"Id\""
                        + "  \"text\" : \"text\""
                        + "  \"description\" : \"description\""
                        + "  \"external_source_name\" : \"externalSourceName\""
                        + "  \"additional_metadata\" : \"value\""
                        + "}";

        MemoryRecordMetadata metadata =
                new MemoryRecordMetadata(
                        _isReference,
                        _id,
                        _text,
                        _description,
                        _externalSourceName,
                        _additionalMetadata);
        MemoryRecord memoryRecord =
                new MemoryRecord(metadata, _embedding, "key", ZonedDateTime.now());

        // Act
        String serializedMetadata = // memoryRecord.getSerializedMetadata();
                jsonString = jsonString.replaceAll("\n", "");
        jsonString = jsonString.replaceAll(" ", "");

        // Assert
        assertEquals(jsonString, serializedMetadata);
    }
}
