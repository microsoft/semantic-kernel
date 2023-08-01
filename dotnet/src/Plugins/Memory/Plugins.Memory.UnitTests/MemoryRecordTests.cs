// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Plugins.Memory;
using Xunit;

namespace SemanticKernel.Plugins.Memory.UnitTests;

public class MemoryRecordTests
{
    private readonly bool _isReference = false;
    private readonly string _id = "Id";
    private readonly string _text = "text";
    private readonly string _description = "description";
    private readonly string _externalSourceName = "externalSourceName";
    private readonly string _additionalMetadata = "value";
    private readonly Embedding<float> _embedding = new(new float[] { 1, 2, 3 });

    [Fact]
    public void ItCanBeConstructedFromMetadataAndVector()
    {
        // Arrange
        var metadata = new MemoryRecordMetadata(
            isReference: this._isReference,
            id: this._id,
            text: this._text,
            description: this._description,
            externalSourceName: this._externalSourceName,
            additionalMetadata: this._additionalMetadata);

        // Act
        var memoryRecord = new MemoryRecord(metadata, this._embedding, "key", DateTimeOffset.Now);

        // Assert
        Assert.Equal(this._isReference, memoryRecord.Metadata.IsReference);
        Assert.Equal(this._id, memoryRecord.Metadata.Id);
        Assert.Equal(this._text, memoryRecord.Metadata.Text);
        Assert.Equal(this._description, memoryRecord.Metadata.Description);
        Assert.Equal(this._externalSourceName, memoryRecord.Metadata.ExternalSourceName);
        Assert.Equal(this._embedding.Vector, memoryRecord.Embedding.Vector);
    }

    [Fact]
    public void ItCanBeCreatedToRepresentLocalData()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        // Assert
        Assert.False(memoryRecord.Metadata.IsReference);
        Assert.Equal(this._id, memoryRecord.Metadata.Id);
        Assert.Equal(this._text, memoryRecord.Metadata.Text);
        Assert.Equal(this._description, memoryRecord.Metadata.Description);
        Assert.Equal(string.Empty, memoryRecord.Metadata.ExternalSourceName);
        Assert.Equal(this._embedding.Vector, memoryRecord.Embedding.Vector);
    }

    [Fact]
    public void ItCanBeCreatedToRepresentExternalData()
    {
        // Arrange
        var memoryRecord = MemoryRecord.ReferenceRecord(
            externalId: this._id,
            sourceName: this._externalSourceName,
            description: this._description,
            embedding: this._embedding);

        // Assert
        Assert.True(memoryRecord.Metadata.IsReference);
        Assert.Equal(this._id, memoryRecord.Metadata.Id);
        Assert.Equal(string.Empty, memoryRecord.Metadata.Text);
        Assert.Equal(this._description, memoryRecord.Metadata.Description);
        Assert.Equal(this._externalSourceName, memoryRecord.Metadata.ExternalSourceName);
        Assert.Equal(this._embedding.Vector, memoryRecord.Embedding.Vector);
    }

    [Fact]
    public void ItCanBeCreatedFromSerializedMetadata()
    {
        // Arrange
        string jsonString = @"{
            ""is_reference"": false,
            ""id"": ""Id"",
            ""text"": ""text"",
            ""description"": ""description"",
            ""external_source_name"": ""externalSourceName"",
            ""additional_metadata"": ""value""
        }";

        // Act
        var memoryRecord = MemoryRecord.FromJsonMetadata(jsonString, this._embedding);

        // Assert
        Assert.Equal(this._isReference, memoryRecord.Metadata.IsReference);
        Assert.Equal(this._id, memoryRecord.Metadata.Id);
        Assert.Equal(this._text, memoryRecord.Metadata.Text);
        Assert.Equal(this._description, memoryRecord.Metadata.Description);
        Assert.Equal(this._externalSourceName, memoryRecord.Metadata.ExternalSourceName);
        Assert.Equal(this._additionalMetadata, memoryRecord.Metadata.AdditionalMetadata);
        Assert.Equal(this._embedding.Vector, memoryRecord.Embedding.Vector);
    }

    [Fact]
    public void ItCanBeDeserializedFromJson()
    {
        // Arrange
        string jsonString = @"{
            ""metadata"": {
                ""is_reference"": false,
                ""id"": ""Id"",
                ""text"": ""text"",
                ""description"": ""description"",
                ""external_source_name"": ""externalSourceName"",
                ""additional_metadata"": ""value""
            },
            ""embedding"": {
                ""vector"": [
                    1,
                    2,
                    3
                ]
            }
        }";

        // Act
        var memoryRecord = JsonSerializer.Deserialize<MemoryRecord>(jsonString);

        // Assert
        Assert.NotNull(memoryRecord);
        Assert.Equal(this._isReference, memoryRecord.Metadata.IsReference);
        Assert.Equal(this._id, memoryRecord.Metadata.Id);
        Assert.Equal(this._text, memoryRecord.Metadata.Text);
        Assert.Equal(this._description, memoryRecord.Metadata.Description);
        Assert.Equal(this._externalSourceName, memoryRecord.Metadata.ExternalSourceName);
        Assert.Equal(this._externalSourceName, memoryRecord.Metadata.ExternalSourceName);
        Assert.Equal(this._embedding.Vector, memoryRecord.Embedding.Vector);
    }

    [Fact]
    public void ItCanBeSerialized()
    {
        // Arrange
        string jsonString = @"{
            ""embedding"": {
                ""vector"": [
                    1,
                    2,
                    3
                ]
            },
            ""metadata"": {
                ""is_reference"": false,
                ""external_source_name"": ""externalSourceName"",
                ""id"": ""Id"",
                ""description"": ""description"",
                ""text"": ""text"",
                ""additional_metadata"": ""value""
            },
            ""key"": ""key"",
            ""timestamp"": null
        }";
        var metadata = new MemoryRecordMetadata(
            isReference: this._isReference,
            id: this._id,
            text: this._text,
            description: this._description,
            externalSourceName: this._externalSourceName,
            additionalMetadata: this._additionalMetadata);
        var memoryRecord = new MemoryRecord(metadata, this._embedding, "key");

        // Act
        string serializedRecord = JsonSerializer.Serialize(memoryRecord);
        jsonString = jsonString.Replace("\n", string.Empty, StringComparison.Ordinal);
        jsonString = jsonString.Replace(" ", string.Empty, StringComparison.Ordinal);

        // Assert
        Assert.Equal(jsonString, serializedRecord);
    }

    [Fact]
    public void ItsMetadataCanBeSerialized()
    {
        // Arrange
        string jsonString = @"{
                ""is_reference"": false,
                ""external_source_name"": ""externalSourceName"",
                ""id"": ""Id"",
                ""description"": ""description"",
                ""text"": ""text"",
                ""additional_metadata"": ""value""
            }";

        var metadata = new MemoryRecordMetadata(
            isReference: this._isReference,
            id: this._id,
            text: this._text,
            description: this._description,
            externalSourceName: this._externalSourceName,
            additionalMetadata: this._additionalMetadata);
        var memoryRecord = new MemoryRecord(metadata, this._embedding, "key");

        // Act
        string serializedMetadata = memoryRecord.GetSerializedMetadata();
        jsonString = jsonString.Replace("\n", string.Empty, StringComparison.Ordinal);
        jsonString = jsonString.Replace(" ", string.Empty, StringComparison.Ordinal);

        // Assert
        Assert.Equal(jsonString, serializedMetadata);
    }
}
