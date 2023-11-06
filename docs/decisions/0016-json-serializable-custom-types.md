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

This ADR aims to simplify the usage of custom types by allowing developers to use any type that can be serialized using `System.Text.Json`.

## Considered Options

**1. Use native serialization methods**
By default, an attribute will not be required on the custom type as `JsonSerializer.Deserialize<object>()` will be used to convert from a string, and `JsonSerializer.Serialize()` used to convert to a string. If a developer wants to customize the serialization and/or deserialization of a custom type, a custom `JsonConverter` can be implemented and the `JsonConverterAttribute` applied to the custom type as seen below.

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

## Decision Outcome
