---
status: proposed
contact: dehoward
date: 2023-11-06
deciders: alliscode, markwallace-microsoft
consulted:
informed:
---

# JSON Serializable Custom Types

## Context and Problem Statement

This ADR aims to simplify the usage of custom types by allowing developers to use any type that can be serialized using `System.Text.Json`.

Standardizing on a JSON-serializable type is necessary to allow functions to be described using a JSON Schema within a planner's function manual. Using a JSON Schema to describe a function's input and output types will allow the planner to validate that the function is being used correctly.

Today, use of custom types within Semantic Kernel requires developers to implement a custom `TypeConverter` to convert to/from the string representation of the type. This is demonstrated in [Example60_AdvancedNativeFunctions](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/KernelSyntaxExamples/Example60_AdvancedNativeFunctions.cs#L202C44-L202C44) as seen below:

```csharp
    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    private sealed class MyCustomTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<MyCustomType>((string)value);
        }

        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }
```

## Considered Options

**1. Use TypeConverter for primitive types and native serialization methods for custom types**
For this option, an attribute will not be required on the custom type by default as `JsonSerializer.Deserialize<object>()` will be used to convert from a string, and `JsonSerializer.Serialize()` used to convert to a string.

Preserving the use of the native `TypeConverter`s for primitive types is necessary to prevent any lossy conversions.

This could change the `GetTypeConverter()` method to look like the following, where before the `JsonConverterWrapper` wasn't needed and the function returned a `TypeConverter` instead of a `JsonConverter`:

```csharp
    private static JsonConverter? GetTypeConverter(Type targetType)
    {
        if (targetType == typeof(byte)) { return new JsonConverterWrapper(new ByteConverter()); }
        if (targetType == typeof(sbyte)) { return new JsonConverterWrapper(new SByteConverter()); }
        if (targetType == typeof(bool)) { return new JsonConverterWrapper(new BooleanConverter()); }
        if (targetType == typeof(ushort)) { return new JsonConverterWrapper(new UInt16Converter()); }
        if (targetType == typeof(short)) { return new JsonConverterWrapper(new Int16Converter()); }
        if (targetType == typeof(char)) { return new JsonConverterWrapper(new CharConverter()); }
        if (targetType == typeof(uint)) { return new JsonConverterWrapper(new UInt32Converter()); }
        if (targetType == typeof(int)) { return new JsonConverterWrapper(new Int32Converter()); }
        if (targetType == typeof(ulong)) { return new JsonConverterWrapper(new UInt64Converter()); }
        if (targetType == typeof(long)) { return new JsonConverterWrapper(new Int64Converter()); }
        if (targetType == typeof(float)) { return new JsonConverterWrapper(new SingleConverter()); }
        if (targetType == typeof(double)) { return new JsonConverterWrapper(new DoubleConverter()); }
        if (targetType == typeof(decimal)) { return new JsonConverterWrapper(new DecimalConverter()); }
        if (targetType == typeof(TimeSpan)) { return new JsonConverterWrapper(new TimeSpanConverter()); }
        if (targetType == typeof(DateTime)) { return new JsonConverterWrapper(new DateTimeConverter()); }
        if (targetType == typeof(DateTimeOffset)) { return new JsonConverterWrapper(new DateTimeOffsetConverter()); }
        if (targetType == typeof(Uri)) { return new JsonConverterWrapper(new UriTypeConverter()); }
        if (targetType == typeof(Guid)) { return new JsonConverterWrapper(new GuidConverter()); }

        if (targetType.GetCustomAttribute<JsonConverterAttribute>() is JsonConverterAttribute tca &&
            Type.GetType(tca.ConverterType.Name, throwOnError: false) is Type converterType &&
            Activator.CreateInstance(converterType) is JsonConverter converter)
        {
            return converter;
        }

        return new SimpleJsonConverter();
    }

    private class JsonConverterWrapper : JsonConverter<object> {
        private readonly TypeConverter _converter;

        public JsonConverterWrapper(TypeConverter converter)
        {
            this._converter = converter;
        }

        public override object Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            return this._converter.ConvertFromString(null, CultureInfo.InvariantCulture, reader.GetString());
        }

        public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
        {
            writer.WriteStringValue(this._converter.ConvertToString(null, CultureInfo.InvariantCulture, value));
        }
    }


    private class SimpleJsonConverter : JsonConverter<object>
    {
        public override object? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            return JsonSerializer.Deserialize(ref reader, typeToConvert, options);
        }

        public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
        {
            JsonSerializer.Serialize(writer, value, value.GetType(), options);
        }
    }

```

If a developer wants to customize the serialization and/or deserialization of a custom type, they can implement their own `JsonConverter` and apply the `JsonConverterAttribute` their custom type as seen below.

**Example usage of the `JsonConverter`** class and attribute:

```csharp
    [JsonConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    private sealed class MyCustomTypeConverter : JsonConverter<MyCustomType>
    {
        public override MyCustomType Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            return JsonSerializer.Deserialize<MyCustomType>(ref reader, options);
        }

        public override void Write(Utf8JsonWriter writer, MyCustomType value, JsonSerializerOptions options)
        {
            JsonSerializer.Serialize(writer, value, options);
        }
    }
```

_When is serialization/deserialization required?_

Required

- **Native to Semantic:** Passing variables from Native to Semantic **will** require serialization of the output of the Native Function from complex type to string so that it can be passed to the LLM.
- **Semantic to Native:** Passing variables from Semantic to Native **will** require de-serialization of the output of the Semantic Function between string to the complex type format that the Native Function is expecting.

Not required

- **Native to Native:** Passing variables from Native to Native **will not** require any serialization or deserialization as the complex type can be passed as-is.
- **Semantic to Semantic:** Passing variables from Semantic to Semantic **will not** require any serialization or deserialization as the the complex type will be passed around using its string representation.

**2. Only use native serialization methods**
This option was originally considered, which would have effectively removed the use of any of the native `TypeConverter`s in favor of the `SimpleJsonConverter` shown above, but it was pointed out that this may result in lossy conversion between primitive types. For example, when converting from a `float` to an `int`, the primitive may be truncated in a way by the native serialization methods that does not provide an accurate result.

## Decision Outcome
