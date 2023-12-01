// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Reflection;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Factory for creating TypeConverter instances based on a provided type.
/// </summary>
internal static class TypeConverterFactory
{
    /// <summary>
    /// Returns a TypeConverter instance for the specified type.
    /// </summary>
    /// <param name="type">The Type of the object to convert.</param>
    /// <returns>A TypeConverter instance if a suitable converter is found, otherwise null.</returns>
    internal static TypeConverter? GetTypeConverter(Type type)
    {
        // In an ideal world, this would use TypeDescriptor.GetConverter. However, that is not friendly to
        // any form of ahead-of-time compilation, as it could end up requiring functionality that was trimmed.
        // Instead, we just use a hard-coded set of converters for the types we know about and then also support
        // types that are explicitly attributed with TypeConverterAttribute.

        if (type == typeof(string)) { return new StringConverter(); }
        if (type == typeof(byte)) { return new ByteConverter(); }
        if (type == typeof(sbyte)) { return new SByteConverter(); }
        if (type == typeof(bool)) { return new BooleanConverter(); }
        if (type == typeof(ushort)) { return new UInt16Converter(); }
        if (type == typeof(short)) { return new Int16Converter(); }
        if (type == typeof(char)) { return new CharConverter(); }
        if (type == typeof(uint)) { return new UInt32Converter(); }
        if (type == typeof(int)) { return new Int32Converter(); }
        if (type == typeof(ulong)) { return new UInt64Converter(); }
        if (type == typeof(long)) { return new Int64Converter(); }
        if (type == typeof(float)) { return new SingleConverter(); }
        if (type == typeof(double)) { return new DoubleConverter(); }
        if (type == typeof(decimal)) { return new DecimalConverter(); }
        if (type == typeof(TimeSpan)) { return new TimeSpanConverter(); }
        if (type == typeof(DateTime)) { return new DateTimeConverter(); }
        if (type == typeof(DateTimeOffset)) { return new DateTimeOffsetConverter(); }
        if (type == typeof(Uri)) { return new UriTypeConverter(); }
        if (type == typeof(Guid)) { return new GuidConverter(); }
        if (type.IsEnum) { return new EnumConverter(type); }

        if (type.GetCustomAttribute<TypeConverterAttribute>() is TypeConverterAttribute tca &&
            Type.GetType(tca.ConverterTypeName, throwOnError: false) is Type converterType &&
            Activator.CreateInstance(converterType) is TypeConverter converter)
        {
            return converter;
        }

        return null;
    }
}
