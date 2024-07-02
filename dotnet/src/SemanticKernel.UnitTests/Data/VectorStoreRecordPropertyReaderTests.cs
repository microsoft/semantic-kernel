// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordPropertyReaderTests
{
    [Theory]
    [InlineData(true, false)]
    [InlineData(false, false)]
    [InlineData(true, true)]
    [InlineData(false, true)]
    public void FindPropertiesCanFindAllPropertiesOnSinglePropsModel(bool supportsMultipleVectors, bool useConfig)
    {
        // Act.
        var properties = useConfig ?
            VectorStoreRecordPropertyReader.FindProperties(typeof(SinglePropsModel), this._singlePropsDefinition, supportsMultipleVectors) :
            VectorStoreRecordPropertyReader.FindProperties(typeof(SinglePropsModel), supportsMultipleVectors);

        // Assert.
        Assert.Equal("Key", properties.keyProperty.Name);
        Assert.Single(properties.dataProperties);
        Assert.Single(properties.vectorProperties);
        Assert.Equal("Data", properties.dataProperties[0].Name);
        Assert.Equal("Vector", properties.vectorProperties[0].Name);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void FindPropertiesCanFindAllPropertiesOnMultiPropsModel(bool useConfig)
    {
        // Act.
        var properties = useConfig ?
            VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), this._multiPropsDefinition, true) :
            VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), true);

        // Assert.
        Assert.Equal("Key", properties.keyProperty.Name);
        Assert.Equal(2, properties.dataProperties.Count);
        Assert.Equal(2, properties.vectorProperties.Count);
        Assert.Equal("Data1", properties.dataProperties[0].Name);
        Assert.Equal("Data2", properties.dataProperties[1].Name);
        Assert.Equal("Vector1", properties.vectorProperties[0].Name);
        Assert.Equal("Vector2", properties.vectorProperties[1].Name);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void FindPropertiesThrowsForMultipleVectorsWithSingleVectorSupport(bool useConfig)
    {
        // Act.
        var ex = useConfig ?
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), this._multiPropsDefinition, false)) :
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), false));

        // Assert.
        var expectedMessage = useConfig ?
            "Multiple vector properties configured for type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+MultiPropsModel while only one is supported." :
            "Multiple vector properties found on type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+MultiPropsModel while only one is supported.";
        Assert.Equal(expectedMessage, ex.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void FindPropertiesThrowsOnMultipleKeyProperties(bool useConfig)
    {
        // Act.
        var ex = useConfig ?
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(MultiKeysModel), this._multiKeysDefinition, true)) :
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(MultiKeysModel), true));

        // Assert.
        var expectedMessage = useConfig ?
            "Multiple key properties configured for type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+MultiKeysModel." :
            "Multiple key properties found on type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+MultiKeysModel.";
        Assert.Equal(expectedMessage, ex.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void FindPropertiesThrowsOnNoKeyProperty(bool useConfig)
    {
        // Act.
        var ex = useConfig ?
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(NoKeyModel), this._noKeyDefinition, true)) :
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(NoKeyModel), true));

        // Assert.
        var expectedMessage = useConfig ?
            "No key property configured for type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+NoKeyModel." :
            "No key property found on type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+NoKeyModel.";
        Assert.Equal(expectedMessage, ex.Message);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void FindPropertiesThrowsOnNoVectorPropertyWithSingleVectorSupport(bool useConfig)
    {
        // Act.
        var ex = useConfig ?
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(NoVectorModel), this._noVectorDefinition, false)) :
            Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(NoVectorModel), false));

        // Assert.
        var expectedMessage = useConfig ?
            "No vector property configured for type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+NoVectorModel." :
            "No vector property found on type SemanticKernel.UnitTests.Data.VectorStoreRecordPropertyReaderTests+NoVectorModel.";
        Assert.Equal(expectedMessage, ex.Message);
    }

    [Theory]
    [InlineData("Key", "MissingKey")]
    [InlineData("Data", "MissingData")]
    [InlineData("Vector", "MissingVector")]
    public void FindPropertiesUsingConfigThrowsForNotFoundProperties(string propertyType, string propertyName)
    {
        var missingKeyDefinition = new VectorStoreRecordDefinition { Properties = [new VectorStoreRecordKeyProperty(propertyName)] };
        var missingDataDefinition = new VectorStoreRecordDefinition { Properties = [new VectorStoreRecordDataProperty(propertyName)] };
        var missingVectorDefinition = new VectorStoreRecordDefinition { Properties = [new VectorStoreRecordVectorProperty(propertyName)] };

        var definition = propertyType switch
        {
            "Key" => missingKeyDefinition,
            "Data" => missingDataDefinition,
            "Vector" => missingVectorDefinition,
            _ => throw new ArgumentException("Invalid property type.")
        };

        Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.FindProperties(typeof(NoKeyModel), definition, false));
    }

    [Fact]
    public void CreateVectorStoreRecordDefinitionFromTypeConvertsAllProps()
    {
        // Act.
        var definition = VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(MultiPropsModel), true);

        // Assert.
        Assert.Equal(5, definition.Properties.Count);
        Assert.Equal("Key", definition.Properties[0].PropertyName);
        Assert.Equal("Data1", definition.Properties[1].PropertyName);
        Assert.Equal("Data2", definition.Properties[2].PropertyName);
        Assert.Equal("Vector1", definition.Properties[3].PropertyName);
        Assert.Equal("Vector2", definition.Properties[4].PropertyName);

        Assert.IsType<VectorStoreRecordKeyProperty>(definition.Properties[0]);
        Assert.IsType<VectorStoreRecordDataProperty>(definition.Properties[1]);
        Assert.IsType<VectorStoreRecordDataProperty>(definition.Properties[2]);
        Assert.IsType<VectorStoreRecordVectorProperty>(definition.Properties[3]);
        Assert.IsType<VectorStoreRecordVectorProperty>(definition.Properties[4]);

        var data1 = (VectorStoreRecordDataProperty)definition.Properties[1];
        var data2 = (VectorStoreRecordDataProperty)definition.Properties[2];

        Assert.True(data1.HasEmbedding);
        Assert.False(data2.HasEmbedding);

        Assert.Equal("Vector1", data1.EmbeddingPropertyName);
    }

    [Fact]
    public void VerifyPropertyTypesPassForAllowedTypes()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(SinglePropsModel), true);

        // Act.
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.dataProperties, [typeof(string)], "Data");
    }

    [Fact]
    public void VerifyPropertyTypesFailsForDisallowedTypes()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(SinglePropsModel), true);

        // Act.
        var ex = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.dataProperties, [typeof(int), typeof(float)], "Data"));

        // Assert.
        Assert.Equal("Data properties must be one of the supported types: System.Int32, System.Single. Type of Data is System.String.", ex.Message);
    }

    [Fact]
    public void VerifyStoragePropertyNameMapChecksAttributeAndFallsBackToPropertyName()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), true);

        // Act.
        var storageNameMap = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties, this._multiPropsDefinition);

        // Assert.
        Assert.Equal(5, storageNameMap.Count);

        // From Property Names.
        Assert.Equal("Key", storageNameMap["Key"]);
        Assert.Equal("Data1", storageNameMap["Data1"]);
        Assert.Equal("Vector1", storageNameMap["Vector1"]);
        Assert.Equal("Vector2", storageNameMap["Vector2"]);

        // From storage property name on vector store record property attribute.
        Assert.Equal("data_2", storageNameMap["Data2"]);
    }

    [Fact]
    public void VerifyGetJsonPropertyNameChecksJsonOptionsAndJsonAttributesAndFallsBackToPropertyName()
    {
        // Arrange.
        var options = new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseUpper };
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), true);
        var allProperties = (new PropertyInfo[] { properties.keyProperty })
            .Concat(properties.dataProperties)
            .Concat(properties.vectorProperties);

        // Act.
        var jsonNameMap = allProperties
            .Select(p => new { PropertyName = p.Name, JsonName = VectorStoreRecordPropertyReader.GetJsonPropertyName(options, p) })
            .ToDictionary(p => p.PropertyName, p => p.JsonName);

        // Assert.
        Assert.Equal(5, jsonNameMap.Count);

        // From JsonNamingPolicy.
        Assert.Equal("KEY", jsonNameMap["Key"]);
        Assert.Equal("DATA1", jsonNameMap["Data1"]);
        Assert.Equal("DATA2", jsonNameMap["Data2"]);
        Assert.Equal("VECTOR1", jsonNameMap["Vector1"]);

        // From JsonPropertyName attribute.
        Assert.Equal("vector-2", jsonNameMap["Vector2"]);
    }

#pragma warning disable CA1812 // Invalid unused classes error, since I am using these for testing purposes above.
    private sealed class NoKeyModel
    {
    }

    private readonly VectorStoreRecordDefinition _noKeyDefinition = new();

    private sealed class NoVectorModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;
    }

    private readonly VectorStoreRecordDefinition _noVectorDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key")
        ]
    };

    private sealed class MultiKeysModel
    {
        [VectorStoreRecordKey]
        public string Key1 { get; set; } = string.Empty;

        [VectorStoreRecordKey]
        public string Key2 { get; set; } = string.Empty;
    }

    private readonly VectorStoreRecordDefinition _multiKeysDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key1"),
            new VectorStoreRecordKeyProperty("Key2")
        ]
    };

    private sealed class SinglePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Vector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key"),
            new VectorStoreRecordDataProperty("Data"),
            new VectorStoreRecordVectorProperty("Vector")
        ]
    };

    private sealed class MultiPropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(HasEmbedding = true, EmbeddingPropertyName = "Vector1")]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Vector1 { get; set; }

        [VectorStoreRecordVector]
        [JsonPropertyName("vector-2")]
        public ReadOnlyMemory<float> Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private readonly VectorStoreRecordDefinition _multiPropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key"),
            new VectorStoreRecordDataProperty("Data1") { HasEmbedding = true, EmbeddingPropertyName = "Vector1" },
            new VectorStoreRecordDataProperty("Data2") { StoragePropertyName = "data_2" },
            new VectorStoreRecordVectorProperty("Vector1"),
            new VectorStoreRecordVectorProperty("Vector2")
        ]
    };
#pragma warning restore CA1812 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
}
