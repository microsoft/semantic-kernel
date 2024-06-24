// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

public class InternalTypeConverterTests
{
    [Theory]
    [InlineData(123.456, "123,456", "fr-FR")]
    [InlineData(123.456, "123.456", "en-US")]
    public void ItTakesCultureIntoAccount(double value, string expectedString, string culture)
    {
        // Act
        var result = InternalTypeConverter.ConvertToString(value, new CultureInfo(culture));

        // Assert
        Assert.Equal(expectedString, result);
    }

    [Fact]
    public void ItCanConvertManyTypes()
    {
        // Arrange  
        var culture = CultureInfo.InvariantCulture;

        // Atc & Assert
        Assert.Equal("10", InternalTypeConverter.ConvertToString((byte)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((byte?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((byte?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((sbyte)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((sbyte?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((sbyte?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((short)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((short?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((short?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((ushort)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((ushort?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((ushort?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((int)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((int?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((int?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((uint)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((uint?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((uint?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((long)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((long?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((long?)null, culture));

        Assert.Equal("10", InternalTypeConverter.ConvertToString((ulong)10, culture));
        Assert.Equal("10", InternalTypeConverter.ConvertToString((ulong?)10, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((ulong?)null, culture));

        Assert.Equal("10.5", InternalTypeConverter.ConvertToString((float)10.5, culture));
        Assert.Equal("10.5", InternalTypeConverter.ConvertToString((float?)10.5, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((float?)null, culture));

        Assert.Equal("10.5", InternalTypeConverter.ConvertToString((double)10.5, culture));
        Assert.Equal("10.5", InternalTypeConverter.ConvertToString((double?)10.5, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((double?)null, culture));

        Assert.Equal("10.5", InternalTypeConverter.ConvertToString((decimal)10.5, culture));
        Assert.Equal("10.5", InternalTypeConverter.ConvertToString((decimal?)10.5, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((decimal?)null, culture));

        Assert.Equal("A", InternalTypeConverter.ConvertToString((char)'A', culture));
        Assert.Equal("A", InternalTypeConverter.ConvertToString((char?)'A', culture));
        Assert.Null(InternalTypeConverter.ConvertToString((char?)null, culture));

        Assert.Equal("True", InternalTypeConverter.ConvertToString((bool)true, culture));
        Assert.Equal("True", InternalTypeConverter.ConvertToString((bool?)true, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((bool?)null, culture));

        Assert.Equal("12/06/2023 11:53:36", InternalTypeConverter.ConvertToString((DateTime)DateTime.ParseExact("06.12.2023 11:53:36", "dd.MM.yyyy HH:mm:ss", culture), culture));
        Assert.Equal("12/06/2023 11:53:36", InternalTypeConverter.ConvertToString((DateTime?)DateTime.ParseExact("06.12.2023 11:53:36", "dd.MM.yyyy HH:mm:ss", culture), culture));
        Assert.Null(InternalTypeConverter.ConvertToString((DateTime?)null, culture));

        Assert.Equal("12/06/2023 11:53:36 +02:00", InternalTypeConverter.ConvertToString((DateTimeOffset)DateTimeOffset.ParseExact("06.12.2023 11:53:36 +02:00", "dd.MM.yyyy HH:mm:ss zzz", culture), culture));
        Assert.Equal("12/06/2023 11:53:36 +02:00", InternalTypeConverter.ConvertToString((DateTimeOffset?)DateTimeOffset.ParseExact("06.12.2023 11:53:36 +02:00", "dd.MM.yyyy HH:mm:ss zzz", culture), culture));
        Assert.Null(InternalTypeConverter.ConvertToString((DateTimeOffset?)null, culture));

        Assert.Equal("01:00:00", InternalTypeConverter.ConvertToString((TimeSpan)TimeSpan.FromHours(1), culture));
        Assert.Equal("01:00:00", InternalTypeConverter.ConvertToString((TimeSpan?)TimeSpan.FromHours(1), culture));
        Assert.Null(InternalTypeConverter.ConvertToString((TimeSpan?)null, culture));

        Guid guid = Guid.NewGuid();
        Assert.Equal(guid.ToString(), InternalTypeConverter.ConvertToString((Guid)guid, culture));
        Assert.Equal(guid.ToString(), InternalTypeConverter.ConvertToString((Guid?)guid, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((Guid?)null, culture));

        Assert.Equal("Monday", InternalTypeConverter.ConvertToString((DayOfWeek)DayOfWeek.Monday, culture));
        Assert.Equal("Monday", InternalTypeConverter.ConvertToString((DayOfWeek?)DayOfWeek.Monday, culture));
        Assert.Null(InternalTypeConverter.ConvertToString((DayOfWeek?)null, culture));

        Assert.Equal("https://example.com", InternalTypeConverter.ConvertToString((Uri)new("https://example.com"), culture));
        Assert.Equal("https://example.com", InternalTypeConverter.ConvertToString((Uri?)new("https://example.com"), culture));
        Assert.Null(InternalTypeConverter.ConvertToString((Uri?)null, culture));

        Assert.Equal("Hello, World!", InternalTypeConverter.ConvertToString((string)"Hello, World!", culture));
        Assert.Equal("Hello, World!", InternalTypeConverter.ConvertToString((string?)"Hello, World!", culture));
        Assert.Null(InternalTypeConverter.ConvertToString((string?)null, culture));
    }

    [Fact]
    public void ItCallsCustomConverterSpecifiedByTypeConverterAttribute()
    {
        // Arrange
        var customType = new MyCustomType();
        customType.Value = 4;

        // Act
        var result = InternalTypeConverter.ConvertToString(customType, CultureInfo.InvariantCulture);

        // Assert
        Assert.Equal("4", result);
    }

#pragma warning disable CA1812 // Instantiated by reflection
    private sealed class MyCustomTypeConverter : TypeConverter
    {
        public override bool CanConvertTo(ITypeDescriptorContext? context, Type? destinationType)
            => destinationType == typeof(string);

        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
            => ((MyCustomType)value!).Value.ToString(culture);
    }

    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Value { get; set; }
    }
#pragma warning restore CA1812
}
