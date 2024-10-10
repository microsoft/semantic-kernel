// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordPropertyVerificationTests
{
    [Fact]
    public void VerifyPropertyTypesPassForAllowedTypes()
    {
        // Arrange.
        var reader = new VectorStoreRecordPropertyReader(typeof(SinglePropsModel), null, null);

        // Act.
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(reader.DataProperties, [typeof(string)], "Data");
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._singlePropsDefinition.Properties.OfType<VectorStoreRecordDataProperty>(), [typeof(string)], "Data");
    }

    [Fact]
    public void VerifyPropertyTypesPassForAllowedEnumerableTypes()
    {
        // Arrange.
        var reader = new VectorStoreRecordPropertyReader(typeof(EnumerablePropsModel), null, null);

        // Act.
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(reader.DataProperties, [typeof(string)], "Data", supportEnumerable: true);
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._enumerablePropsDefinition.Properties.OfType<VectorStoreRecordDataProperty>(), [typeof(string)], "Data", supportEnumerable: true);
    }

    [Fact]
    public void VerifyPropertyTypesFailsForDisallowedTypes()
    {
        // Arrange.
        var reader = new VectorStoreRecordPropertyReader(typeof(SinglePropsModel), null, null);

        // Act.
        var ex1 = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyVerification.VerifyPropertyTypes(reader.DataProperties, [typeof(int), typeof(float)], "Data"));
        var ex2 = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._singlePropsDefinition.Properties.OfType<VectorStoreRecordDataProperty>(), [typeof(int), typeof(float)], "Data"));

        // Assert.
        Assert.Equal("Data properties must be one of the supported types: System.Int32, System.Single. Type of the property 'Data' is System.String.", ex1.Message);
        Assert.Equal("Data properties must be one of the supported types: System.Int32, System.Single. Type of the property 'Data' is System.String.", ex2.Message);
    }

    [Theory]
    [InlineData(typeof(SinglePropsModel), false, new Type[] { typeof(string) }, false)]
    [InlineData(typeof(VectorStoreGenericDataModel<string>), false, new Type[] { typeof(string), typeof(ulong) }, false)]
    [InlineData(typeof(VectorStoreGenericDataModel<int>), true, new Type[] { typeof(string), typeof(ulong) }, false)]
    [InlineData(typeof(VectorStoreGenericDataModel<int>), false, new Type[] { typeof(string), typeof(ulong) }, true)]
    public void VerifyGenericDataModelKeyTypeThrowsOnlyForUnsupportedKeyTypeWithoutCustomMapper(Type recordType, bool customMapperSupplied, IEnumerable<Type> allowedKeyTypes, bool shouldThrow)
    {
        if (shouldThrow)
        {
            var ex = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(recordType, customMapperSupplied, allowedKeyTypes));
            Assert.Equal("The key type 'System.Int32' of data model 'VectorStoreGenericDataModel' is not supported by the default mappers. Only the following key types are supported: System.String, System.UInt64. Please provide your own mapper to map to your chosen key type.", ex.Message);
        }
        else
        {
            VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(recordType, customMapperSupplied, allowedKeyTypes);
        }
    }

    [Theory]
    [InlineData(typeof(SinglePropsModel), false, false)]
    [InlineData(typeof(VectorStoreGenericDataModel<string>), true, false)]
    [InlineData(typeof(VectorStoreGenericDataModel<string>), false, true)]
    public void VerifyGenericDataModelDefinitionSuppliedThrowsOnlyForMissingDefinition(Type recordType, bool definitionSupplied, bool shouldThrow)
    {
        if (shouldThrow)
        {
            var ex = Assert.Throws<ArgumentException>(() => VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(recordType, definitionSupplied));
            Assert.Equal("A VectorStoreRecordDefinition must be provided when using 'VectorStoreGenericDataModel'.", ex.Message);
        }
        else
        {
            VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(recordType, definitionSupplied);
        }
    }

    [Theory]
    [InlineData(typeof(List<string>), true)]
    [InlineData(typeof(ICollection<string>), true)]
    [InlineData(typeof(IEnumerable<string>), true)]
    [InlineData(typeof(IList<string>), true)]
    [InlineData(typeof(IReadOnlyCollection<string>), true)]
    [InlineData(typeof(IReadOnlyList<string>), true)]
    [InlineData(typeof(string[]), true)]
    [InlineData(typeof(IEnumerable), true)]
    [InlineData(typeof(ArrayList), true)]
    [InlineData(typeof(string), false)]
    [InlineData(typeof(HashSet<string>), false)]
    [InlineData(typeof(ISet<string>), false)]
    [InlineData(typeof(Dictionary<string, string>), false)]
    [InlineData(typeof(Stack<string>), false)]
    [InlineData(typeof(Queue<string>), false)]
    public void IsSupportedEnumerableTypeReturnsCorrectAnswerForEachType(Type type, bool expected)
    {
        // Act.
        var actual = VectorStoreRecordPropertyVerification.IsSupportedEnumerableType(type);

        // Assert.
        Assert.Equal(expected, actual);
    }

#pragma warning disable CA1812 // Invalid unused classes error, since I am using these for testing purposes above.

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

#pragma warning restore CA1812
}
