// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using Microsoft.SemanticKernel;
using Xunit;
using static Microsoft.SemanticKernel.TypeConverterFactory;

namespace SemanticKernel.UnitTests;

/// <summary>
/// Represents a factory for asserting type converters.
/// </summary>
public sealed class AssertTypeConverterFactory
{
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomTypeWithCustomConverter
    {
        public string Foo { get; set; }
    }

#pragma warning disable CA1815
    private sealed class MyCustomTypeConverter : TypeConverter
#pragma warning restore CA1815
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        /// <summary>
        /// This method is used to convert object from string to actual type. This will allow to pass object to
        /// method function which requires it.
        /// </summary>
        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return new MyCustomTypeWithCustomConverter { Foo = "Bar" };
        }

        /// <summary>
        /// This method is used to convert actual type to string representation, so it can be passed to AI
        /// for further processing.
        /// </summary>
        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return "{\"Foo\":\"Bar\"}";
        }
    }

    /// <summary>
    /// Asserts the custom type type converter.
    /// </summary>
    [Fact]
    public static void ItCanCreateNativeConverterForCustomType()
    {
        var typeConverter = TypeConverterFactory.GetTypeConverter(typeof(MyCustomType));
        Assert.NotNull(typeConverter);
        Assert.IsType<JsonSerializationTypeConverter>(typeConverter);
    }

    /// <summary>
    /// Asserts the custom type type converter.
    /// </summary>
    [Fact]
    public static void ItCanSerializeCustomTypeUsingNativeConverter()
    {
        var typeConverter = TypeConverterFactory.GetTypeConverter(typeof(MyCustomType));
        Assert.Equal("{\"Number\":1,\"Text\":\"test\"}", typeConverter!.ConvertToInvariantString(new MyCustomType { Number = 1, Text = "test" }));
    }

    /// <summary>
    /// Asserts the custom type type converter.
    /// </summary>
    [Fact]
    public static void ItCanDeserializeCustomTypeUsingNativeConverter()
    {
        var typeConverter = TypeConverterFactory.GetTypeConverter(typeof(MyCustomType));
        Assert.Equal(new MyCustomType { Number = 1, Text = "test" }.ToString(), typeConverter!.ConvertFromInvariantString("{\"Number\":1,\"Text\":\"test\"}").ToString());
    }

    /// <summary>
    /// Asserts the custom type type converter.
    /// </summary>
    [Fact]
    public static void ItCanCreateCustomConverterForCustomType()
    {
        var typeConverter = TypeConverterFactory.GetTypeConverter(typeof(MyCustomTypeWithCustomConverter));
        Assert.NotNull(typeConverter);
        Assert.IsType<MyCustomTypeConverter>(typeConverter);
    }

    /// <summary>
    /// Asserts the custom type type converter.
    /// </summary>
    [Fact]
    public static void ItCanSerializeCustomTypeUsingCustomConverter()
    {
        var typeConverter = TypeConverterFactory.GetTypeConverter(typeof(MyCustomTypeWithCustomConverter));
        Assert.Equal("{\"Foo\":\"Bar\"}", typeConverter!.ConvertToInvariantString(new MyCustomTypeWithCustomConverter { Foo = "Bar" }));
    }

    /// <summary>
    /// Asserts the custom type type converter.
    /// </summary>
    [Fact]
    public static void ItCanDeserializeCustomTypeUsingCustomConverter()
    {
        var typeConverter = TypeConverterFactory.GetTypeConverter(typeof(MyCustomTypeWithCustomConverter));
        Assert.Equal(new MyCustomTypeWithCustomConverter { Foo = "Bar" }.ToString(), typeConverter!.ConvertFromInvariantString("{\"Foo\":\"Bar\"}").ToString());
    }
}
