// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordPropertyReaderTests
{
    [Fact]
    public void SplitDefinitionsAndVerifyReturnsProperties()
    {
        // Act.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify("testType", this._multiPropsDefinition, true, true);

        // Assert.
        Assert.Equal("Key", properties.KeyProperty.DataModelPropertyName);
        Assert.Equal(2, properties.DataProperties.Count);
        Assert.Equal(2, properties.VectorProperties.Count);
        Assert.Equal("Data1", properties.DataProperties[0].DataModelPropertyName);
        Assert.Equal("Data2", properties.DataProperties[1].DataModelPropertyName);
        Assert.Equal("Vector1", properties.VectorProperties[0].DataModelPropertyName);
        Assert.Equal("Vector2", properties.VectorProperties[1].DataModelPropertyName);
    }

    [Theory]
    [InlineData(false, true, "MultiProps")]
    [InlineData(true, true, "NoKey")]
    [InlineData(true, true, "MultiKeys")]
    [InlineData(false, true, "NoVector")]
    [InlineData(true, true, "NoVector")]
    public void SplitDefinitionsAndVerifyThrowsForInvalidModel(bool supportsMultipleVectors, bool requiresAtLeastOneVector, string definitionName)
    {
        // Arrange.
        var definition = definitionName switch
        {
            "MultiProps" => this._multiPropsDefinition,
            "NoKey" => this._noKeyDefinition,
            "MultiKeys" => this._multiKeysDefinition,
            "NoVector" => this._noVectorDefinition,
            _ => throw new ArgumentException("Invalid definition.")
        };

        // Act & Assert.
        Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.SplitDefinitionAndVerify("testType", definition, supportsMultipleVectors, requiresAtLeastOneVector));
    }

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
        Assert.Equal("Key", properties.KeyProperty.Name);
        Assert.Single(properties.DataProperties);
        Assert.Single(properties.VectorProperties);
        Assert.Equal("Data", properties.DataProperties[0].Name);
        Assert.Equal("Vector", properties.VectorProperties[0].Name);
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
        Assert.Equal("Key", properties.KeyProperty.Name);
        Assert.Equal(2, properties.DataProperties.Count);
        Assert.Equal(2, properties.VectorProperties.Count);
        Assert.Equal("Data1", properties.DataProperties[0].Name);
        Assert.Equal("Data2", properties.DataProperties[1].Name);
        Assert.Equal("Vector1", properties.VectorProperties[0].Name);
        Assert.Equal("Vector2", properties.VectorProperties[1].Name);
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
        var missingKeyDefinition = new VectorStoreRecordDefinition { Properties = [new VectorStoreRecordKeyProperty(propertyName, typeof(string))] };
        var missingDataDefinition = new VectorStoreRecordDefinition { Properties = [new VectorStoreRecordDataProperty(propertyName, typeof(string))] };
        var missingVectorDefinition = new VectorStoreRecordDefinition { Properties = [new VectorStoreRecordVectorProperty(propertyName, typeof(ReadOnlyMemory<float>))] };

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
        Assert.Equal("Key", definition.Properties[0].DataModelPropertyName);
        Assert.Equal("Data1", definition.Properties[1].DataModelPropertyName);
        Assert.Equal("Data2", definition.Properties[2].DataModelPropertyName);
        Assert.Equal("Vector1", definition.Properties[3].DataModelPropertyName);
        Assert.Equal("Vector2", definition.Properties[4].DataModelPropertyName);

        Assert.IsType<VectorStoreRecordKeyProperty>(definition.Properties[0]);
        Assert.IsType<VectorStoreRecordDataProperty>(definition.Properties[1]);
        Assert.IsType<VectorStoreRecordDataProperty>(definition.Properties[2]);
        Assert.IsType<VectorStoreRecordVectorProperty>(definition.Properties[3]);
        Assert.IsType<VectorStoreRecordVectorProperty>(definition.Properties[4]);

        var data1 = (VectorStoreRecordDataProperty)definition.Properties[1];
        var data2 = (VectorStoreRecordDataProperty)definition.Properties[2];

        Assert.True(data1.IsFilterable);
        Assert.False(data2.IsFilterable);

        Assert.True(data1.IsFullTextSearchable);
        Assert.False(data2.IsFullTextSearchable);

        Assert.Equal(typeof(string), data1.PropertyType);
        Assert.Equal(typeof(string), data2.PropertyType);

        var vector1 = (VectorStoreRecordVectorProperty)definition.Properties[3];

        Assert.Equal(4, vector1.Dimensions);
    }

    [Fact]
    public void VerifyPropertyTypesPassForAllowedTypes()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(SinglePropsModel), true);

        // Act.
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, [typeof(string)], "Data");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(this._singlePropsDefinition.Properties.OfType<VectorStoreRecordDataProperty>(), [typeof(string)], "Data");
    }

    [Fact]
    public void VerifyPropertyTypesPassForAllowedEnumerableTypes()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(EnumerablePropsModel), true);

        // Act.
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, [typeof(string)], "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(this._enumerablePropsDefinition.Properties.OfType<VectorStoreRecordDataProperty>(), [typeof(string)], "Data", supportEnumerable: true);
    }

    [Fact]
    public void VerifyPropertyTypesFailsForDisallowedTypes()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(SinglePropsModel), true);

        // Act.
        var ex1 = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, [typeof(int), typeof(float)], "Data"));
        var ex2 = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyReader.VerifyPropertyTypes(this._singlePropsDefinition.Properties.OfType<VectorStoreRecordDataProperty>(), [typeof(int), typeof(float)], "Data"));

        // Assert.
        Assert.Equal("Data properties must be one of the supported types: System.Int32, System.Single. Type of the property 'Data' is System.String.", ex1.Message);
        Assert.Equal("Data properties must be one of the supported types: System.Int32, System.Single. Type of the property 'Data' is System.String.", ex2.Message);
    }

    [Fact]
    public void VerifyStoragePropertyNameMapChecksStorageNameAndFallsBackToPropertyName()
    {
        // Arrange.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify("testType", this._multiPropsDefinition, true, true);

        // Act.
        var storageNameMap = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties);

        // Assert.
        Assert.Equal(5, storageNameMap.Count);

        // From Property Names.
        Assert.Equal("Key", storageNameMap["Key"]);
        Assert.Equal("Data1", storageNameMap["Data1"]);
        Assert.Equal("Vector1", storageNameMap["Vector1"]);
        Assert.Equal("Vector2", storageNameMap["Vector2"]);

        // From storage property name on vector store record data property.
        Assert.Equal("data_2", storageNameMap["Data2"]);
    }

    [Fact]
    public void VerifyGetJsonPropertyNameChecksJsonOptionsAndJsonAttributesAndFallsBackToPropertyName()
    {
        // Arrange.
        var options = new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseUpper };
        var properties = VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), true);
        var allProperties = (new PropertyInfo[] { properties.KeyProperty })
            .Concat(properties.DataProperties)
            .Concat(properties.VectorProperties);

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

    [Fact]
    public void VerifyBuildPropertyNameToJsonPropertyNameMapChecksJsonAttributesAndJsonOptionsAndFallsbackToPropertyNames()
    {
        // Arrange.
        var options = new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseUpper };
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify("testType", this._multiPropsDefinition, true, true);
        var propertiesInfo = VectorStoreRecordPropertyReader.FindProperties(typeof(MultiPropsModel), true);

        // Act.
        var jsonNameMap1 = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(properties, typeof(MultiPropsModel), options);
        var jsonNameMap2 = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(propertiesInfo, typeof(MultiPropsModel), options);

        void assertJsonNameMap(Dictionary<string, string> jsonNameMap)
        {
            Assert.Equal(5, jsonNameMap.Count);

            // From JsonNamingPolicy.
            Assert.Equal("KEY", jsonNameMap["Key"]);
            Assert.Equal("DATA1", jsonNameMap["Data1"]);
            Assert.Equal("DATA2", jsonNameMap["Data2"]);
            Assert.Equal("VECTOR1", jsonNameMap["Vector1"]);

            // From JsonPropertyName attribute.
            Assert.Equal("vector-2", jsonNameMap["Vector2"]);
        };

        // Assert.
        assertJsonNameMap(jsonNameMap1);
        assertJsonNameMap(jsonNameMap2);
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
            new VectorStoreRecordKeyProperty("Key", typeof(string))
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
            new VectorStoreRecordKeyProperty("Key1", typeof(string)),
            new VectorStoreRecordKeyProperty("Key2", typeof(string))
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
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data", typeof(string)),
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>))
        ]
    };

    private sealed class MultiPropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(IsFilterable = true, IsFullTextSearchable = true)]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector(4, IndexKind.Flat, DistanceFunction.DotProductSimilarity)]
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
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "data_2" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>))
        ]
    };

    private sealed class EnumerablePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public IEnumerable<string> EnumerableData { get; set; } = new List<string>();

        [VectorStoreRecordData]
        public string[] ArrayData { get; set; } = Array.Empty<string>();

        [VectorStoreRecordData]
        public List<string> ListData { get; set; } = new List<string>();

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Vector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private readonly VectorStoreRecordDefinition _enumerablePropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("EnumerableData", typeof(IEnumerable<string>)),
            new VectorStoreRecordDataProperty("ArrayData", typeof(string[])),
            new VectorStoreRecordDataProperty("ListData", typeof(List<string>)),
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>))
        ]
    };

#pragma warning restore CA1812 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
}
