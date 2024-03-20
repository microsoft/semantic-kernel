using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace JsonSchemaMapper;

/// <summary>
/// Maps .NET types to JSON schema objects using contract metadata from <see cref="JsonTypeInfo"/> instances.
/// </summary>
internal static class JsonSchemaMapper
{
    /// <summary>
    /// The JSON schema draft version used by the generated schemas.
    /// </summary>
    public const string SchemaVersion = "https://json-schema.org/draft/2020-12/schema";

    /// <summary>
    /// Generates a JSON schema corresponding to the contract metadata of the specified type.
    /// </summary>
    /// <param name="options">The options instance from which to resolve the contract metadata.</param>
    /// <param name="type">The root type for which to generate the JSON schema.</param>
    /// <param name="configuration">The configuration object controlling the schema generation.</param>
    /// <returns>A new <see cref="JsonObject"/> instance defining the JSON schema for <paramref name="type"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    /// <exception cref="InvalidOperationException">The <paramref name="options"/> instance is not marked as read-only.</exception>
    public static JsonObject GetJsonSchema(this JsonSerializerOptions options, Type type, JsonSchemaMapperConfiguration? configuration = null)
    {
        if (options is null)
        {
           ThrowHelpers.ThrowArgumentNullException(nameof(options));
        }

        if (type is null)
        {
            ThrowHelpers.ThrowArgumentNullException(nameof(type));
        }

        if (!options.IsReadOnly)
        {
            Throw();
            static void Throw() => throw new InvalidOperationException("The options instance must be read-only");
        }

        JsonTypeInfo typeInfo = options.GetTypeInfo(type);
        return ToJsonSchemaCore(typeInfo, configuration);
    }

    /// <summary>
    /// Generates a JSON schema corresponding to the specified contract metadata.
    /// </summary>
    /// <param name="typeInfo">The contract metadata for which to generate the schema.</param>
    /// <param name="configuration">The configuration object controlling the schema generation.</param>
    /// <returns>A new <see cref="JsonObject"/> instance defining the JSON schema for <paramref name="typeInfo"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    public static JsonObject ToJsonSchema(this JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration? configuration = null)
    {
        if (typeInfo is null)
        {
            ThrowHelpers.ThrowArgumentNullException(nameof(typeInfo));
        }

        return ToJsonSchemaCore(typeInfo, configuration);
    }

    private static JsonObject ToJsonSchemaCore(JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration? configuration)
    {
        if (typeInfo.Options.ReferenceHandler == ReferenceHandler.Preserve)
        {
            Throw();
            static void Throw() => throw new NotSupportedException("Schema generation not supported with ReferenceHandler.Preserve enabled.");
        }

        typeInfo.MakeReadOnly();
        var state = new GenerationState(configuration ?? JsonSchemaMapperConfiguration.Default);
        return MapJsonSchemaCore(typeInfo, ref state);
    }

    private static JsonObject MapJsonSchemaCore(
        JsonTypeInfo typeInfo,
        ref GenerationState state,
        string? description = null,
        JsonConverter? customConverter = null,
        JsonNumberHandling? customNumberHandling = null,
        KeyValuePair<string, JsonNode?>? derivedTypeDiscriminator = null,
        Type? parentNullableOfT = null)
    {
        Debug.Assert(typeInfo.IsReadOnly);

        Type type = typeInfo.Type;
        JsonConverter effectiveConverter = customConverter ?? typeInfo.Converter;
        JsonNumberHandling? effectiveNumberHandling = customNumberHandling ?? typeInfo.NumberHandling;
        bool emitsTypeDiscriminator = derivedTypeDiscriminator?.Value is not null;

        if (!IsBuiltInConverter(effectiveConverter))
        {
            return new JsonObject(); // We can't make any schema determinations if a custom converter is used
        }

        if (!emitsTypeDiscriminator && state.TryGetGeneratedSchemaPath(parentNullableOfT ?? type, effectiveConverter, out string? typePath))
        {
            // Schema for type has already been generated, return a reference to it.
            // For derived types using discriminators, the schema is generated inline.
            return new JsonObject { [RefPropertyName] = typePath };
        }

        if (state.Configuration.ResolveDescriptionAttributes)
        {
            description ??= type.GetCustomAttribute<DescriptionAttribute>()?.Description;
        }

        if (TryGetNullableElement(type, out Type? nullableElementType))
        {
            // Nullable<T> types must be handled separately
            JsonTypeInfo nullableElementTypeInfo = typeInfo.Options.GetTypeInfo(nullableElementType);
            customConverter = ExtractCustomNullableConverter(customConverter);

            return MapJsonSchemaCore(
                nullableElementTypeInfo,
                ref state,
                description,
                customConverter,
                parentNullableOfT: type);
        }

        if (!emitsTypeDiscriminator && typeInfo.Kind != JsonTypeInfoKind.None)
        {
            // For complex types such objects, arrays, and dictionaries register the current path
            // so that it can be referenced by later occurrences in the type graph. Do not register
            // types in a polymorphic hierarchy using discriminators as they need to be inlined.
            state.RegisterTypePath(parentNullableOfT ?? type, effectiveConverter);
        }

        JsonSchemaType schemaType = JsonSchemaType.Any;
        string? format = null;
        JsonObject? properties = null;
        JsonArray? requiredProperties = null;
        JsonObject? arrayItems = null;
        JsonNode? additionalProperties = null;
        JsonArray? enumValues = null;
        JsonArray? anyOfTypes = null;

        if (derivedTypeDiscriminator is null && typeInfo.PolymorphismOptions is { DerivedTypes.Count: > 0 } polyOptions)
        {
            // This is the base type of a polymorphic type hierarchy. The schema for this type
            // will include an "anyOf" property with the schemas for all derived types.

            string typeDiscriminatorKey = polyOptions.TypeDiscriminatorPropertyName;
            var derivedTypes = polyOptions.DerivedTypes.ToList();

            if (!type.IsAbstract && derivedTypes.Any(derived => derived.DerivedType == type))
            {
                // For non-abstract base types that haven't been explicitly configured,
                // add a trivial schema to the derived types since we should support it.
                derivedTypes.Add(new JsonDerivedType(type));
            }

            state.Push(AnyOfPropertyName);
            anyOfTypes = new JsonArray();

            int i = 0;
            foreach (JsonDerivedType derivedType in derivedTypes)
            {
                Debug.Assert(derivedType.TypeDiscriminator is null or int or string);
                JsonNode? typeDiscriminatorPropertySchema = derivedType.TypeDiscriminator switch
                {
                    null => null,
                    int intId => new JsonObject { [ConstPropertyName] = (JsonNode)intId },
                    object stringId => new JsonObject { [ConstPropertyName] = (JsonNode)(string)stringId }
                };

                JsonTypeInfo derivedTypeInfo = typeInfo.Options.GetTypeInfo(derivedType.DerivedType);

                state.Push(i++.ToString(CultureInfo.InvariantCulture));
                JsonObject derivedSchema = MapJsonSchemaCore(
                    derivedTypeInfo, ref state,
                    derivedTypeDiscriminator: new(typeDiscriminatorKey, typeDiscriminatorPropertySchema));
                state.Pop();

                anyOfTypes.Add((JsonNode)derivedSchema);
            }

            state.Pop();
            goto ConstructSchemaDocument;
        }

        switch (typeInfo.Kind)
        {
            case JsonTypeInfoKind.None:
                if (s_simpleTypeInfo.TryGetValue(type, out var simpleTypeInfo))
                {
                    schemaType = simpleTypeInfo.SchemaType;
                    format = simpleTypeInfo.Format;

                    if (effectiveNumberHandling is JsonNumberHandling numberHandling &&
                        schemaType is JsonSchemaType.Integer or JsonSchemaType.Number)
                    {
                        if ((numberHandling & (JsonNumberHandling.AllowReadingFromString | JsonNumberHandling.WriteAsString)) != 0)
                        {
                            schemaType |= JsonSchemaType.String;
                        }
                        else if (numberHandling is JsonNumberHandling.AllowNamedFloatingPointLiterals)
                        {
                            anyOfTypes = new JsonArray()
                            {
                                new JsonObject { [TypePropertyName] = MapSchemaType(schemaType) },
                                new JsonObject
                                {
                                    [EnumPropertyName] = new JsonArray { (JsonNode)"NaN", (JsonNode)"Infinity", (JsonNode)"-Infinity" }
                                }
                            };

                            schemaType = JsonSchemaType.Any; // reset the parent setting
                        }
                    }
                }
                else if (type.IsEnum)
                {
                    if (TryGetStringEnumConverterValues(typeInfo, effectiveConverter, out JsonArray? values))
                    {
                        if (values is null)
                        {
                            // enum declared with the flags attribute -- do not surface enum values in the JSON schema.
                            schemaType = JsonSchemaType.String;
                        }
                        else
                        {
                            if (parentNullableOfT != null)
                            {
                                // We're generating the schema for a nullable
                                // enum type. Append null to the "enum" array.
                                values.Add(null);
                            }

                            enumValues = values;
                        }
                    }
                    else
                    {
                        schemaType = JsonSchemaType.Integer;
                    }
                }

                break;

            case JsonTypeInfoKind.Object:
                schemaType = JsonSchemaType.Object;

                if (typeInfo.UnmappedMemberHandling is JsonUnmappedMemberHandling.Disallow)
                {
                    // Disallow unspecified properties.
                    additionalProperties = false;
                }

                if (emitsTypeDiscriminator)
                {
                    Debug.Assert(derivedTypeDiscriminator?.Value is not null);
                    (properties ??= new()).Add(derivedTypeDiscriminator!.Value);
                    (requiredProperties ??= new()).Add((JsonNode)derivedTypeDiscriminator.Value.Key);
                }

                state.Push(PropertiesPropertyName);
                foreach (JsonPropertyInfo property in typeInfo.Properties)
                {
                    if (property is { Get: null, Set: null })
                    {
                        continue; // Skip [JsonIgnore] property
                    }

                    if (property.IsExtensionData)
                    {
                        continue; // Extension data properties don't impact the schema.
                    }

                    JsonNumberHandling? propertyNumberHandling = property.NumberHandling ?? effectiveNumberHandling;
                    JsonTypeInfo propertyTypeInfo = typeInfo.Options.GetTypeInfo(property.PropertyType);
                    string? propertyDescription = state.Configuration.ResolveDescriptionAttributes
                        ? property.AttributeProvider?.GetCustomAttributes(inherit: true).OfType<DescriptionAttribute>().FirstOrDefault()?.Description
                        : null;

                    state.Push(property.Name);
                    JsonObject propertySchema = MapJsonSchemaCore(propertyTypeInfo, ref state, propertyDescription, property.CustomConverter, propertyNumberHandling);
                    state.Pop();

                    (properties ??= new()).Add(property.Name, propertySchema);

                    if (property.IsRequired)
                    {
                        (requiredProperties ??= new()).Add((JsonNode)property.Name);
                    }
                }
                state.Pop();

                break;

            case JsonTypeInfoKind.Enumerable:
                Type elementType = GetElementType(typeInfo);
                JsonTypeInfo elementTypeInfo = typeInfo.Options.GetTypeInfo(elementType);

                if (emitsTypeDiscriminator)
                {
                    Debug.Assert(derivedTypeDiscriminator != null);

                    // Polymorphic enumerable types are represented using a wrapping object:
                    // { "$type" : "discriminator", "$values" : [element1, element2, ...] }
                    // Which corresponds to the schema
                    // { "properties" : { "$type" : { "const" : "discriminator" }, "$values" : { "type" : "array", "items" : { ... } } } }

                    schemaType = JsonSchemaType.Object;
                    (properties ??= new()).Add(derivedTypeDiscriminator!.Value);
                    (requiredProperties ??= new()).Add((JsonNode)derivedTypeDiscriminator.Value.Key);

                    state.Push(PropertiesPropertyName);
                    state.Push(StjValuesMetadataProperty);
                    state.Push(ItemsPropertyName);
                    JsonObject elementSchema = MapJsonSchemaCore(elementTypeInfo, ref state);
                    state.Pop();
                    state.Pop();
                    state.Pop();

                    properties.Add(StjValuesMetadataProperty,
                        new JsonObject
                        {
                            [TypePropertyName] = MapSchemaType(JsonSchemaType.Array),
                            [ItemsPropertyName] = elementSchema
                        });
                }
                else
                {
                    schemaType = JsonSchemaType.Array;

                    state.Push(ItemsPropertyName);
                    arrayItems = MapJsonSchemaCore(elementTypeInfo, ref state);
                    state.Pop();
                }

                break;

            case JsonTypeInfoKind.Dictionary:
                schemaType = JsonSchemaType.Object;
                Type valueType = GetElementType(typeInfo);
                JsonTypeInfo valueTypeInfo = typeInfo.Options.GetTypeInfo(valueType);

                if (emitsTypeDiscriminator)
                {
                    Debug.Assert(derivedTypeDiscriminator?.Value is not null);
                    (properties ??= new()).Add(derivedTypeDiscriminator!.Value);
                    (requiredProperties ??= new()).Add((JsonNode)derivedTypeDiscriminator.Value.Key);
                }

                state.Push(AdditionalPropertiesPropertyName);
                additionalProperties = MapJsonSchemaCore(valueTypeInfo, ref state);
                state.Pop();

                break;

            default:
                Debug.Fail("Unreachable code");
                break;
        }

        if (schemaType != JsonSchemaType.Any &&
            (type.IsValueType ? parentNullableOfT != null : state.Configuration.AllowNullForReferenceTypes))
        {
            // Add null support for nullable types and reference types when configured.
            // NB STJ does not currently honor non-nullable reference type annotations.
            // cf. https://github.com/dotnet/runtime/issues/1256
            schemaType |= JsonSchemaType.Null;
        }

    ConstructSchemaDocument:
        return CreateSchemaDocument(
            description,
            schemaType,
            format,
            properties,
            requiredProperties,
            arrayItems,
            additionalProperties,
            enumValues,
            anyOfTypes,
            state);
    }

    private ref struct GenerationState
    {
        private readonly List<string>? _currentPath;
        private readonly Dictionary<(Type, JsonConverter), string>? _typePaths;
        private int _currentDepth = 0;

        public GenerationState(JsonSchemaMapperConfiguration configuration)
        {
            this.Configuration = configuration;
            this._currentPath = configuration.AllowSchemaReferences ? new() : null;
            this._typePaths = configuration.AllowSchemaReferences ? new() : null;
        }

        public readonly JsonSchemaMapperConfiguration Configuration { get; }
        public readonly int CurrentDepth => this._currentDepth;

        public void Push(string nodeId)
        {
            if (this._currentDepth == this.Configuration.MaxDepth)
            {
                Throw();
                static void Throw() => throw new InvalidOperationException("The maximum depth of the schema has been reached.");
            }

            this._currentDepth++;

            if (this.Configuration.AllowSchemaReferences)
            {
                Debug.Assert(this._currentPath != null);
                this._currentPath!.Add(nodeId);
            }
        }

        public void Pop()
        {
            Debug.Assert(this._currentDepth > 0);
            this._currentDepth--;

            if (this.Configuration.AllowSchemaReferences)
            {
                Debug.Assert(this._currentPath != null);
                this._currentPath!.RemoveAt(this._currentPath.Count - 1);
            }
        }

        public readonly void RegisterTypePath(Type type, JsonConverter converter)
        {
            if (this.Configuration.AllowSchemaReferences)
            {
                Debug.Assert(this._currentPath != null);
                Debug.Assert(this._typePaths != null);

                string pointer = this._currentDepth == 0 ? "#" : "#/" + string.Join("/", this._currentPath);
                this._typePaths!.Add((type, converter), pointer);
            }
        }

        public readonly bool TryGetGeneratedSchemaPath(Type type, JsonConverter converter, [NotNullWhen(true)]out string? value)
        {
            if (this.Configuration.AllowSchemaReferences)
            {
                Debug.Assert(this._typePaths != null);
                return this._typePaths!.TryGetValue((type, converter), out value);
            }

            value = null;
            return false;
        }
    }

    private static JsonObject CreateSchemaDocument(
        string? description,
        JsonSchemaType schemaType,
        string? format,
        JsonObject? properties,
        JsonArray? requiredProperties,
        JsonObject? arrayItems,
        JsonNode? additionalProperties,
        JsonArray? enumValues,
        JsonArray? anyOfSchema,
        GenerationState state)
    {
        var schema = new JsonObject();

        if (state.CurrentDepth == 0 && state.Configuration.IncludeSchemaVersion)
        {
            schema.Add(SchemaPropertyName, SchemaVersion);
        }

        if (description is not null)
        {
            schema.Add(DescriptionPropertyName, description);
        }

        if (MapSchemaType(schemaType) is JsonNode type)
        {
            schema.Add(TypePropertyName, type);
        }

        if (format is not null)
        {
            schema.Add(FormatPropertyName, format);
        }

        if (properties is not null)
        {
            schema.Add(PropertiesPropertyName, properties);
        }

        if (requiredProperties is not null)
        {
            schema.Add(RequiredPropertyName, requiredProperties);
        }

        if (arrayItems is not null)
        {
            schema.Add(ItemsPropertyName, arrayItems);
        }

        if (additionalProperties is not null)
        {
            schema.Add(AdditionalPropertiesPropertyName, additionalProperties);
        }

        if (enumValues is not null)
        {
            schema.Add(EnumPropertyName, enumValues);
        }

        if (anyOfSchema is not null)
        {
            schema.Add(AnyOfPropertyName, anyOfSchema);
        }

        return schema;
    }

    [Flags]
    private enum JsonSchemaType
    {
        Any = 0, // No type declared on the schema
        Null = 1,
        Boolean = 2,
        Integer = 4,
        Number = 8,
        String = 16,
        Array = 32,
        Object = 64,
    }

    private readonly static JsonSchemaType[] s_schemaValues = {
        // NB the order of these values influences order of types in the rendered schema
        JsonSchemaType.String,
        JsonSchemaType.Integer,
        JsonSchemaType.Number,
        JsonSchemaType.Boolean,
        JsonSchemaType.Array,
        JsonSchemaType.Object,
        JsonSchemaType.Null
    };

    private static JsonNode? MapSchemaType(JsonSchemaType schemaType)
    {
        return schemaType switch
        {
            JsonSchemaType.Any => null,
            JsonSchemaType.Null => "null",
            JsonSchemaType.Boolean => "boolean",
            JsonSchemaType.Integer => "integer",
            JsonSchemaType.Number => "number",
            JsonSchemaType.String => "string",
            JsonSchemaType.Array => "array",
            JsonSchemaType.Object => "object",
            _ => MapCompositeSchemaType(schemaType),
        };

        static JsonArray MapCompositeSchemaType(JsonSchemaType schemaType)
        {
            var array = new JsonArray();
            foreach (JsonSchemaType type in s_schemaValues)
            {
                if ((schemaType & type) != 0)
                {
                    array.Add(MapSchemaType(type));
                }
            }

            return array;
        }
    }

    private static bool IsBuiltInConverter(JsonConverter converter)
        => converter.GetType().Assembly == typeof(JsonConverter).Assembly;

    private static Type GetElementType(JsonTypeInfo typeInfo)
    {
        // Workaround for https://github.com/dotnet/runtime/issues/77306#issuecomment-2007887560
        Debug.Assert(typeInfo.Kind is JsonTypeInfoKind.Enumerable or JsonTypeInfoKind.Dictionary);
        return (Type)typeof(JsonTypeInfo).GetProperty("ElementType", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(typeInfo)!;
    }

    private static bool TryGetStringEnumConverterValues(JsonTypeInfo typeInfo, JsonConverter converter, out JsonArray? values)
    {
        Debug.Assert(typeInfo.Type.IsEnum && IsBuiltInConverter(converter));

        if (converter is JsonConverterFactory factory)
        {
            converter = factory.CreateConverter(typeInfo.Type, typeInfo.Options)!;
        }

        // There is unfortunately no way in which we can obtain enum converter configuration without resorting to private reflection
        // https://github.com/dotnet/runtime/blob/5fda47434cecc590095e9aef3c4e560b7b7ebb47/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Converters/Value/EnumConverter.cs#L23-L25
        FieldInfo? converterOptionsField = converter.GetType().GetField("_converterOptions", BindingFlags.Instance | BindingFlags.NonPublic);
        FieldInfo? namingPolicyField = converter.GetType().GetField("_namingPolicy", BindingFlags.Instance | BindingFlags.NonPublic);
        Debug.Assert(converterOptionsField != null);
        Debug.Assert(namingPolicyField != null);

        const int EnumConverterOptionsAllowStrings = 1;
        var converterOptions = (int)converterOptionsField!.GetValue(converter)!;
        if ((converterOptions & EnumConverterOptionsAllowStrings) != 0)
        {
            if (typeInfo.Type.GetCustomAttribute<FlagsAttribute>() is not null)
            {
                // For enums implemented as flags do not surface values in the JSON schema.
                values = null;
            }
            else
            {
                var namingPolicy = (JsonNamingPolicy?)namingPolicyField!.GetValue(converter)!;
                string[] names = Enum.GetNames(typeInfo.Type);
                values = new JsonArray();
                foreach (string name in names)
                {
                    string effectiveName = namingPolicy?.ConvertName(name) ?? name;
                    values.Add((JsonNode)effectiveName);
                }
            }

            return true;
        }

        values = null;
        return false;
    }

    private static JsonConverter? ExtractCustomNullableConverter(JsonConverter? converter)
    {
        Debug.Assert(converter is null || IsBuiltInConverter(converter));

        // There is unfortunately no way in which we can obtain the element converter from a nullable converter without resorting to private reflection
        // https://github.com/dotnet/runtime/blob/5fda47434cecc590095e9aef3c4e560b7b7ebb47/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Converters/Value/NullableConverter.cs#L15-L17
        if (converter != null && converter.GetType().Name == "NullableConverter`1")
        {
            FieldInfo? elementConverterField = converter.GetType().GetField("_elementConverter", BindingFlags.Instance | BindingFlags.NonPublic);
            Debug.Assert(elementConverterField != null);
            return (JsonConverter)elementConverterField!.GetValue(converter)!;
        }

        return null;
    }

    private static bool TryGetNullableElement(Type type, [NotNullWhen(true)] out Type? elementType)
    {
        if (type.IsValueType && type.IsGenericType && type.GetGenericTypeDefinition() == typeof(Nullable<>))
        {
            elementType = type.GetGenericArguments()[0];
            return true;
        }

        elementType = null;
        return false;
    }

    private const string SchemaPropertyName = "$schema";
    private const string RefPropertyName = "$ref";
    private const string DescriptionPropertyName = "description";
    private const string TypePropertyName = "type";
    private const string FormatPropertyName = "format";
    private const string PropertiesPropertyName = "properties";
    private const string RequiredPropertyName = "required";
    private const string ItemsPropertyName = "items";
    private const string AdditionalPropertiesPropertyName = "additionalProperties";
    private const string EnumPropertyName = "enum";
    private const string AnyOfPropertyName = "anyOf";
    private const string ConstPropertyName = "const";
    private const string StjValuesMetadataProperty = "$values";

    private static Dictionary<Type, (JsonSchemaType SchemaType, string? Format)> s_simpleTypeInfo = new()
    {
        [typeof(object)] = (JsonSchemaType.Any, null),
        [typeof(bool)] = (JsonSchemaType.Boolean, null),
        [typeof(byte)] = (JsonSchemaType.Integer, null),
        [typeof(ushort)] = (JsonSchemaType.Integer, null),
        [typeof(uint)] = (JsonSchemaType.Integer, null),
        [typeof(ulong)] = (JsonSchemaType.Integer, null),
        [typeof(sbyte)] = (JsonSchemaType.Integer, null),
        [typeof(short)] = (JsonSchemaType.Integer, null),
        [typeof(int)] = (JsonSchemaType.Integer, null),
        [typeof(long)] = (JsonSchemaType.Integer, null),
        [typeof(float)] = (JsonSchemaType.Number, null),
        [typeof(double)] = (JsonSchemaType.Number, null),
        [typeof(decimal)] = (JsonSchemaType.Number, null),
#if NET7_0_OR_GREATER
        [typeof(UInt128)] = (JsonSchemaType.Integer, null),
        [typeof(Int128)] = (JsonSchemaType.Integer, null),
        [typeof(Half)] = (JsonSchemaType.Number, null),
#endif
        [typeof(char)] = (JsonSchemaType.String, null),
        [typeof(string)] = (JsonSchemaType.String, null),
        [typeof(byte[])] = (JsonSchemaType.String, null),
        [typeof(Memory<byte>)] = (JsonSchemaType.String, null),
        [typeof(ReadOnlyMemory<byte>)] = (JsonSchemaType.String, null),
        [typeof(DateTime)] = (JsonSchemaType.String, Format: "date-time"),
        [typeof(DateTimeOffset)] = (JsonSchemaType.String, Format: "date-time"),
        [typeof(TimeSpan)] = (JsonSchemaType.String, Format: "time"),
#if NET6_0_OR_GREATER
        [typeof(DateOnly)] = (JsonSchemaType.String, Format: "date"),
        [typeof(TimeOnly)] = (JsonSchemaType.String, Format: "time"),
#endif
        [typeof(Guid)] = (JsonSchemaType.String, Format: "uuid"),
        [typeof(Uri)] = (JsonSchemaType.String, Format: "uri"),
        [typeof(Version)] = (JsonSchemaType.String, null),
        [typeof(JsonDocument)] = (JsonSchemaType.Any, null),
        [typeof(JsonElement)] = (JsonSchemaType.Any, null),
        [typeof(JsonNode)] = (JsonSchemaType.Any, null),
        [typeof(JsonValue)] = (JsonSchemaType.Any, null),
        [typeof(JsonObject)] = (JsonSchemaType.Object, null),
        [typeof(JsonArray)] = (JsonSchemaType.Array, null),
    };

    private static class ThrowHelpers
    {
        [DoesNotReturn]
        public static void ThrowArgumentNullException(string name) => throw new ArgumentNullException(name);
    }
}
