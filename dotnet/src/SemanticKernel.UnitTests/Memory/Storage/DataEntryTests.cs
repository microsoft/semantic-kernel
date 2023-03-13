// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory.Storage;
using Xunit;

namespace SemanticKernel.UnitTests.Memory.Storage;

/// <summary>
/// Unit tests of <see cref="DataEntry"/>.
/// </summary>
public class DataEntryTests
{
    [Fact]
    public void ItCannotHaveNullKey()
    {
        Assert.Throws<ValidationException>(() => DataEntry.Create<string>(null!, "test_value"));
    }

    [Fact]
    public void ItCannotHaveEmptyKeyName()
    {
        Assert.Throws<ValidationException>(() => DataEntry.Create<string>(string.Empty, "test_value"));
    }

    [Fact]
    public void ItWillSetNullValueTypeInputToNonNullValueInt()
    {
        // Arrange
        var target = DataEntry.Create<int>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Equal(0, target.Value);
        Assert.True(target.HasValue);
    }

    [Fact]
    public void ItWillSetNullValueTypeInputToNonNullValueFloat()
    {
        // Arrange
        var target = DataEntry.Create<float>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Equal(0.0F, target.Value);
        Assert.True(target.HasValue);
    }

    [Fact]
    public void ItWillSetNullValueTypeInputToNonNullValueDouble()
    {
        // Arrange
        var target = DataEntry.Create<double>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Equal(0.0, target.Value);
        Assert.True(target.HasValue);
    }

    [Fact]
    public void ItWillSetNullValueTypeInputToNonNullValueBool()
    {
        // Arrange
        var target = DataEntry.Create<bool>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.False(target.Value);
        Assert.True(target.HasValue);
    }

    [Fact]
    public void ItWillSetNullReferenceTypeInputToNullString()
    {
        // Arrange
        var target = DataEntry.Create<string>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Null(target.Value);
        Assert.False(target.HasValue);
    }

    [Fact]
    public void ItWillSetNullReferenceTypeInputToNullObject()
    {
        // Arrange
        var target = DataEntry.Create<object>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Null(target.Value);
        Assert.False(target.HasValue);
    }

    [Fact]
    public void ItWillSetNullReferenceTypeInputToNullDynamic()
    {
        // Arrange
        var target = DataEntry.Create<dynamic>("test_key", null!);

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Null(target.Value);
        Assert.False(target.HasValue);
    }

    [Fact]
    public void ItCanCreateMemoryEntryWithNoTimestamp()
    {
        // Arrange
        var target = DataEntry.Create<string>("test_key", "test_value");

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Equal("test_value", target.Value);
        Assert.True(target.HasValue);
        Assert.False(target.Timestamp.HasValue);
        Assert.Null(target.Timestamp);
    }

    [Fact]
    public void ItCanCreateMemoryEntryWithTimestamp()
    {
        // Arrange
        var target = DataEntry.Create<int>("test_key", 10, new DateTimeOffset(2020, 1, 1, 0, 0, 0, TimeSpan.Zero));

        // Assert
        Assert.Equal("test_key", target.Key);
        Assert.Equal(10, target.Value);
        Assert.True(target.HasValue);
        Assert.True(target.Timestamp.HasValue);
        Assert.NotNull(target.Timestamp);
    }

    [Fact]
    public void ItCanSetValue()
    {
        // Arrange
        var target = DataEntry.Create<string>("test_key", "test_value");

        // Act
        target.Value = "new_value";

        // Assert
        Assert.Equal("new_value", target.Value);
        Assert.True(target.HasValue);
    }

    [Fact]
    public void ItCanSetTimestamp()
    {
        // Arrange
        var target = DataEntry.Create<int>("test_key", 10);

        // Act
        target.Timestamp = new DateTimeOffset(2020, 1, 1, 0, 0, 0, TimeSpan.Zero);

        // Assert
        Assert.Equal(new DateTimeOffset(2020, 1, 1, 0, 0, 0, TimeSpan.Zero), target.Timestamp);
        Assert.True(target.HasValue);
    }

    [Fact]
    public void ItCanCheckForEquality()
    {
        // Arrange
        var target = DataEntry.Create<int>("test_key", 10);

        // Assert
        Assert.Equal(target, target);
        Assert.Equal(DataEntry.Create<int>("test_key", 10), target);
        Assert.NotEqual(DataEntry.Create<int>("test_key", 9), target);
        Assert.True(DataEntry.Create<int>("test_key", 10) == target);
        Assert.True(DataEntry.Create<int>("test_key", 9) != target);
    }

    [Fact]
    public void ItCanHashTheCollectionInformation()
    {
        // Arrange
        var entry = DataEntry.Create<float>("test_key", 10.875F);

        // Act
        var target = entry.GetHashCode();

        // Assert
        Assert.IsType<int>(target);
        Assert.True(target != 0);
    }

    [Fact]
    public void ItCanSerializeObjectToJson()
    {
        // Arrange
        var entry = DataEntry.Create<float>("test_key", 10.875F);

        // Act
        var target = entry.ToString();

        // Assert
        Assert.IsType<string>(target);
        Assert.Contains("\"key\":\"test_key\"", target, StringComparison.Ordinal);
        Assert.Contains("\"value\":10.875", target, StringComparison.Ordinal);
        Assert.Contains("\"timestamp\":null", target, StringComparison.Ordinal);
    }

    [Fact]
    public void ItCanDeserializeStringToObject()
    {
        // Arrange
        var entry = DataEntry.Create<float>("test_key", 128.5F);

        // Act
        var json = entry.ToString();
        var result = DataEntry.TryParse<float>(json, out DataEntry<float>? target);

        // Assert
        Assert.True(result);
        Assert.Equal(entry, target);
    }

    [Fact]
    public void ItWillReturnFalseIfDeserializationStringIsNotObjectString()
    {
        // Arrange
        var badString = "abcdefghijklmnopqrstuv";

        // Act
        var result = DataEntry.TryParse<float>(badString, out DataEntry<float>? target);

        // Assert
        Assert.False(result);
        Assert.Null(target);
    }
}
