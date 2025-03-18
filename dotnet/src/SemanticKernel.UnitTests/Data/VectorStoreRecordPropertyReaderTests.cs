// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordPropertyReaderTests
{
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

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void GetVectorPropertyOrSingleReturnsRequestedVectorAndThrowsForInvalidVector(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);
        var validVector = new VectorSearchOptions<MultiPropsModel>() { VectorProperty = r => r.Vector2 };
        var invalidVector = new VectorSearchOptions<MultiPropsModel>() { VectorProperty = r => r.Data2 };

        // Act & Assert.
        Assert.Equal("Vector2", sut.GetVectorPropertyOrSingle(validVector).DataModelPropertyName);
        Assert.Throws<InvalidOperationException>(() => sut.GetVectorPropertyOrSingle(invalidVector));
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void GetVectorPropertyOrSingleThrowsForMultipleVectors(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() => sut.GetVectorPropertyOrSingle<MultiPropsModel>(null));
    }

    [Theory]
    [MemberData(nameof(NoVectorsTypeAndDefinitionCombos))]
    public void GetVectorPropertyOrSingleThrowsForNoVectors(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() => sut.GetVectorPropertyOrSingle<NoVectorModel>(null));
    }

    [Fact]
    public void GetVectorPropertyOrSingleReturnsRequestedGenericDataModelVectorWhenUsingConst()
    {
        const string TheConst = "FloatVector";
        VectorStoreRecordPropertyReader sut = CreateReaderForGenericModel(TheConst);
        VectorSearchOptions<VectorStoreGenericDataModel<string>> expectedConst = new()
        {
            VectorProperty = r => r.Vectors[TheConst]
        };
        VectorSearchOptions<VectorStoreGenericDataModel<string>> wrongConst = new()
        {
            VectorProperty = r => r.Vectors["Different"]
        };

        Assert.Equal(TheConst, sut.GetVectorPropertyOrSingle(expectedConst).DataModelPropertyName);
        Assert.Throws<InvalidOperationException>(() => sut.GetVectorPropertyOrSingle(wrongConst));
    }

    [Fact]
    public void GetVectorPropertyOrSingleReturnsRequestedGenericDataModelVectorWhenUsingVariable()
    {
        string theVariable = "FloatVector";
        string theWrongVariable = "Different";
        VectorStoreRecordPropertyReader sut = CreateReaderForGenericModel(theVariable);
        VectorSearchOptions<VectorStoreGenericDataModel<string>> expectedVariable = new()
        {
            VectorProperty = r => r.Vectors[theVariable]
        };
        VectorSearchOptions<VectorStoreGenericDataModel<string>> wrongVariable = new()
        {
            VectorProperty = r => r.Vectors[theWrongVariable]
        };

        Assert.Equal(theVariable, sut.GetVectorPropertyOrSingle(expectedVariable).DataModelPropertyName);
        Assert.Throws<InvalidOperationException>(() => sut.GetVectorPropertyOrSingle(wrongVariable));
    }

    [Theory]
    [InlineData("FloatVector", "Different")]
    // it's a Theory just for the need of testing a method expected being captured by the lambda property selector
    public void GetVectorPropertyOrSingleReturnsRequestedGenericDataModelVectorWhenUsingArgument(string expected, string wrong)
    {
        VectorStoreRecordPropertyReader sut = CreateReaderForGenericModel(expected);
        VectorSearchOptions<VectorStoreGenericDataModel<string>> expectedArgument = new()
        {
            VectorProperty = r => r.Vectors[expected]
        };
        VectorSearchOptions<VectorStoreGenericDataModel<string>> wrongArgument = new()
        {
            VectorProperty = r => r.Vectors[wrong]
        };

        Assert.Equal("FloatVector", sut.GetVectorPropertyOrSingle(expectedArgument).DataModelPropertyName);
        Assert.Throws<InvalidOperationException>(() => sut.GetVectorPropertyOrSingle(wrongArgument));
    }

    private static VectorStoreRecordPropertyReader CreateReaderForGenericModel(string vectorPropertyName)
    {
        VectorStoreGenericDataModel<string> genericRecord = new("key")
        {
            Data =
            {
                ["Text"] = "data"
            },
            Vectors =
            {
                [vectorPropertyName] = new ReadOnlyMemory<float>([-1, -1, -1, -1])
            }
        };
        VectorStoreRecordDefinition definition = new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                new VectorStoreRecordDataProperty("Text", typeof(string)),
                new VectorStoreRecordVectorProperty(vectorPropertyName, typeof(ReadOnlyMemory<float>)),
            ]
        };

        return new(genericRecord.GetType(), definition, null);
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void GetFullTextDataPropertyOrOnlyReturnsRequestedPropOrOnlyTextDataPropAndThrowsForInvalidProp(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Equal("Data1", sut.GetFullTextDataPropertyOrSingle<MultiPropsModel>(r => r.Data1).DataModelPropertyName);
        Assert.Equal("Data1", sut.GetFullTextDataPropertyOrSingle<MultiPropsModel>(null).DataModelPropertyName);
        Assert.Throws<InvalidOperationException>(() => sut.GetFullTextDataPropertyOrSingle<MultiPropsModel>(r => r.Vector1));
        Assert.Throws<InvalidOperationException>(() => sut.GetFullTextDataPropertyOrSingle<MultiPropsModel>(r => "DoesNotExist"));
    }

    [Theory]
    [MemberData(nameof(NoVectorsTypeAndDefinitionCombos))]
    public void GetFullTextDataPropertyOrOnlyThrowsForNoTextDataProps(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() => sut.GetFullTextDataPropertyOrSingle<NoVectorModel>(null));
    }

    [Theory]
    [MemberData(nameof(MultiPropsTypeAndDefinitionCombos))]
    public void GetFullTextDataPropertyOrOnlyThrowsForNonFullTextSearchProp(Type type, VectorStoreRecordDefinition? definition)
    {
        // Arrange.
        var sut = new VectorStoreRecordPropertyReader(type, definition, null);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() => sut.GetFullTextDataPropertyOrSingle<MultiPropsModel>(r => r.Data2));
    }

    [Fact]
    public void GetFullTextDataPropertyOrOnlyThrowsForMultipleMatchingProps()
    {
        // Arrange.
        var properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { IsFullTextSearchable = true },
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { IsFullTextSearchable = true }
        };
        var definition = new VectorStoreRecordDefinition
        {
            Properties = properties
        };
        var sut = new VectorStoreRecordPropertyReader(typeof(object), definition, null);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() => sut.GetFullTextDataPropertyOrSingle<object>(null));
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
    }

#pragma warning disable CA1812 // Invalid unused classes error, since I am using these for testing purposes above.

    private sealed class NoKeyModel
    {
    }

    private static readonly VectorStoreRecordDefinition s_noKeyDefinition = new();

    private sealed class NoVectorModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;
    }

    private static readonly VectorStoreRecordDefinition s_noVectorDefinition = new()
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

    private static readonly VectorStoreRecordDefinition s_multiKeysDefinition = new()
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

    private static readonly VectorStoreRecordDefinition s_singlePropsDefinition = new()
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

        [VectorStoreRecordData(StoragePropertyName = "storage_data2")]
        [JsonPropertyName("json_data2")]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector(4, DistanceFunction.DotProductSimilarity, IndexKind.Flat)]
        public ReadOnlyMemory<float> Vector1 { get; set; }

        [VectorStoreRecordVector(StoragePropertyName = "storage_vector2")]
        [JsonPropertyName("json_vector2")]
        public ReadOnlyMemory<float> Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private static readonly VectorStoreRecordDefinition s_multiPropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { StoragePropertyName = "storage_data2" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "storage_vector2" }
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

    private static readonly VectorStoreRecordDefinition s_enumerablePropsDefinition = new()
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
}
