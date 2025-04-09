// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;
using Xunit;

namespace SemanticKernel.Connectors.Pinecone.UnitTests;

/// <summary>
/// Contains tests for the <see cref="PineconeGenericDataModelMapper"/> class.
/// </summary>
public class PineconeGenericDataModelMapperTests
{
    private static readonly VectorStoreRecordDefinition s_singleVectorStoreRecordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordDataProperty("IntDataProp", typeof(int)),
            new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
            new VectorStoreRecordDataProperty("LongDataProp", typeof(long)),
            new VectorStoreRecordDataProperty("NullableLongDataProp", typeof(long?)),
            new VectorStoreRecordDataProperty("FloatDataProp", typeof(float)),
            new VectorStoreRecordDataProperty("NullableFloatDataProp", typeof(float?)),
            new VectorStoreRecordDataProperty("DoubleDataProp", typeof(double)),
            new VectorStoreRecordDataProperty("NullableDoubleDataProp", typeof(double?)),
            new VectorStoreRecordDataProperty("BoolDataProp", typeof(bool)),
            new VectorStoreRecordDataProperty("NullableBoolDataProp", typeof(bool?)),
            new VectorStoreRecordDataProperty("TagListDataProp", typeof(string[])),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
        },
    };

    private static readonly float[] s_vector = new float[] { 1.0f, 2.0f, 3.0f };
    private static readonly string[] s_taglist = new string[] { "tag1", "tag2" };
    private const string TestKeyString = "testKey";

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange.
        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<ulong>),
            s_singleVectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);
        var dataModel = new VectorStoreGenericDataModel<string>(TestKeyString)
        {
            Data =
            {
                ["StringDataProp"] = "string",
                ["IntDataProp"] = 1,
                ["NullableIntDataProp"] = 2,
                ["LongDataProp"] = 3L,
                ["NullableLongDataProp"] = 4L,
                ["FloatDataProp"] = 5.0f,
                ["NullableFloatDataProp"] = 6.0f,
                ["DoubleDataProp"] = 7.0,
                ["NullableDoubleDataProp"] = 8.0,
                ["BoolDataProp"] = true,
                ["NullableBoolDataProp"] = false,
                ["TagListDataProp"] = s_taglist,
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_vector),
            },
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(TestKeyString, storageModel.Id);
        Assert.Equal("string", (string?)storageModel.Metadata!["StringDataProp"]!.Value);
        // MetadataValue converts all numeric types to double.
        Assert.Equal(1, (double?)storageModel.Metadata["IntDataProp"]!.Value);
        Assert.Equal(2, (double?)storageModel.Metadata["NullableIntDataProp"]!.Value);
        Assert.Equal(3L, (double?)storageModel.Metadata["LongDataProp"]!.Value);
        Assert.Equal(4L, (double?)storageModel.Metadata["NullableLongDataProp"]!.Value);
        Assert.Equal(5.0f, (double?)storageModel.Metadata["FloatDataProp"]!.Value);
        Assert.Equal(6.0f, (double?)storageModel.Metadata["NullableFloatDataProp"]!.Value);
        Assert.Equal(7.0, (double?)storageModel.Metadata["DoubleDataProp"]!.Value);
        Assert.Equal(8.0, (double?)storageModel.Metadata["NullableDoubleDataProp"]!.Value);
        Assert.Equal(true, (bool?)storageModel.Metadata["BoolDataProp"]!.Value);
        Assert.Equal(false, (bool?)storageModel.Metadata["NullableBoolDataProp"]!.Value);
        Assert.Equal(s_taglist, ((IEnumerable<MetadataValue>?)(storageModel.Metadata["TagListDataProp"]!.Value!))
            .Select(x => x.Value as string)
            .ToArray());
        Assert.Equal(s_vector, storageModel.Values);
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreRecordDataProperty("NullableTagListDataProp", typeof(string[])),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var dataModel = new VectorStoreGenericDataModel<string>(TestKeyString)
        {
            Data =
            {
                ["StringDataProp"] = null,
                ["NullableIntDataProp"] = null,
                ["NullableTagListDataProp"] = null,
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_vector),
            },
        };

        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<Guid>),
            vectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(TestKeyString, storageModel.Id);
        Assert.Null(storageModel.Metadata!["StringDataProp"]);
        Assert.Null(storageModel.Metadata["NullableIntDataProp"]);
        Assert.Null(storageModel.Metadata["NullableTagListDataProp"]);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange
        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<ulong>),
            s_singleVectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);
        var storageModel = new Vector()
        {
            Id = TestKeyString,
            Metadata = new Metadata()
            {
                ["StringDataProp"] = (MetadataValue)"string",
                ["IntDataProp"] = (MetadataValue)1,
                ["NullableIntDataProp"] = (MetadataValue)2,
                ["LongDataProp"] = (MetadataValue)3L,
                ["NullableLongDataProp"] = (MetadataValue)4L,
                ["FloatDataProp"] = (MetadataValue)5.0f,
                ["NullableFloatDataProp"] = (MetadataValue)6.0f,
                ["DoubleDataProp"] = (MetadataValue)7.0,
                ["NullableDoubleDataProp"] = (MetadataValue)8.0,
                ["BoolDataProp"] = (MetadataValue)true,
                ["NullableBoolDataProp"] = (MetadataValue)false,
                ["TagListDataProp"] = (MetadataValue)new MetadataValue[] { "tag1", "tag2" }
            },
            Values = new float[] { 1.0f, 2.0f, 3.0f }
        };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = true });

        // Assert
        Assert.Equal(TestKeyString, dataModel.Key);
        Assert.Equal("string", (string?)dataModel.Data["StringDataProp"]);
        Assert.Equal(1, (int?)dataModel.Data["IntDataProp"]);
        Assert.Equal(2, (int?)dataModel.Data["NullableIntDataProp"]);
        Assert.Equal(3L, (long?)dataModel.Data["LongDataProp"]);
        Assert.Equal(4L, (long?)dataModel.Data["NullableLongDataProp"]);
        Assert.Equal(5.0f, (float?)dataModel.Data["FloatDataProp"]);
        Assert.Equal(6.0f, (float?)dataModel.Data["NullableFloatDataProp"]);
        Assert.Equal(7.0, (double?)dataModel.Data["DoubleDataProp"]);
        Assert.Equal(8.0, (double?)dataModel.Data["NullableDoubleDataProp"]);
        Assert.Equal(true, (bool?)dataModel.Data["BoolDataProp"]);
        Assert.Equal(false, (bool?)dataModel.Data["NullableBoolDataProp"]);
        Assert.Equal(s_taglist, (string[]?)dataModel.Data["TagListDataProp"]);
        Assert.Equal(s_vector, ((ReadOnlyMemory<float>?)dataModel.Vectors["FloatVector"])!.Value.ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreRecordDataProperty("NullableTagListDataProp", typeof(string[])),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var storageModel = new Vector()
        {
            Id = TestKeyString,
            Metadata = new Metadata()
            {
                ["StringDataProp"] = null,
                ["NullableIntDataProp"] = null,
                ["NullableTagListDataProp"] = null,
            },
            Values = new float[] { 1.0f, 2.0f, 3.0f }
        };

        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<string>),
            vectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = true });

        // Assert
        Assert.Equal(TestKeyString, dataModel.Key);
        Assert.Null(dataModel.Data["StringDataProp"]);
        Assert.Null(dataModel.Data["NullableIntDataProp"]);
        Assert.Null(dataModel.Data["NullableTagListDataProp"]);
        Assert.Equal(s_vector, ((ReadOnlyMemory<float>?)dataModel.Vectors["FloatVector"])!.Value.ToArray());
    }

    [Fact]
    public void MapFromDataToStorageModelThrowsForInvalidVectorType()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<string>),
            vectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);

        var dataModel = new VectorStoreGenericDataModel<string>(TestKeyString)
        {
            Vectors =
            {
                ["FloatVector"] = "not a vector",
            },
        };

        // Act
        var exception = Assert.Throws<VectorStoreRecordMappingException>(() => sut.MapFromDataToStorageModel(dataModel));

        // Assert
        Assert.Equal("Vector property 'FloatVector' on provided record of type VectorStoreGenericDataModel must be of type ReadOnlyMemory<float> and not null.", exception.Message);
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<string>),
            vectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);

        var dataModel = new VectorStoreGenericDataModel<string>(TestKeyString)
        {
            Vectors = { ["FloatVector"] = new ReadOnlyMemory<float>(s_vector) },
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(TestKeyString, storageModel.Id);
        Assert.False(storageModel.Metadata!.ContainsKey("StringDataProp"));
        Assert.Equal(s_vector, storageModel.Values);
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var reader = new VectorStoreRecordPropertyReader(
            typeof(VectorStoreGenericDataModel<string>),
            vectorStoreRecordDefinition,
            new() { RequiresAtLeastOneVector = true, SupportsMultipleKeys = false, SupportsMultipleVectors = false });
        var sut = new PineconeGenericDataModelMapper(reader);

        var storageModel = new Vector()
        {
            Id = TestKeyString,
            Values = new float[] { 1.0f, 2.0f, 3.0f }
        };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = true });

        // Assert
        Assert.Equal(TestKeyString, dataModel.Key);
        Assert.False(dataModel.Data.ContainsKey("StringDataProp"));
        Assert.Equal(s_vector, ((ReadOnlyMemory<float>?)dataModel.Vectors["FloatVector"])!.Value.ToArray());
    }
}
