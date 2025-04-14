// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Xunit;

namespace VectorData.UnitTests;

public class VectorStoreRecordModelBuilderTests
{
    [Theory]
    [InlineData(typeof(bool), typeof(RecordWithSimpleDataProperties))]
    [InlineData(typeof(bool?), typeof(RecordWithSimpleDataProperties))]
    [InlineData(typeof(bool), typeof(RecordWithNullableDataProperties))]
    [InlineData(typeof(bool?), typeof(RecordWithNullableDataProperties))]
    [InlineData(typeof(bool), typeof(RecordWithEnumerableDataProperties))]
    [InlineData(typeof(bool?), typeof(RecordWithEnumerableDataProperties))]
    [InlineData(typeof(bool), typeof(RecordWithEnumerableNullableDataProperties))]
    [InlineData(typeof(bool?), typeof(RecordWithEnumerableNullableDataProperties))]
    public void BuildWithDifferentDataPropertyTypesReturnsVectorStoreRecordModel(Type dataPropertyType, Type recordType)
    {
        // Arrange
        var options = new VectorStoreRecordModelBuildingOptions()
        {
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = true,
            RequiresAtLeastOneVector = false,

            SupportedKeyPropertyTypes = [typeof(string)],
            SupportedDataPropertyTypes = [dataPropertyType],
            SupportedEnumerableDataPropertyElementTypes = [dataPropertyType],
            SupportedVectorPropertyTypes = [typeof(ReadOnlyMemory<float>)]
        };

        var builder = new VectorStoreRecordModelBuilder(options);

        // Act
        var model = builder.Build(recordType, vectorStoreRecordDefinition: null);

        // Assert
        Assert.NotNull(model);
    }

    #region private

#pragma warning disable CA1812
    private sealed class RecordWithSimpleDataProperties
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public bool Flag { get; set; }

        [VectorStoreRecordVector(Dimensions: 4)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    private sealed class RecordWithNullableDataProperties
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public bool? Flag { get; set; }

        [VectorStoreRecordVector(Dimensions: 4)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    private sealed class RecordWithEnumerableDataProperties
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public List<bool> Flags { get; set; }

        [VectorStoreRecordVector(Dimensions: 4)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    private sealed class RecordWithEnumerableNullableDataProperties
    {
        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public List<bool?> Flags { get; set; }

        [VectorStoreRecordVector(Dimensions: 4)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
