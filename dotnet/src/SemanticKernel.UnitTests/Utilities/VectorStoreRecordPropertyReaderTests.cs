// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

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
            "Multiple vector properties configured for type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+MultiPropsModel while only one is supported." :
            "Multiple vector properties found on type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+MultiPropsModel while only one is supported.";
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
            "Multiple key properties configured for type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+MultiKeysModel." :
            "Multiple key properties found on type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+MultiKeysModel.";
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
            "No key property configured for type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+NoKeyModel." :
            "No key property found on type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+NoKeyModel.";
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
            "No vector property configured for type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+NoVectorModel." :
            "No vector property found on type SemanticKernel.UnitTests.Utilities.VectorStoreRecordPropertyReaderTests+NoVectorModel.";
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

        [VectorStoreRecordData]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Vector1 { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float> Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private readonly VectorStoreRecordDefinition _multiPropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key"),
            new VectorStoreRecordDataProperty("Data1"),
            new VectorStoreRecordDataProperty("Data2"),
            new VectorStoreRecordVectorProperty("Vector1"),
            new VectorStoreRecordVectorProperty("Vector2")
        ]
    };
#pragma warning restore CA1812 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
}
