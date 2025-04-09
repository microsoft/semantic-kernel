// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordMappingTests
{
    [Fact]
    public void BuildPropertiesInfoWithValuesShouldBuildPropertiesInfo()
    {
        // Arrange.
        var dataModelPropertiesInfo = new[]
        {
            typeof(DataModel).GetProperty(nameof(DataModel.Key))!,
            typeof(DataModel).GetProperty(nameof(DataModel.Data))!
        };
        var dataModelToStorageNameMapping = new Dictionary<string, string>
        {
            { nameof(DataModel.Key), "key" },
            { nameof(DataModel.Data), "data" },
        };
        var storageValues = new Dictionary<string, string>
        {
            { "key", "key value" },
            { "data", "data value" },
        };

        // Act.
        var propertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
            dataModelPropertiesInfo,
            dataModelToStorageNameMapping,
            storageValues);

        // Assert.
        var propertiesInfoWithValuesArray = propertiesInfoWithValues.ToArray();
        Assert.Equal(2, propertiesInfoWithValuesArray.Length);
        Assert.Equal(dataModelPropertiesInfo[0], propertiesInfoWithValuesArray[0].Key);
        Assert.Equal("key value", propertiesInfoWithValuesArray[0].Value);
        Assert.Equal(dataModelPropertiesInfo[1], propertiesInfoWithValuesArray[1].Key);
        Assert.Equal("data value", propertiesInfoWithValuesArray[1].Value);
    }

    [Fact]
    public void BuildPropertiesInfoWithValuesShouldUseValueMapperIfProvided()
    {
        // Arrange.
        var dataModelPropertiesInfo = new[]
        {
            typeof(DataModel).GetProperty(nameof(DataModel.Key))!,
            typeof(DataModel).GetProperty(nameof(DataModel.Data))!
        };
        var dataModelToStorageNameMapping = new Dictionary<string, string>
        {
            { nameof(DataModel.Key), "key" },
            { nameof(DataModel.Data), "data" },
        };
        var storageValues = new Dictionary<string, int>
        {
            { "key", 10 },
            { "data", 20 },
        };

        // Act.
        var propertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
            dataModelPropertiesInfo,
            dataModelToStorageNameMapping,
            storageValues,
            (int value, Type type) => value.ToString());

        // Assert.
        var propertiesInfoWithValuesArray = propertiesInfoWithValues.ToArray();
        Assert.Equal(2, propertiesInfoWithValuesArray.Length);
        Assert.Equal(dataModelPropertiesInfo[0], propertiesInfoWithValuesArray[0].Key);
        Assert.Equal("10", propertiesInfoWithValuesArray[0].Value);
        Assert.Equal(dataModelPropertiesInfo[1], propertiesInfoWithValuesArray[1].Key);
        Assert.Equal("20", propertiesInfoWithValuesArray[1].Value);
    }

    [Fact]
    public void SetPropertiesOnRecordShouldSetProperties()
    {
        // Arrange.
        var record = new DataModel();

        // Act.
        VectorStoreRecordMapping.SetPropertiesOnRecord(record, new[]
        {
            new KeyValuePair<PropertyInfo, object?>(typeof(DataModel).GetProperty(nameof(DataModel.Key))!, "key value"),
            new KeyValuePair<PropertyInfo, object?>(typeof(DataModel).GetProperty(nameof(DataModel.Data))!, "data value"),
        });

        // Assert.
        Assert.Equal("key value", record.Key);
        Assert.Equal("data value", record.Data);
    }

    [Theory]
    [InlineData(typeof(List<string>))]
    [InlineData(typeof(ICollection<string>))]
    [InlineData(typeof(IEnumerable<string>))]
    [InlineData(typeof(IList<string>))]
    [InlineData(typeof(IReadOnlyCollection<string>))]
    [InlineData(typeof(IReadOnlyList<string>))]
    [InlineData(typeof(string[]))]
    [InlineData(typeof(IEnumerable))]
    [InlineData(typeof(ArrayList))]
    public void CreateEnumerableCanCreateEnumerablesOfAllRequiredTypes(Type expectedType)
    {
        // Arrange.
        IEnumerable<string> input = new List<string> { "one", "two", "three", "four" };

        // Act.
        var actual = VectorStoreRecordMapping.CreateEnumerable(input, expectedType);

        // Assert.
        Assert.True(expectedType.IsAssignableFrom(actual!.GetType()));
    }

    [Theory]
    [InlineData(typeof(List<string>))]
    [InlineData(typeof(ICollection<string>))]
    [InlineData(typeof(IEnumerable<string>))]
    [InlineData(typeof(IList<string>))]
    [InlineData(typeof(IReadOnlyCollection<string>))]
    [InlineData(typeof(IReadOnlyList<string>))]
    [InlineData(typeof(string[]))]
    [InlineData(typeof(IEnumerable))]
    [InlineData(typeof(ArrayList))]
    public void CreateEnumerableCanCreateEnumerablesOfAllRequiredTypesUsingObjectEnumerable(Type expectedType)
    {
        // Arrange.
        IEnumerable<object> input = new List<object> { "one", "two", "three", "four" };

        // Act.
        var actual = VectorStoreRecordMapping.CreateEnumerable(input, expectedType);

        // Assert.
        Assert.True(expectedType.IsAssignableFrom(actual!.GetType()));
    }

    [Theory]
    [InlineData(typeof(string))]
    [InlineData(typeof(HashSet<string>))]
    [InlineData(typeof(ISet<string>))]
    [InlineData(typeof(Dictionary<string, string>))]
    [InlineData(typeof(Stack<string>))]
    [InlineData(typeof(Queue<string>))]
    public void CreateEnumerableThrowsForUnsupportedType(Type expectedType)
    {
        // Arrange.
        IEnumerable<string> input = new List<string> { "one", "two", "three", "four" };

        // Act & Assert.
        Assert.Throws<NotSupportedException>(() => VectorStoreRecordMapping.CreateEnumerable(input, expectedType));
    }

    private sealed class DataModel
    {
        public string Key { get; set; } = string.Empty;
        public string Data { get; set; } = string.Empty;
    }
}
