// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData.ProviderServices;
using Xunit;

namespace VectorData.UnitTests;

public class IPropertyModelTests
{
    #region Value type nullability

    [Fact]
    public void IsNullable_NonNullableValueType_ReturnsFalse()
    {
        var property = new DataPropertyModel("test", typeof(int));
        Assert.False(property.IsNullable);
    }

    [Fact]
    public void IsNullable_NullableValueType_ReturnsTrue()
    {
        var property = new DataPropertyModel("test", typeof(int?));
        Assert.True(property.IsNullable);
    }

    [Fact]
    public void IsNullable_Guid_ReturnsFalse()
    {
        var property = new DataPropertyModel("test", typeof(Guid));
        Assert.False(property.IsNullable);
    }

    [Fact]
    public void IsNullable_NullableGuid_ReturnsTrue()
    {
        var property = new DataPropertyModel("test", typeof(Guid?));
        Assert.True(property.IsNullable);
    }

    [Fact]
    public void IsNullable_ReadOnlyMemoryFloat_ReturnsFalse()
    {
        var property = new DataPropertyModel("test", typeof(ReadOnlyMemory<float>));
        Assert.False(property.IsNullable);
    }

    [Fact]
    public void IsNullable_NullableReadOnlyMemoryFloat_ReturnsTrue()
    {
        var property = new DataPropertyModel("test", typeof(ReadOnlyMemory<float>?));
        Assert.True(property.IsNullable);
    }

    #endregion

    #region Reference type nullability (dynamic mapping, no PropertyInfo)

    [Fact]
    public void IsNullable_String_WithoutPropertyInfo_ReturnsTrue()
    {
        // Without PropertyInfo (dynamic mapping), reference types are assumed nullable
        var property = new DataPropertyModel("test", typeof(string));
        Assert.True(property.IsNullable);
    }

    [Fact]
    public void IsNullable_ByteArray_WithoutPropertyInfo_ReturnsTrue()
    {
        var property = new DataPropertyModel("test", typeof(byte[]));
        Assert.True(property.IsNullable);
    }

    #endregion

#if NET
    #region NRT detection via NullabilityInfoContext (POCO mapping with PropertyInfo)

    [Fact]
    public void IsNullable_NonNullableString_WithPropertyInfo_ReturnsFalse()
    {
        var propertyInfo = typeof(NrtTestRecord).GetProperty(nameof(NrtTestRecord.NonNullableString))!;
        var property = new DataPropertyModel("test", typeof(string)) { PropertyInfo = propertyInfo };
        Assert.False(property.IsNullable);
    }

    [Fact]
    public void IsNullable_NullableString_WithPropertyInfo_ReturnsTrue()
    {
        var propertyInfo = typeof(NrtTestRecord).GetProperty(nameof(NrtTestRecord.NullableString))!;
        var property = new DataPropertyModel("test", typeof(string)) { PropertyInfo = propertyInfo };
        Assert.True(property.IsNullable);
    }

    [Fact]
    public void IsNullable_NonNullableByteArray_WithPropertyInfo_ReturnsFalse()
    {
        var propertyInfo = typeof(NrtTestRecord).GetProperty(nameof(NrtTestRecord.NonNullableByteArray))!;
        var property = new DataPropertyModel("test", typeof(byte[])) { PropertyInfo = propertyInfo };
        Assert.False(property.IsNullable);
    }

    [Fact]
    public void IsNullable_NullableByteArray_WithPropertyInfo_ReturnsTrue()
    {
        var propertyInfo = typeof(NrtTestRecord).GetProperty(nameof(NrtTestRecord.NullableByteArray))!;
        var property = new DataPropertyModel("test", typeof(byte[])) { PropertyInfo = propertyInfo };
        Assert.True(property.IsNullable);
    }

    [Fact]
    public void IsNullable_ValueType_WithPropertyInfo_StillUsesTypeCheck()
    {
        var propertyInfo = typeof(NrtTestRecord).GetProperty(nameof(NrtTestRecord.NonNullableInt))!;
        var property = new DataPropertyModel("test", typeof(int)) { PropertyInfo = propertyInfo };
        Assert.False(property.IsNullable);

        var nullablePropertyInfo = typeof(NrtTestRecord).GetProperty(nameof(NrtTestRecord.NullableInt))!;
        var nullableProperty = new DataPropertyModel("test", typeof(int?)) { PropertyInfo = nullablePropertyInfo };
        Assert.True(nullableProperty.IsNullable);
    }

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor
#pragma warning disable CA1812 // Class is used via reflection
    private sealed class NrtTestRecord
    {
        public string NonNullableString { get; set; }
        public string? NullableString { get; set; }
        public byte[] NonNullableByteArray { get; set; }
        public byte[]? NullableByteArray { get; set; }
        public int NonNullableInt { get; set; }
        public int? NullableInt { get; set; }
    }
#pragma warning restore CA1812
#pragma warning restore CS8618

    #endregion
#endif
}
