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

Today, use of custom types within Semantic Kernel requires developers to implement a custom `TypeConverter` to convert to/from the string representation of the type. This is demonstrated in [Functions/MethodFunctions_Advanced] as seen below:

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

The above approach will now only be needed when a custom type cannot be serialized using `System.Text.Json`.

## Considered Options

**1. Fallback to serialization using `System.Text.Json` if a `TypeConverter` is not available for the given type**

- Primitive types will be handled using their native `TypeConverter`s
  - We preserve the use of the native `TypeConverter` for primitive types to prevent any lossy conversions.
- Complex types will be handled by their registered `TypeConverter`, if provided.
- If no `TypeConverter` is registered for a complex type, our own `JsonSerializationTypeConverter` will be used to attempt JSON serialization/deserialization using `System.Text.Json`.
  - A detailed error message will be thrown if the type cannot be serialized/deserialized.

This will change the `GetTypeConverter()` method in `NativeFunction.cs` to look like the following, where before `null` was returned if no `TypeConverter` was found for the type:

```csharp
private static TypeConverter GetTypeConverter(Type targetType)
    {
        if (targetType == typeof(byte)) { return new ByteConverter(); }
        if (targetType == typeof(sbyte)) { return new SByteConverter(); }
        if (targetType == typeof(bool)) { return new BooleanConverter(); }
        if (targetType == typeof(ushort)) { return new UInt16Converter(); }
        if (targetType == typeof(short)) { return new Int16Converter(); }
        if (targetType == typeof(char)) { return new CharConverter(); }
        if (targetType == typeof(uint)) { return new UInt32Converter(); }
        if (targetType == typeof(int)) { return new Int32Converter(); }
        if (targetType == typeof(ulong)) { return new UInt64Converter(); }
        if (targetType == typeof(long)) { return new Int64Converter(); }
        if (targetType == typeof(float)) { return new SingleConverter(); }
        if (targetType == typeof(double)) { return new DoubleConverter(); }
        if (targetType == typeof(decimal)) { return new DecimalConverter(); }
        if (targetType == typeof(TimeSpan)) { return new TimeSpanConverter(); }
        if (targetType == typeof(DateTime)) { return new DateTimeConverter(); }
        if (targetType == typeof(DateTimeOffset)) { return new DateTimeOffsetConverter(); }
        if (targetType == typeof(Uri)) { return new UriTypeConverter(); }
        if (targetType == typeof(Guid)) { return new GuidConverter(); }

        if (targetType.GetCustomAttribute<TypeConverterAttribute>() is TypeConverterAttribute tca &&
            Type.GetType(tca.ConverterTypeName, throwOnError: false) is Type converterType &&
            Activator.CreateInstance(converterType) is TypeConverter converter)
        {
            return converter;
        }

        // now returns a JSON-serializing TypeConverter by default, instead of returning null
        return new JsonSerializationTypeConverter();
    }

    private sealed class JsonSerializationTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<object>((string)value);
        }

        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
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
This option was originally considered, which would have effectively removed the use of the `TypeConverter`s in favor of a simple `JsonConverter`, but it was pointed out that this may result in lossy conversion between primitive types. For example, when converting from a `float` to an `int`, the primitive may be truncated in a way by the native serialization methods that does not provide an accurate result.

## Decision Outcome
