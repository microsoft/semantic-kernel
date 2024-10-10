// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.Linq;
using System.Reflection;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
using System.Linq;
using System.Reflection;
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordPropertyReaderTests
{
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    [Theory]
    [MemberData(nameof(NoKeyTypeAndDefinitionCombos))]
    public void ConstructorFailsForNoKey(Type type, VectorStoreRecordDefinition? definition)
    {
        // Act & Assert.
        var exception = Assert.Throws<ArgumentException>(() => new VectorStoreRecordPropertyReader(type, definition, null));
        Assert.Equal("No key property found on type NoKeyModel or the provided VectorStoreRecordDefinition.", exception.Message);
    }

    [Theory]
    [MemberData(nameof(MultiKeysTypeAndDefinitionCombos))]
    public void ConstructorSucceedsForSupportedMultiKeys(Type type, VectorStoreRecordDefinition? definition)
    {
        // Act & Assert.
        var sut = new VectorStoreRecordPropertyReader(type, definition, new VectorStoreRecordPropertyReaderOptions { SupportsMultipleKeys = true });
    }

    [Theory]
    [MemberData(nameof(MultiKeysTypeAndDefinitionCombos))]
    public void ConstructorFailsForUnsupportedMultiKeys(Type type, VectorStoreRecordDefinition? definition)
    {
        // Act & Assert.
        var exception = Assert.Throws<ArgumentException>(() => new VectorStoreRecordPropertyReader(type, definition, new VectorStoreRecordPropertyReaderOptions { SupportsMultipleKeys = false }));
        Assert.Equal("Multiple key properties found on type MultiKeysModel or the provided VectorStoreRecordDefinition.", exception.Message);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void ConstructorSucceedsForSupportedMultiVectors(Type type, VectorStoreRecordDefinition? definition)
    {
        // Act & Assert.
        var sut = new VectorStoreRecordPropertyReader(type, definition, new VectorStoreRecordPropertyReaderOptions { SupportsMultipleVectors = true });
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void ConstructorFailsForUnsupportedMultiVectors(Type type, VectorStoreRecordDefinition? definition)
    {
        // Act & Assert.
        var exception = Assert.Throws<ArgumentException>(() => new VectorStoreRecordPropertyReader(type, definition, new VectorStoreRecordPropertyReaderOptions { SupportsMultipleVectors = false }));
        Assert.Equal("Multiple vector properties found on type MultiPropsModel or the provided VectorStoreRecordDefinition while only one is supported.", exception.Message);
    }

    [Theory]
    [MemberData(nameof(NoVectorsTypeAndDefinitionCombos))]
    public void ConstructorFailsForUnsupportedNoVectors(Type type, VectorStoreRecordDefinition? definition)
    {
        // Act & Assert.
        var exception = Assert.Throws<ArgumentException>(() => new VectorStoreRecordPropertyReader(type, definition, new VectorStoreRecordPropertyReaderOptions { RequiresAtLeastOneVector = true }));
        Assert.Equal("No vector property found on type NoVectorModel or the provided VectorStoreRecordDefinition while at least one is required.", exception.Message);
    }

    [Theory]
    [MemberData(nameof(TypeAndDefinitionCombos))]
    public void CanGetDefinition(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.RecordDefinition;

        // Assert.
        Assert.NotNull(actual);
    }

    [Theory]
    [MemberData(nameof(TypeAndDefinitionCombos))]
    public void CanGetKeyPropertyInfo(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertyInfo;

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal("Key", actual.Name);
        Assert.Equal(typeof(string), actual.PropertyType);
    }

    [Theory]
    [MemberData(nameof(TypeAndDefinitionCombos))]
    public void CanGetKeyPropertiesInfo(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertiesInfo;

        // Assert.
        Assert.NotNull(actual);
        Assert.Single(actual);
        Assert.Equal("Key", actual[0].Name);
        Assert.Equal(typeof(string), actual[0].PropertyType);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetDataPropertiesInfo(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.DataPropertiesInfo;

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal("Data1", actual[0].Name);
        Assert.Equal(typeof(string), actual[0].PropertyType);
        Assert.Equal("Data2", actual[1].Name);
        Assert.Equal(typeof(string), actual[1].PropertyType);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetVectorPropertiesInfo(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.VectorPropertiesInfo;

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal("Vector1", actual[0].Name);
        Assert.Equal(typeof(ReadOnlyMemory<float>), actual[0].PropertyType);
        Assert.Equal("Vector2", actual[1].Name);
        Assert.Equal(typeof(ReadOnlyMemory<float>), actual[1].PropertyType);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetFirstVectorPropertyName(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.FirstVectorPropertyName;

        // Assert.
        Assert.Equal("Vector1", actual);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetFirstVectorPropertyInfo(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.FirstVectorPropertyInfo;

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal("Vector1", actual.Name);
        Assert.Equal(typeof(ReadOnlyMemory<float>), actual.PropertyType);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetKeyPropertyName(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertyName;

        // Assert.
        Assert.Equal("Key", actual);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetKeyPropertyStoragePropertyNameWithoutOverride(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertyStoragePropertyName;

        // Assert.
        Assert.Equal("Key", actual);
    }

    [Theory]
    [MemberData(nameof(StorageNamesPropsTypeAndDefinitionCombos))]
    public void CanGetKeyPropertyStoragePropertyNameWithOverride(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertyStoragePropertyName;

        // Assert.
        Assert.Equal("storage_key", actual);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetDataPropertyStoragePropertyNameWithOverrideMix(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.DataPropertyStoragePropertyNames;

        // Assert.
        Assert.Equal("Data1", actual[0]);
        Assert.Equal("storage_data2", actual[1]);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetVectorPropertyStoragePropertyNameWithOverrideMix(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.VectorPropertyStoragePropertyNames;

        // Assert.
        Assert.Equal("Vector1", actual[0]);
        Assert.Equal("storage_vector2", actual[1]);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetKeyPropertyJsonNameWithoutOverride(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertyJsonName;

        // Assert.
        Assert.Equal("Key", actual);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void CanGetKeyPropertyJsonNameWithSerializerSettings(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, new()
        {
            JsonSerializerOptions = new JsonSerializerOptions()
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseUpper
            }
        });

        // Act.
        var actual = sut.KeyPropertyJsonName;

        // Assert.
        Assert.Equal("KEY", actual);
    }

    [Theory]
    [MemberData(nameof(StorageNamesPropsTypeAndDefinitionCombos))]
    public void CanGetKeyPropertyJsonNameWithOverride(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.KeyPropertyJsonName;

        // Assert.
        Assert.Equal("json_key", actual);
    }

    [Theory]
    [MemberData(nameof(StorageNamesPropsTypeAndDefinitionCombos))]
    public void CanGetDataPropertyJsonNameWithOverride(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.DataPropertyJsonNames;

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal("json_data1", actual[0]);
        Assert.Equal("json_data2", actual[1]);
    }

    [Theory]
    [MemberData(nameof(StorageNamesPropsTypeAndDefinitionCombos))]
    public void CanGetVectorPropertyJsonNameWithOverride(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act.
        var actual = sut.VectorPropertyJsonNames;

        // Assert.
        Assert.NotNull(actual);
        Assert.Single(actual);
        Assert.Equal("json_vector", actual[0]);
    }

    [Theory]
    [MemberData(nameof(TypeAndDefinitionCombos))]
    public void VerifyKeyPropertiesPassesForAllowedTypes(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var allowedTypes = new HashSet<Type> { typeof(string), typeof(int) };

        // Act.
        sut.VerifyKeyProperties(allowedTypes);
    }

    [Theory]
    [MemberData(nameof(TypeAndDefinitionCombos))]
    public void VerifyKeyPropertiesFailsForDisallowedTypes(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var allowedTypes = new HashSet<Type> { typeof(long) };

        // Act.
        var exception = Assert.Throws<ArgumentException>(() => sut.VerifyKeyProperties(allowedTypes));
        Assert.Equal("Key properties must be one of the supported types: System.Int64. Type of the property 'Key' is System.String.", exception.Message);
    }

    [Theory]
    [MemberData(nameof(EnumerablePropsTypeAndDefinitionCombos))]
    public void VerifyDataPropertiesPassesForAllowedEnumerableTypes(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var allowedTypes = new HashSet<Type> { typeof(string), typeof(int) };

        // Act.
        sut.VerifyDataProperties(allowedTypes, true);
    }

    [Theory]
    [MemberData(nameof(EnumerablePropsTypeAndDefinitionCombos))]
    public void VerifyDataPropertiesFailsForDisallowedEnumerableTypes(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var allowedTypes = new HashSet<Type> { typeof(string), typeof(int) };

        // Act.
        var exception = Assert.Throws<ArgumentException>(() => sut.VerifyDataProperties(allowedTypes, false));
        Assert.Equal("Data properties must be one of the supported types: System.String, System.Int32. Type of the property 'EnumerableData' is System.Collections.Generic.IEnumerable`1[[System.String, System.Private.CoreLib, Version=8.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].", exception.Message);
    }

    [Theory]
    [MemberData(nameof(EnumerablePropsTypeAndDefinitionCombos))]
    public void VerifyVectorPropertiesPassesForAllowedEnumerableTypes(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var allowedTypes = new HashSet<Type> { typeof(ReadOnlyMemory<float>) };

        // Act.
        sut.VerifyVectorProperties(allowedTypes);
    }

    [Theory]
    [MemberData(nameof(EnumerablePropsTypeAndDefinitionCombos))]
    public void VerifyVectorPropertiesFailsForDisallowedEnumerableTypes(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var allowedTypes = new HashSet<Type> { typeof(ReadOnlyMemory<double>) };

        // Act.
        var exception = Assert.Throws<ArgumentException>(() => sut.VerifyVectorProperties(allowedTypes));
        Assert.Equal("Vector properties must be one of the supported types: System.ReadOnlyMemory`1[[System.Double, System.Private.CoreLib, Version=8.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]]. Type of the property 'Vector' is System.ReadOnlyMemory`1[[System.Single, System.Private.CoreLib, Version=8.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]].", exception.Message);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void GetStoragePropertyNameReturnsStorageNameWithFallback(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Equal("Data1", sut.GetStoragePropertyName("Data1"));
        Assert.Equal("storage_data2", sut.GetStoragePropertyName("Data2"));
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void GetJsonPropertyNameReturnsJsonWithFallback(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Equal("Data1", sut.GetJsonPropertyName("Data1"));
        Assert.Equal("json_data2", sut.GetJsonPropertyName("Data2"));
    }

    public static IEnumerable<object?[]> NoKeyTypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(NoKeyModel), s_noKeyDefinition };
        yield return new object?[] { typeof(NoKeyModel), null };
    }

    public static IEnumerable<object?[]> NoVectorsTypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(NoVectorModel), s_noVectorDefinition };
        yield return new object?[] { typeof(NoVectorModel), null };
    }

    public static IEnumerable<object?[]> MultiKeysTypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(MultiKeysModel), s_multiKeysDefinition };
        yield return new object?[] { typeof(MultiKeysModel), null };
    }

    public static IEnumerable<object?[]> TypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(SinglePropsModel), s_singlePropsDefinition };
        yield return new object?[] { typeof(SinglePropsModel), null };
        yield return new object?[] { typeof(MultiPropsModel), s_multiPropsDefinition };
        yield return new object?[] { typeof(MultiPropsModel), null };
        yield return new object?[] { typeof(EnumerablePropsModel), s_enumerablePropsDefinition };
        yield return new object?[] { typeof(EnumerablePropsModel), null };
    }

    public static IEnumerable<object?[]> MultiPropsTypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(MultiPropsModel), s_multiPropsDefinition };
        yield return new object?[] { typeof(MultiPropsModel), null };
    }

    public static IEnumerable<object?[]> StorageNamesPropsTypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(StorageNamesPropsModel), s_storageNamesPropsDefinition };
        yield return new object?[] { typeof(StorageNamesPropsModel), null };
    }

    public static IEnumerable<object?[]> EnumerablePropsTypeAndDefinitionCombos()
    {
        yield return new object?[] { typeof(EnumerablePropsModel), s_enumerablePropsDefinition };
        yield return new object?[] { typeof(EnumerablePropsModel), null };
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    }

#pragma warning disable CA1812 // Invalid unused classes error, since I am using these for testing purposes above.

    private sealed class NoKeyModel
    {
    }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VectorStoreRecordDefinition _noKeyDefinition = new();
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VectorStoreRecordDefinition _noKeyDefinition = new();
=======
    private static readonly VectorStoreRecordDefinition s_noKeyDefinition = new();
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static readonly VectorStoreRecordDefinition s_noKeyDefinition = new();
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

    private sealed class NoVectorModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;
    }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VectorStoreRecordDefinition _noVectorDefinition = new()
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VectorStoreRecordDefinition _noVectorDefinition = new()
=======
    private static readonly VectorStoreRecordDefinition s_noVectorDefinition = new()
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static readonly VectorStoreRecordDefinition s_noVectorDefinition = new()
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VectorStoreRecordDefinition _multiKeysDefinition = new()
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VectorStoreRecordDefinition _multiKeysDefinition = new()
=======
    private static readonly VectorStoreRecordDefinition s_multiKeysDefinition = new()
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static readonly VectorStoreRecordDefinition s_multiKeysDefinition = new()
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
=======
    private static readonly VectorStoreRecordDefinition s_singlePropsDefinition = new()
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static readonly VectorStoreRecordDefinition s_singlePropsDefinition = new()
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        [VectorStoreRecordData]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        [VectorStoreRecordData]
=======
        [VectorStoreRecordData(StoragePropertyName = "storage_data2")]
        [JsonPropertyName("json_data2")]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        [VectorStoreRecordData(StoragePropertyName = "storage_data2")]
        [JsonPropertyName("json_data2")]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector(4, IndexKind.Flat, DistanceFunction.DotProductSimilarity)]
        public ReadOnlyMemory<float> Vector1 { get; set; }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        [VectorStoreRecordVector]
        [JsonPropertyName("vector-2")]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        [VectorStoreRecordVector]
        [JsonPropertyName("vector-2")]
=======
        [VectorStoreRecordVector(StoragePropertyName = "storage_vector2")]
        [JsonPropertyName("json_vector2")]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        [VectorStoreRecordVector(StoragePropertyName = "storage_vector2")]
        [JsonPropertyName("json_vector2")]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        public ReadOnlyMemory<float> Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VectorStoreRecordDefinition _multiPropsDefinition = new()
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VectorStoreRecordDefinition _multiPropsDefinition = new()
=======
    private static readonly VectorStoreRecordDefinition s_multiPropsDefinition = new()
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static readonly VectorStoreRecordDefinition s_multiPropsDefinition = new()
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "data_2" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>))
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "data_2" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>))
=======
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "storage_data2" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "storage_vector2" }
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "storage_data2" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "storage_vector2" }
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VectorStoreRecordDefinition _enumerablePropsDefinition = new()
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VectorStoreRecordDefinition _enumerablePropsDefinition = new()
=======
    private static readonly VectorStoreRecordDefinition s_enumerablePropsDefinition = new()
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private static readonly VectorStoreRecordDefinition s_enumerablePropsDefinition = new()
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
#pragma warning restore CA1812 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
#pragma warning restore CA1812 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
#pragma warning restore CA1812 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
=======
>>>>>>> Stashed changes
    private sealed class StorageNamesPropsModel
    {
        [VectorStoreRecordKey(StoragePropertyName = "storage_key")]
        [JsonPropertyName("json_key")]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(StoragePropertyName = "storage_data1")]
        [JsonPropertyName("json_data1")]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData(StoragePropertyName = "storage_data2")]
        [JsonPropertyName("json_data2")]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector(StoragePropertyName = "storage_vector")]
        [JsonPropertyName("json_vector")]
        public ReadOnlyMemory<float> Vector { get; set; }
    }

    private static readonly VectorStoreRecordDefinition s_storageNamesPropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)) { StoragePropertyName = "storage_key" },
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { StoragePropertyName = "storage_data1" },
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "storage_data2" },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "storage_vector" }
        ]
    };

#pragma warning restore CA1812
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
