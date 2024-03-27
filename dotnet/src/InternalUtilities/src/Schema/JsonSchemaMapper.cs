// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

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
#if EXPOSE_JSON_SCHEMA_MAPPER
    public
#else
    internal
#endif
    static partial class JsonSchemaMapper
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
    /// <exception cref="NotSupportedException">The <paramref name="options"/> parameter contains unsupported configuration.</exception>
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

        ValidateOptions(options);

        JsonTypeInfo typeInfo = options.GetTypeInfo(type);
        var state = new GenerationState(configuration ?? JsonSchemaMapperConfiguration.Default);
        return MapJsonSchemaCore(typeInfo, ref state);
    }

    /// <summary>
    /// Generates a JSON object schema with properties corresponding to the specified method parameters.
    /// </summary>
    /// <param name="options">The options instance from which to resolve the contract metadata.</param>
    /// <param name="method">The method from whose parameters to generate the JSON schema.</param>
    /// <param name="configuration">The configuration object controlling the schema generation.</param>
    /// <returns>A new <see cref="JsonObject"/> instance defining the JSON schema for <paramref name="method"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    /// <exception cref="NotSupportedException">The <paramref name="options"/> parameter contains unsupported configuration.</exception>
    public static JsonObject GetJsonSchema(this JsonSerializerOptions options, MethodBase method, JsonSchemaMapperConfiguration? configuration = null)
    {
        if (options is null)
        {
            ThrowHelpers.ThrowArgumentNullException(nameof(options));
        }

        if (method is null)
        {
            ThrowHelpers.ThrowArgumentNullException(nameof(method));
        }

        ValidateOptions(options);

        configuration ??= JsonSchemaMapperConfiguration.Default;
        string description = (configuration.ResolveDescriptionAttributes ? method.GetCustomAttribute<DescriptionAttribute>()?.Description : null) ?? method.Name;

        JsonObject schema = new()
        {
            [DescriptionPropertyName] = description,
            [TypePropertyName] = "object",
        };

        ParameterInfo[] parameters = method.GetParameters();
        if (parameters.Length == 0)
        {
            return schema;
        }

        var state = new GenerationState(configuration);
        JsonObject paramSchemas = new();
        JsonArray? requiredParams = null;

        foreach (ParameterInfo parameter in parameters)
        {
            if (parameter.Name is null)
            {
                ThrowHelpers.ThrowInvalidOperationException_TrimmedMethodParameters(method);
            }

            JsonTypeInfo parameterInfo = options.GetTypeInfo(parameter.ParameterType);
            bool isNullableReferenceType = false;
            string? parameterDescription = null;
            bool isRequired = false;

            ResolveParameterInfo(parameter, parameterInfo, ref state, ref parameterDescription, ref isNullableReferenceType, ref isRequired);

            state.Push(parameter.Name);
            JsonObject paramSchema = MapJsonSchemaCore(parameterInfo, ref state, parameterDescription, isNullableReferenceType: isNullableReferenceType);
            state.Pop();

            paramSchemas.Add(parameter.Name, paramSchema);
            if (isRequired)
            {
                (requiredParams ??= new()).Add((JsonNode)parameter.Name);
            }
        }

        schema.Add(PropertiesPropertyName, paramSchemas);
        if (requiredParams != null)
        {
            schema.Add(RequiredPropertyName, requiredParams);
        }

        return schema;
    }

    /// <summary>
    /// Generates a JSON schema corresponding to the specified contract metadata.
    /// </summary>
    /// <param name="typeInfo">The contract metadata for which to generate the schema.</param>
    /// <param name="configuration">The configuration object controlling the schema generation.</param>
    /// <returns>A new <see cref="JsonObject"/> instance defining the JSON schema for <paramref name="typeInfo"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    /// <exception cref="NotSupportedException">The <paramref name="typeInfo"/> parameter contains unsupported configuration.</exception>
    public static JsonObject GetJsonSchema(this JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration? configuration = null)
    {
        if (typeInfo is null)
        {
            ThrowHelpers.ThrowArgumentNullException(nameof(typeInfo));
        }

        ValidateOptions(typeInfo.Options);
        typeInfo.MakeReadOnly();

        var state = new GenerationState(configuration ?? JsonSchemaMapperConfiguration.Default);
        return MapJsonSchemaCore(typeInfo, ref state);
    }

    private static JsonObject MapJsonSchemaCore(
        JsonTypeInfo typeInfo,
        ref GenerationState state,
        string? description = null,
        JsonConverter? customConverter = null,
        bool isNullableReferenceType = false,
        JsonNumberHandling? customNumberHandling = null,
        KeyValuePair<string, JsonNode?>? derivedTypeDiscriminator = null,
        Type? parentNullableOfT = null)
    {
        Debug.Assert(typeInfo.IsReadOnly);

        Type type = typeInfo.Type;
        JsonConverter effectiveConverter = customConverter ?? typeInfo.Converter;
        JsonNumberHandling? effectiveNumberHandling = customNumberHandling ?? typeInfo.NumberHandling;
        bool emitsTypeDiscriminator = derivedTypeDiscriminator?.Value is not null;
        bool isCacheable = !emitsTypeDiscriminator && description is null;

        if (!IsBuiltInConverter(effectiveConverter))
        {
            return new JsonObject(); // We can't make any schema determinations if a custom converter is used
        }

        if (isCacheable && state.TryGetGeneratedSchemaPath(type, parentNullableOfT, customConverter, isNullableReferenceType, customNumberHandling, out string? typePath))
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

        if (isCacheable && typeInfo.Kind != JsonTypeInfoKind.None)
        {
            // For complex types such objects, arrays, and dictionaries register the current path
            // so that it can be referenced by later occurrences in the type graph. Do not register
            // types in a polymorphic hierarchy using discriminators as they need to be inlined.
            state.RegisterTypePath(type, parentNullableOfT, customConverter, isNullableReferenceType, customNumberHandling);
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
                    derivedTypeInfo,
                    ref state,
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
                            anyOfTypes = new JsonArray
                            {
                                (JsonNode)new JsonObject { [TypePropertyName] = MapSchemaType(schemaType) },
                                (JsonNode)new JsonObject
                                {
                                    [EnumPropertyName] = new JsonArray { (JsonNode)"NaN", (JsonNode)"Infinity", (JsonNode)"-Infinity" },
                                },
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

                Func<JsonPropertyInfo, ParameterInfo?> parameterInfoMapper = ResolveJsonConstructorParameterMapper(typeInfo);

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

                    // Only resolve nullability metadata for reference types.
                    NullabilityInfoContext? nullabilityCtx = !property.PropertyType.IsValueType ? state.NullabilityInfoContext : null;

                    // Only resolve the attribute provider if needed.
                    ICustomAttributeProvider? attributeProvider = state.Configuration.ResolveDescriptionAttributes || nullabilityCtx != null
                        ? ResolveAttributeProvider(typeInfo, property)
                        : null;

                    // Resolve property-level description attributes.
                    string? propertyDescription = state.Configuration.ResolveDescriptionAttributes
                        ? attributeProvider?.GetCustomAttributes(inherit: true).OfType<DescriptionAttribute>().FirstOrDefault()?.Description
                        : null;

                    // Declare the property as nullable if either getter or setter are nullable.
                    bool isPropertyNullableReferenceType = nullabilityCtx != null && attributeProvider is MemberInfo memberInfo
                        ? nullabilityCtx.GetMemberNullability(memberInfo) is { WriteState: NullabilityState.Nullable } or { ReadState: NullabilityState.Nullable }
                        : false;

                    bool isRequired = property.IsRequired;
                    if (parameterInfoMapper(property) is ParameterInfo ctorParam)
                    {
                        ResolveParameterInfo(
                            ctorParam,
                            propertyTypeInfo,
                            ref state,
                            ref propertyDescription,
                            ref isPropertyNullableReferenceType,
                            ref isRequired);
                    }

                    state.Push(property.Name);
                    JsonObject propertySchema = MapJsonSchemaCore(
                        propertyTypeInfo,
                        ref state,
                        propertyDescription,
                        property.CustomConverter,
                        isPropertyNullableReferenceType,
                        propertyNumberHandling);

                    state.Pop();

                    (properties ??= new()).Add(property.Name, propertySchema);

                    if (isRequired)
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

                    properties.Add(
                        StjValuesMetadataProperty,
                        new JsonObject
                        {
                            [TypePropertyName] = MapSchemaType(JsonSchemaType.Array),
                            [ItemsPropertyName] = elementSchema,
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
            (type.IsValueType ? parentNullableOfT != null : (isNullableReferenceType || !state.Configuration.ResolveNullableReferenceTypes)))
        {
            // Append "null" to the type array in the following cases:
            // 1. The type is a nullable value type or
            // 2. The type has been inferred to be a nullable reference type annotation or
            // 3. The type is a reference type and nullable reference types are not resolved (default STJ semantics).
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
            ref state);
    }

    private static void ResolveParameterInfo(
        ParameterInfo parameter,
        JsonTypeInfo parameterTypeInfo,
        ref GenerationState state,
        ref string? description,
        ref bool isNullableReferenceType,
        ref bool isRequired)
    {
        Debug.Assert(parameterTypeInfo.Type == parameter.ParameterType);

        if (state.Configuration.ResolveDescriptionAttributes)
        {
            // Resolve parameter-level description attributes.
            description ??= parameter.GetCustomAttribute<DescriptionAttribute>()?.Description;
        }

        if (!isNullableReferenceType && state.NullabilityInfoContext is { } ctx)
        {
            // Consult the nullability annotation of the constructor parameter if available.
            isNullableReferenceType = ctx.GetParameterNullability(parameter) is NullabilityState.Nullable;
        }

        if (parameter.HasDefaultValue)
        {
            // Append the default value to the description.
            string defaultValueJson = JsonSerializer.Serialize(parameter.DefaultValue, parameterTypeInfo);
            description = description is null
                ? $"default value: {defaultValueJson}"
                : $"{description} (default value: {defaultValueJson})";
        }
        else if (state.Configuration.RequireConstructorParameters)
        {
            // Parameter is not optional, mark as required.
            isRequired = true;
        }
    }

    private ref struct GenerationState
    {
        private readonly JsonSchemaMapperConfiguration _configuration;
        private readonly NullabilityInfoContext? _nullabilityInfoContext;
        private readonly Dictionary<(Type, JsonConverter? CustomConverter, bool IsNullableReferenceType, JsonNumberHandling? customNumberHandling), string>? _generatedTypePaths;
        private readonly List<string>? _currentPath;
        private int _currentDepth;

        public GenerationState(JsonSchemaMapperConfiguration configuration)
        {
            _configuration = configuration;
            _nullabilityInfoContext = configuration.ResolveNullableReferenceTypes ? new() : null;
            _generatedTypePaths = configuration.AllowSchemaReferences ? new() : null;
            _currentPath = configuration.AllowSchemaReferences ? new() : null;
            _currentDepth = 0;
        }

        public readonly JsonSchemaMapperConfiguration Configuration => _configuration;
        public readonly NullabilityInfoContext? NullabilityInfoContext => _nullabilityInfoContext;
        public readonly int CurrentDepth => _currentDepth;

        public void Push(string nodeId)
        {
            if (_currentDepth == Configuration.MaxDepth)
            {
                ThrowHelpers.ThrowInvalidOperationException_MaxDepthReached();
            }

            _currentDepth++;

            if (Configuration.AllowSchemaReferences)
            {
                Debug.Assert(_currentPath != null);
                _currentPath!.Add(nodeId);
            }
        }

        public void Pop()
        {
            Debug.Assert(_currentDepth > 0);
            _currentDepth--;

            if (Configuration.AllowSchemaReferences)
            {
                Debug.Assert(_currentPath != null);
                _currentPath!.RemoveAt(_currentPath.Count - 1);
            }
        }

        /// <summary>
        /// Associates the specified type configuration with the current path in the schema.
        /// </summary>
        public readonly void RegisterTypePath(Type type, Type? parentNullableOfT, JsonConverter? customConverter, bool isNullableReferenceType, JsonNumberHandling? customNumberHandling)
        {
            if (Configuration.AllowSchemaReferences)
            {
                Debug.Assert(_currentPath != null);
                Debug.Assert(_generatedTypePaths != null);

                string pointer = _currentDepth == 0 ? "#" : "#/" + string.Join("/", _currentPath);
                _generatedTypePaths!.Add((parentNullableOfT ?? type, customConverter, isNullableReferenceType, customNumberHandling), pointer);
            }
        }

        /// <summary>
        /// Looks up the schema path for the specified type configuration.
        /// </summary>
        public readonly bool TryGetGeneratedSchemaPath(Type type, Type? parentNullableOfT, JsonConverter? customConverter, bool isNullableReferenceType, JsonNumberHandling? customNumberHandling, [NotNullWhen(true)]out string? value)
        {
            if (Configuration.AllowSchemaReferences)
            {
                Debug.Assert(_generatedTypePaths != null);
                return _generatedTypePaths!.TryGetValue((parentNullableOfT ?? type, customConverter, isNullableReferenceType, customNumberHandling), out value);
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
        ref GenerationState state)
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

    private static readonly JsonSchemaType[] s_schemaValues = new[]
    {
        // NB the order of these values influences order of types in the rendered schema
        JsonSchemaType.String,
        JsonSchemaType.Integer,
        JsonSchemaType.Number,
        JsonSchemaType.Boolean,
        JsonSchemaType.Array,
        JsonSchemaType.Object,
        JsonSchemaType.Null,
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

    private static readonly Dictionary<Type, (JsonSchemaType SchemaType, string? Format)> s_simpleTypeInfo = new()
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
#if NET6_0_OR_GREATER
        [typeof(Half)] = (JsonSchemaType.Number, null),
#endif
#if NET7_0_OR_GREATER
        [typeof(UInt128)] = (JsonSchemaType.Integer, null),
        [typeof(Int128)] = (JsonSchemaType.Integer, null),
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

    private static void ValidateOptions(JsonSerializerOptions options)
    {
        if (options.ReferenceHandler == ReferenceHandler.Preserve)
        {
            ThrowHelpers.ThrowNotSupportedException_ReferenceHandlerPreserveNotSupported();
        }

        options.MakeReadOnly();
    }

    private static class ThrowHelpers
    {
        [DoesNotReturn]
        public static void ThrowArgumentNullException(string name) => throw new ArgumentNullException(name);

        [DoesNotReturn]
        public static void ThrowNotSupportedException_ReferenceHandlerPreserveNotSupported() =>
            throw new NotSupportedException("Schema generation not supported with ReferenceHandler.Preserve enabled.");

        [DoesNotReturn]
        public static void ThrowInvalidOperationException_TrimmedMethodParameters(MethodBase method) =>
            throw new InvalidOperationException($"The parameters for method '{method}' have been trimmed away.");

        [DoesNotReturn]
        public static void ThrowInvalidOperationException_MaxDepthReached() =>
            throw new InvalidOperationException("The maximum depth of the schema has been reached.");
    }
}