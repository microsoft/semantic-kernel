// Copyright (c) Microsoft. All rights reserved.

#if !NET9_0_OR_GREATER && !SYSTEM_TEXT_JSON_V9
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using System.Threading.Tasks;

namespace JsonSchemaMapper;

#if EXPOSE_JSON_SCHEMA_MAPPER
public
#else
internal
#endif
    static partial class JsonSchemaMapper
{
    // For System.Text.Json versions prior to v9, JsonSchemaMapper is implemented as a standalone component.
    // The implementation uses private reflection to access metadata not available with the older APIs of STJ.
    // While the implementation is forward compatible with .NET 9, it is not guaranteed that it will work with
    // later versions of .NET and users are encouraged to switch to the built-in JsonSchemaExporter eventually.

    private static partial JsonNode MapRootTypeJsonSchema(JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration configuration)
    {
        GenerationState state = new(configuration, typeInfo.Options);
        JsonSchema schema = MapJsonSchemaCore(ref state, typeInfo);
        return schema.ToJsonNode(configuration);
    }

    private static partial JsonNode MapMethodParameterJsonSchema(
        ParameterInfo parameterInfo,
        JsonTypeInfo parameterTypeInfo,
        JsonSchemaMapperConfiguration configuration,
        NullabilityInfoContext nullabilityContext,
        out bool isRequired)
    {
        Debug.Assert(parameterInfo.Name != null);

        GenerationState state = new(configuration, parameterTypeInfo.Options, nullabilityContext);

        string? parameterDescription = null;
        isRequired = false;

        ResolveParameterInfo(
            parameterInfo,
            parameterTypeInfo,
            state.NullabilityInfoContext,
            state.Configuration,
            out bool hasDefaultValue,
            out JsonNode? defaultValue,
            out bool isNonNullableType,
            ref parameterDescription,
            ref isRequired);

        state.PushSchemaNode(JsonSchemaConstants.PropertiesPropertyName);
        state.PushSchemaNode(parameterInfo.Name!);

        JsonSchema paramSchema = MapJsonSchemaCore(
            ref state,
            parameterTypeInfo,
            parameterInfo: parameterInfo,
            description: parameterDescription,
            isNonNullableType: isNonNullableType);

        if (hasDefaultValue)
        {
            paramSchema.DefaultValue = defaultValue;
            paramSchema.HasDefaultValue = true;
        }

        state.PopSchemaNode();
        state.PopSchemaNode();

        return paramSchema.ToJsonNode(configuration);
    }

    private static JsonSchema MapJsonSchemaCore(
        ref GenerationState state,
        JsonTypeInfo typeInfo,
        Type? parentType = null,
        JsonPropertyInfo? propertyInfo = null,
        ICustomAttributeProvider? propertyAttributeProvider = null,
        ParameterInfo? parameterInfo = null,
        bool isNonNullableType = false,
        JsonConverter? customConverter = null,
        JsonNumberHandling? customNumberHandling = null,
        JsonTypeInfo? parentPolymorphicTypeInfo = null,
        bool parentPolymorphicTypeContainsTypesWithoutDiscriminator = false,
        bool parentPolymorphicTypeIsNonNullable = false,
        KeyValuePair<string, JsonSchema>? typeDiscriminator = null,
        string? description = null,
        bool cacheResult = true)
    {
        Debug.Assert(typeInfo.IsReadOnly);

        if (cacheResult && state.TryPushType(typeInfo, propertyInfo, out string? existingJsonPointer))
        {
            // We're generating the schema of a recursive type, return a reference pointing to the outermost schema.
            return CompleteSchema(ref state, new JsonSchema { Ref = existingJsonPointer });
        }

        JsonSchema schema;
        JsonConverter effectiveConverter = customConverter ?? typeInfo.Converter;
        JsonNumberHandling effectiveNumberHandling = customNumberHandling ?? typeInfo.NumberHandling ?? typeInfo.Options.NumberHandling;

        if (!IsBuiltInConverter(effectiveConverter))
        {
            // Return a `true` schema for types with user-defined converters.
            return CompleteSchema(ref state, JsonSchema.True);
        }

        if (state.Configuration.ResolveDescriptionAttributes)
        {
            description ??= typeInfo.Type.GetCustomAttribute<DescriptionAttribute>()?.Description;
        }

        if (parentPolymorphicTypeInfo is null && typeInfo.PolymorphismOptions is { DerivedTypes.Count: > 0 } polyOptions)
        {
            // This is the base type of a polymorphic type hierarchy. The schema for this type
            // will include an "anyOf" property with the schemas for all derived types.

            string typeDiscriminatorKey = polyOptions.TypeDiscriminatorPropertyName;
            List<JsonDerivedType> derivedTypes = polyOptions.DerivedTypes.ToList();

            if (!typeInfo.Type.IsAbstract && !derivedTypes.Any(derived => derived.DerivedType == typeInfo.Type))
            {
                // For non-abstract base types that haven't been explicitly configured,
                // add a trivial schema to the derived types since we should support it.
                derivedTypes.Add(new JsonDerivedType(typeInfo.Type));
            }

            bool containsTypesWithoutDiscriminator = derivedTypes.Exists(static derivedTypes => derivedTypes.TypeDiscriminator is null);
            JsonSchemaType schemaType = JsonSchemaType.Any;
            List<JsonSchema>? anyOf = new(derivedTypes.Count);

            state.PushSchemaNode(JsonSchemaConstants.AnyOfPropertyName);

            foreach (JsonDerivedType derivedType in derivedTypes)
            {
                Debug.Assert(derivedType.TypeDiscriminator is null or int or string);

                KeyValuePair<string, JsonSchema>? derivedTypeDiscriminator = null;
                if (derivedType.TypeDiscriminator is { } discriminatorValue)
                {
                    JsonNode discriminatorNode = discriminatorValue switch
                    {
                        string stringId => (JsonNode)stringId,
                        _ => (JsonNode)(int)discriminatorValue,
                    };

                    JsonSchema discriminatorSchema = new() { Constant = discriminatorNode };
                    derivedTypeDiscriminator = new(typeDiscriminatorKey, discriminatorSchema);
                }

                JsonTypeInfo derivedTypeInfo = typeInfo.Options.GetTypeInfo(derivedType.DerivedType);

                state.PushSchemaNode(anyOf.Count.ToString(CultureInfo.InvariantCulture));
                JsonSchema derivedSchema = MapJsonSchemaCore(
                    ref state,
                    derivedTypeInfo,
                    parentPolymorphicTypeInfo: typeInfo,
                    typeDiscriminator: derivedTypeDiscriminator,
                    parentPolymorphicTypeContainsTypesWithoutDiscriminator: containsTypesWithoutDiscriminator,
                    parentPolymorphicTypeIsNonNullable: isNonNullableType,
                    cacheResult: false);

                state.PopSchemaNode();

                // Determine if all derived schemas have the same type.
                if (anyOf.Count == 0)
                {
                    schemaType = derivedSchema.Type;
                }
                else if (schemaType != derivedSchema.Type)
                {
                    schemaType = JsonSchemaType.Any;
                }

                anyOf.Add(derivedSchema);
            }

            state.PopSchemaNode();

            if (schemaType is not JsonSchemaType.Any)
            {
                // If all derived types have the same schema type, we can simplify the schema
                // by moving the type keyword to the base schema and removing it from the derived schemas.
                foreach (JsonSchema derivedSchema in anyOf)
                {
                    derivedSchema.Type = JsonSchemaType.Any;

                    if (derivedSchema.KeywordCount == 0)
                    {
                        // if removing the type results in an empty schema,
                        // remove the anyOf array entirely since it's always true.
                        anyOf = null;
                        break;
                    }
                }
            }

            schema = new()
            {
                Type = schemaType,
                AnyOf = anyOf,

                // If all derived types have a discriminator, we can require it in the base schema.
                Required = containsTypesWithoutDiscriminator ? null : new() { typeDiscriminatorKey },
            };

            return CompleteSchema(ref state, schema);
        }

        if (Nullable.GetUnderlyingType(typeInfo.Type) is Type nullableElementType)
        {
            JsonTypeInfo elementTypeInfo = typeInfo.Options.GetTypeInfo(nullableElementType);
            customConverter = ExtractCustomNullableConverter(customConverter);
            schema = MapJsonSchemaCore(ref state, elementTypeInfo, customConverter: customConverter, cacheResult: false);

            if (schema.Enum != null)
            {
                Debug.Assert(elementTypeInfo.Type.IsEnum, "The enum keyword should only be populated by schemas for enum types.");
                schema.Enum.Add(null); // Append null to the enum array.
            }

            return CompleteSchema(ref state, schema);
        }

        switch (typeInfo.Kind)
        {
            case JsonTypeInfoKind.Object:
                List<KeyValuePair<string, JsonSchema>>? properties = null;
                List<string>? required = null;
                JsonSchema? additionalProperties = null;

                if (typeInfo.UnmappedMemberHandling is JsonUnmappedMemberHandling.Disallow)
                {
                    // Disallow unspecified properties.
                    additionalProperties = JsonSchema.False;
                }

                if (typeDiscriminator is { } typeDiscriminatorPair)
                {
                    (properties ??= new()).Add(typeDiscriminatorPair);
                    if (parentPolymorphicTypeContainsTypesWithoutDiscriminator)
                    {
                        // Require the discriminator here since it's not common to all derived types.
                        (required ??= new()).Add(typeDiscriminatorPair.Key);
                    }
                }

                Func<JsonPropertyInfo, ParameterInfo?>? parameterInfoMapper = ResolveJsonConstructorParameterMapper(typeInfo);

                state.PushSchemaNode(JsonSchemaConstants.PropertiesPropertyName);
                foreach (JsonPropertyInfo property in typeInfo.Properties)
                {
                    if (property is { Get: null, Set: null } or { IsExtensionData: true })
                    {
                        continue; // Skip JsonIgnored properties and extension data
                    }

                    JsonNumberHandling? propertyNumberHandling = property.NumberHandling ?? effectiveNumberHandling;
                    JsonTypeInfo propertyTypeInfo = typeInfo.Options.GetTypeInfo(property.PropertyType);

                    // Resolve the attribute provider for the property.
                    ICustomAttributeProvider? attributeProvider = ResolveAttributeProvider(typeInfo.Type, property);

                    // Resolve property-level description attributes.
                    string? propertyDescription = state.Configuration.ResolveDescriptionAttributes
                        ? attributeProvider?.GetCustomAttributes(inherit: true).OfType<DescriptionAttribute>().FirstOrDefault()?.Description
                        : null;

                    // Declare the property as nullable if either getter or setter are nullable.
                    bool isNonNullableProperty = false;
                    if (attributeProvider is MemberInfo memberInfo)
                    {
                        NullabilityInfo nullabilityInfo = state.NullabilityInfoContext.GetMemberNullability(memberInfo);
                        isNonNullableProperty =
                            (property.Get is null || nullabilityInfo.ReadState is NullabilityState.NotNull) &&
                            (property.Set is null || nullabilityInfo.WriteState is NullabilityState.NotNull);
                    }

                    bool isRequired = property.IsRequired;
                    bool hasDefaultValue = false;
                    JsonNode? defaultValue = null;

                    ParameterInfo? associatedParameter = parameterInfoMapper?.Invoke(property);
                    if (associatedParameter != null)
                    {
                        ResolveParameterInfo(
                            associatedParameter,
                            propertyTypeInfo,
                            state.NullabilityInfoContext,
                            state.Configuration,
                            out hasDefaultValue,
                            out defaultValue,
                            out bool isNonNullableParameter,
                            ref propertyDescription,
                            ref isRequired);

                        isNonNullableProperty &= isNonNullableParameter;
                    }

                    state.PushSchemaNode(property.Name);
                    JsonSchema propertySchema = MapJsonSchemaCore(
                        ref state,
                        propertyTypeInfo,
                        parentType: typeInfo.Type,
                        propertyInfo: property,
                        parameterInfo: associatedParameter,
                        propertyAttributeProvider: attributeProvider,
                        isNonNullableType: isNonNullableProperty,
                        description: propertyDescription,
                        customConverter: property.CustomConverter,
                        customNumberHandling: propertyNumberHandling);

                    state.PopSchemaNode();

                    if (hasDefaultValue)
                    {
                        propertySchema.DefaultValue = defaultValue;
                        propertySchema.HasDefaultValue = true;
                    }

                    (properties ??= new()).Add(new(property.Name, propertySchema));

                    if (isRequired)
                    {
                        (required ??= new()).Add(property.Name);
                    }
                }

                state.PopSchemaNode();
                return CompleteSchema(ref state, new()
                {
                    Type = JsonSchemaType.Object,
                    Properties = properties,
                    Required = required,
                    AdditionalProperties = additionalProperties,
                });

            case JsonTypeInfoKind.Enumerable:
                Type elementType = GetElementType(typeInfo);
                JsonTypeInfo elementTypeInfo = typeInfo.Options.GetTypeInfo(elementType);

                if (typeDiscriminator is null)
                {
                    state.PushSchemaNode(JsonSchemaConstants.ItemsPropertyName);
                    JsonSchema items = MapJsonSchemaCore(ref state, elementTypeInfo, customNumberHandling: effectiveNumberHandling);
                    state.PopSchemaNode();

                    return CompleteSchema(ref state, new()
                    {
                        Type = JsonSchemaType.Array,
                        Items = items.IsTrue ? null : items,
                    });
                }
                else
                {
                    // Polymorphic enumerable types are represented using a wrapping object:
                    // { "$type" : "discriminator", "$values" : [element1, element2, ...] }
                    // Which corresponds to the schema
                    // { "properties" : { "$type" : { "const" : "discriminator" }, "$values" : { "type" : "array", "items" : { ... } } } }
                    const string ValuesKeyword = "$values";

                    state.PushSchemaNode(JsonSchemaConstants.PropertiesPropertyName);
                    state.PushSchemaNode(ValuesKeyword);
                    state.PushSchemaNode(JsonSchemaConstants.ItemsPropertyName);

                    JsonSchema items = MapJsonSchemaCore(ref state, elementTypeInfo, customNumberHandling: effectiveNumberHandling);

                    state.PopSchemaNode();
                    state.PopSchemaNode();
                    state.PopSchemaNode();

                    return CompleteSchema(ref state, new()
                    {
                        Type = JsonSchemaType.Object,
                        Properties = new()
                        {
                            typeDiscriminator.Value,
                            new(ValuesKeyword,
                                new JsonSchema()
                                {
                                    Type = JsonSchemaType.Array,
                                    Items = items.IsTrue ? null : items,
                                }),
                        },
                        Required = parentPolymorphicTypeContainsTypesWithoutDiscriminator ? new() { typeDiscriminator.Value.Key } : null,
                    });
                }

            case JsonTypeInfoKind.Dictionary:
                Type valueType = GetElementType(typeInfo);
                JsonTypeInfo valueTypeInfo = typeInfo.Options.GetTypeInfo(valueType);

                List<KeyValuePair<string, JsonSchema>>? dictProps = null;
                List<string>? dictRequired = null;

                if (typeDiscriminator is { } dictDiscriminator)
                {
                    dictProps = new() { dictDiscriminator };
                    if (parentPolymorphicTypeContainsTypesWithoutDiscriminator)
                    {
                        // Require the discriminator here since it's not common to all derived types.
                        dictRequired = new() { dictDiscriminator.Key };
                    }
                }

                state.PushSchemaNode(JsonSchemaConstants.AdditionalPropertiesPropertyName);
                JsonSchema valueSchema = MapJsonSchemaCore(ref state, valueTypeInfo, customNumberHandling: effectiveNumberHandling);
                state.PopSchemaNode();

                return CompleteSchema(ref state, new()
                {
                    Type = JsonSchemaType.Object,
                    Properties = dictProps,
                    Required = dictRequired,
                    AdditionalProperties = valueSchema.IsTrue ? null : valueSchema,
                });

            default:
                Debug.Assert(typeInfo.Kind is JsonTypeInfoKind.None);

                if (s_simpleTypeSchemaFactories.TryGetValue(typeInfo.Type, out Func<JsonNumberHandling, JsonSchema>? simpleTypeSchemaFactory))
                {
                    schema = simpleTypeSchemaFactory(effectiveNumberHandling);
                }
                else if (typeInfo.Type.IsEnum)
                {
                    schema = GetEnumConverterSchema(typeInfo, effectiveConverter, state.Configuration);
                }
                else
                {
                    schema = JsonSchema.True;
                }

                return CompleteSchema(ref state, schema);
        }

        JsonSchema CompleteSchema(ref GenerationState state, JsonSchema schema)
        {
            if (schema.Ref is null)
            {
                if (state.Configuration.IncludeSchemaVersion && state.CurrentDepth == 0)
                {
                    JsonSchema.EnsureMutable(ref schema);
                    schema.Schema = SchemaVersion;
                }

                if (description is not null)
                {
                    JsonSchema.EnsureMutable(ref schema);
                    schema.Description = description;
                }

                // A schema is marked as nullable if either
                // 1. We have a schema for a property where either the getter or setter are marked as nullable.
                // 2. We have a schema for a reference type, unless we're explicitly treating null-oblivious types as non-nullable.
                bool isNullableSchema = (propertyInfo != null || parameterInfo != null)
                    ? !isNonNullableType
                    : CanBeNull(typeInfo.Type) && !parentPolymorphicTypeIsNonNullable && !state.Configuration.TreatNullObliviousAsNonNullable;

                if (isNullableSchema)
                {
                    schema.MakeNullable();
                }

                if (cacheResult)
                {
                    state.PopGeneratedType();
                }
            }

            if (state.Configuration.TransformSchemaNode != null)
            {
                // Prime the schema for invocation by the JsonNode transformer.
                schema.GenerationContext = new(typeInfo, parentType, propertyInfo, parameterInfo, propertyAttributeProvider);
            }

            return schema;
        }
    }

    private readonly ref struct GenerationState
    {
        private readonly List<string> _currentPath;
        private readonly List<(JsonTypeInfo typeInfo, JsonPropertyInfo? propertyInfo, int depth)> _generationStack;
        private readonly int _maxDepth;

        public GenerationState(JsonSchemaMapperConfiguration configuration, JsonSerializerOptions options, NullabilityInfoContext? nullabilityInfoContext = null)
        {
            Configuration = configuration;
            NullabilityInfoContext = nullabilityInfoContext ?? new();
            _maxDepth = options.MaxDepth is 0 ? 64 : options.MaxDepth;
            _generationStack = new();
            _currentPath = new();
        }

        public JsonSchemaMapperConfiguration Configuration { get; }
        public NullabilityInfoContext NullabilityInfoContext { get; }
        public int CurrentDepth => _currentPath.Count;

        public void PushSchemaNode(string nodeId)
        {
            if (CurrentDepth == _maxDepth)
            {
                ThrowHelpers.ThrowInvalidOperationException_MaxDepthReached();
            }

            _currentPath.Add(nodeId);
        }

        public void PopSchemaNode()
        {
            _currentPath.RemoveAt(_currentPath.Count - 1);
        }

        /// <summary>
        /// Pushes the current type/property to the generation stack or returns a JSON pointer if the type is recursive.
        /// </summary>
        public bool TryPushType(JsonTypeInfo typeInfo, JsonPropertyInfo? propertyInfo, [NotNullWhen(true)] out string? existingJsonPointer)
        {
            foreach ((JsonTypeInfo otherTypeInfo, JsonPropertyInfo? otherPropertyInfo, int depth) in _generationStack)
            {
                if (typeInfo == otherTypeInfo && propertyInfo == otherPropertyInfo)
                {
                    existingJsonPointer = FormatJsonPointer(_currentPath, depth);
                    return true;
                }
            }

            _generationStack.Add((typeInfo, propertyInfo, CurrentDepth));
            existingJsonPointer = null;
            return false;
        }

        public void PopGeneratedType()
        {
            Debug.Assert(_generationStack.Count > 0);
            _generationStack.RemoveAt(_generationStack.Count - 1);
        }

        private static string FormatJsonPointer(List<string> currentPathList, int depth)
        {
            Debug.Assert(0 <= depth && depth < currentPathList.Count);

            if (depth == 0)
            {
                return "#";
            }

            StringBuilder sb = new();
            sb.Append('#');

            for (int i = 0; i < depth; i++)
            {
                string segment = currentPathList[i];
                if (segment.AsSpan().IndexOfAny('~', '/') != -1)
                {
                    segment = segment.Replace("~", "~0").Replace("/", "~1");
                }

                sb.Append('/');
                sb.Append(segment);
            }

            return sb.ToString();
        }
    }

    private static readonly Dictionary<Type, Func<JsonNumberHandling, JsonSchema>> s_simpleTypeSchemaFactories = new()
    {
        [typeof(object)] = _ => JsonSchema.True,
        [typeof(bool)] = _ => new JsonSchema { Type = JsonSchemaType.Boolean },
        [typeof(byte)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(ushort)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(uint)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(ulong)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(sbyte)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(short)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(int)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(long)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(float)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Number, numberHandling, isIeeeFloatingPoint: true),
        [typeof(double)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Number, numberHandling, isIeeeFloatingPoint: true),
        [typeof(decimal)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Number, numberHandling),
#if NET6_0_OR_GREATER
        [typeof(Half)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Number, numberHandling, isIeeeFloatingPoint: true),
#endif
#if NET7_0_OR_GREATER
        [typeof(UInt128)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
        [typeof(Int128)] = numberHandling => GetSchemaForNumericType(JsonSchemaType.Integer, numberHandling),
#endif
        [typeof(char)] = _ => new JsonSchema { Type = JsonSchemaType.String, MinLength = 1, MaxLength = 1 },
        [typeof(string)] = _ => new JsonSchema { Type = JsonSchemaType.String },
        [typeof(byte[])] = _ => new JsonSchema { Type = JsonSchemaType.String },
        [typeof(Memory<byte>)] = _ => new JsonSchema { Type = JsonSchemaType.String },
        [typeof(ReadOnlyMemory<byte>)] = _ => new JsonSchema { Type = JsonSchemaType.String },
        [typeof(DateTime)] = _ => new JsonSchema { Type = JsonSchemaType.String, Format = "date-time" },
        [typeof(DateTimeOffset)] = _ => new JsonSchema { Type = JsonSchemaType.String, Format = "date-time" },
        [typeof(TimeSpan)] = _ => new JsonSchema
        {
            Comment = "Represents a System.TimeSpan value.",
            Type = JsonSchemaType.String,
            Pattern = @"^-?(\d+\.)?\d{2}:\d{2}:\d{2}(\.\d{1,7})?$",
        },

#if NET6_0_OR_GREATER
        [typeof(DateOnly)] = _ => new JsonSchema { Type = JsonSchemaType.String, Format = "date" },
        [typeof(TimeOnly)] = _ => new JsonSchema { Type = JsonSchemaType.String, Format = "time" },
#endif
        [typeof(Guid)] = _ => new JsonSchema { Type = JsonSchemaType.String, Format = "uuid" },
        [typeof(Uri)] = _ => new JsonSchema { Type = JsonSchemaType.String, Format = "uri" },
        [typeof(Version)] = _ => new JsonSchema
        {
            Comment = "Represents a version string.",
            Type = JsonSchemaType.String,
            Pattern = @"^\d+(\.\d+){1,3}$",
        },

        [typeof(JsonDocument)] = _ => new JsonSchema { Type = JsonSchemaType.Any },
        [typeof(JsonElement)] = _ => new JsonSchema { Type = JsonSchemaType.Any },
        [typeof(JsonNode)] = _ => new JsonSchema { Type = JsonSchemaType.Any },
        [typeof(JsonValue)] = _ => new JsonSchema { Type = JsonSchemaType.Any },
        [typeof(JsonObject)] = _ => new JsonSchema { Type = JsonSchemaType.Object },
        [typeof(JsonArray)] = _ => new JsonSchema { Type = JsonSchemaType.Array },
    };

    // Adapted from https://github.com/dotnet/runtime/blob/d606c601510c1a1a28cb6ef3550f12db049c0776/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Converters/Value/JsonPrimitiveConverter.cs#L36-L69
    private static JsonSchema GetSchemaForNumericType(JsonSchemaType schemaType, JsonNumberHandling numberHandling, bool isIeeeFloatingPoint = false)
    {
        Debug.Assert(schemaType is JsonSchemaType.Integer or JsonSchemaType.Number);
        Debug.Assert(!isIeeeFloatingPoint || schemaType is JsonSchemaType.Number);

        string? pattern = null;

        if ((numberHandling & (JsonNumberHandling.AllowReadingFromString | JsonNumberHandling.WriteAsString)) != 0)
        {
            pattern = schemaType is JsonSchemaType.Integer
                ? @"^-?(?:0|[1-9]\d*)$"
                : isIeeeFloatingPoint
                    ? @"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$"
                    : @"^-?(?:0|[1-9]\d*)(?:\.\d+)?$";

            schemaType |= JsonSchemaType.String;
        }

        if (isIeeeFloatingPoint && (numberHandling & JsonNumberHandling.AllowNamedFloatingPointLiterals) != 0)
        {
            return new JsonSchema
            {
                AnyOf = new()
                {
                    new JsonSchema { Type = schemaType, Pattern = pattern },
                    new JsonSchema { Enum = new() { (JsonNode)"NaN", (JsonNode)"Infinity", (JsonNode)"-Infinity" } },
                },
            };
        }

        return new JsonSchema { Type = schemaType, Pattern = pattern };
    }

    // Uses reflection to determine the element type of an enumerable or dictionary type
    // Workaround for https://github.com/dotnet/runtime/issues/77306#issuecomment-2007887560
    private static Type GetElementType(JsonTypeInfo typeInfo)
    {
        Debug.Assert(typeInfo.Kind is JsonTypeInfoKind.Enumerable or JsonTypeInfoKind.Dictionary);
        s_elementTypeProperty ??= typeof(JsonTypeInfo).GetProperty("ElementType", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        return (Type)s_elementTypeProperty?.GetValue(typeInfo)!;
    }

    private static PropertyInfo? s_elementTypeProperty;

    // The source generator currently doesn't populate attribute providers for properties
    // cf. https://github.com/dotnet/runtime/issues/100095
    // Work around the issue by running a query for the relevant MemberInfo using the internal MemberName property
    // https://github.com/dotnet/runtime/blob/de774ff9ee1a2c06663ab35be34b755cd8d29731/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Metadata/JsonPropertyInfo.cs#L206
#if NETCOREAPP
    [EditorBrowsable(EditorBrowsableState.Never)]
    [UnconditionalSuppressMessage("Trimming", "IL2075:'this' argument does not satisfy 'DynamicallyAccessedMembersAttribute' in call to target method. The return value of the source method does not have matching annotations.",
        Justification = "We're reading the internal JsonPropertyInfo.MemberName which cannot have been trimmed away.")]
    [UnconditionalSuppressMessage("Trimming", "IL2070:'this' argument does not satisfy 'DynamicallyAccessedMembersAttribute' in call to target method. The parameter of method does not have matching annotations.",
        Justification = "We're reading the member which is already accessed by the source generator.")]
#endif
    private static ICustomAttributeProvider? ResolveAttributeProvider(Type? declaringType, JsonPropertyInfo? propertyInfo)
    {
        if (declaringType is null || propertyInfo is null)
        {
            return null;
        }

        if (propertyInfo.AttributeProvider is { } provider)
        {
            return provider;
        }

        s_memberNameProperty ??= typeof(JsonPropertyInfo).GetProperty("MemberName", BindingFlags.Instance | BindingFlags.NonPublic)!;
        var memberName = (string?)s_memberNameProperty.GetValue(propertyInfo);
        if (memberName is not null)
        {
            return declaringType.GetMember(memberName, MemberTypes.Property | MemberTypes.Field, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).FirstOrDefault();
        }

        return null;
    }

    private static PropertyInfo? s_memberNameProperty;

    // Uses reflection to determine any custom converters specified for the element of a nullable type.
#if NETCOREAPP
    [UnconditionalSuppressMessage("Trimming", "IL2026",
        Justification = "We're resolving private fields of the built-in Nullable converter which cannot have been trimmed away.")]
#endif
    private static JsonConverter? ExtractCustomNullableConverter(JsonConverter? converter)
    {
        Debug.Assert(converter is null || IsBuiltInConverter(converter));

        // There is unfortunately no way in which we can obtain the element converter from a nullable converter without resorting to private reflection
        // https://github.com/dotnet/runtime/blob/5fda47434cecc590095e9aef3c4e560b7b7ebb47/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Converters/Value/NullableConverter.cs#L15-L17
        Type? converterType = converter?.GetType();
        if (converterType?.Name == "NullableConverter`1")
        {
            FieldInfo elementConverterField = converterType.GetPrivateFieldWithPotentiallyTrimmedMetadata("_elementConverter");
            return (JsonConverter)elementConverterField!.GetValue(converter)!;
        }

        return null;
    }

    // Uses reflection to determine schema for enum types
    // Adapted from https://github.com/dotnet/runtime/blob/d606c601510c1a1a28cb6ef3550f12db049c0776/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Converters/Value/EnumConverter.cs#L498-L521
#if NETCOREAPP
    [UnconditionalSuppressMessage("Trimming", "IL2026",
        Justification = "We're resolving private fields of the built-in enum converter which cannot have been trimmed away.")]
#endif
    private static JsonSchema GetEnumConverterSchema(JsonTypeInfo typeInfo, JsonConverter converter, JsonSchemaMapperConfiguration configuration)
    {
        Debug.Assert(typeInfo.Type.IsEnum && IsBuiltInConverter(converter));

        if (converter is JsonConverterFactory factory)
        {
            converter = factory.CreateConverter(typeInfo.Type, typeInfo.Options)!;
        }

        Type converterType = converter.GetType();
        FieldInfo converterOptionsField = converterType.GetPrivateFieldWithPotentiallyTrimmedMetadata("_converterOptions");
        FieldInfo namingPolicyField = converterType.GetPrivateFieldWithPotentiallyTrimmedMetadata("_namingPolicy");

        const int EnumConverterOptionsAllowStrings = 1;
        var converterOptions = (int)converterOptionsField!.GetValue(converter)!;
        if ((converterOptions & EnumConverterOptionsAllowStrings) != 0)
        {
            // This explicitly ignores the integer component in converters configured as AllowNumbers | AllowStrings
            // which is the default for JsonStringEnumConverter. This sacrifices some precision in the schema for simplicity.

            if (typeInfo.Type.GetCustomAttribute<FlagsAttribute>() is not null)
            {
                // Do not report enum values in case of flags.
                return new() { Type = JsonSchemaType.String };
            }

            var namingPolicy = (JsonNamingPolicy?)namingPolicyField!.GetValue(converter)!;
            JsonArray enumValues = new();
            foreach (string name in Enum.GetNames(typeInfo.Type))
            {
                // This does not account for custom names specified via the new
                // JsonStringEnumMemberNameAttribute introduced in .NET 9.
                string effectiveName = namingPolicy?.ConvertName(name) ?? name;
                enumValues.Add((JsonNode)effectiveName);
            }

            JsonSchema schema = new() { Enum = enumValues };
            if (configuration.IncludeTypeInEnums)
            {
                schema.Type = JsonSchemaType.String;
            }

            return schema;
        }

        return new() { Type = JsonSchemaType.Integer };
    }

#if NETCOREAPP
    [RequiresUnreferencedCode("Resolves unreferenced member metadata.")]
#endif
    private static FieldInfo GetPrivateFieldWithPotentiallyTrimmedMetadata(this Type type, string fieldName)
    {
        FieldInfo? field = type.GetField(fieldName, BindingFlags.Instance | BindingFlags.NonPublic);
        if (field is null)
        {
            throw new InvalidOperationException(
                $"Could not resolve metadata for field '{fieldName}' in type '{type}'. " +
                "If running Native AOT ensure that the 'IlcTrimMetadata' property has been disabled.");
        }

        return field;
    }

    // Resolves the parameters of the deserialization constructor for a type, if they exist.
#if NETCOREAPP
    [UnconditionalSuppressMessage("Trimming", "IL2072:Target parameter argument does not satisfy 'DynamicallyAccessedMembersAttribute' in call to target method. The return value of the source method does not have matching annotations.",
        Justification = "The deserialization constructor should have already been referenced by the source generator and therefore will not have been trimmed.")]
#endif
    private static Func<JsonPropertyInfo, ParameterInfo?>? ResolveJsonConstructorParameterMapper(JsonTypeInfo typeInfo)
    {
        Debug.Assert(typeInfo.Kind is JsonTypeInfoKind.Object);

        if (typeInfo.Properties.Count > 0 &&
            typeInfo.CreateObject is null && // Ensure that a default constructor isn't being used
            typeInfo.Type.TryGetDeserializationConstructor(useDefaultCtorInAnnotatedStructs: true, out ConstructorInfo? ctor))
        {
            ParameterInfo[]? parameters = ctor?.GetParameters();
            if (parameters?.Length > 0)
            {
                Dictionary<ParameterLookupKey, ParameterInfo> dict = new(parameters.Length);
                foreach (ParameterInfo parameter in parameters)
                {
                    if (parameter.Name is not null)
                    {
                        // We don't care about null parameter names or conflicts since they
                        // would have already been rejected by JsonTypeInfo configuration.
                        dict[new(parameter.Name, parameter.ParameterType)] = parameter;
                    }
                }

                return prop => dict.TryGetValue(new(prop.Name, prop.PropertyType), out ParameterInfo? parameter) ? parameter : null;
            }
        }

        return null;
    }

    // Parameter to property matching semantics as declared in
    // https://github.com/dotnet/runtime/blob/12d96ccfaed98e23c345188ee08f8cfe211c03e7/src/libraries/System.Text.Json/src/System/Text/Json/Serialization/Metadata/JsonTypeInfo.cs#L1007-L1030
    private readonly struct ParameterLookupKey : IEquatable<ParameterLookupKey>
    {
        public ParameterLookupKey(string name, Type type)
        {
            Name = name;
            Type = type;
        }

        public string Name { get; }
        public Type Type { get; }

        public override int GetHashCode() => StringComparer.OrdinalIgnoreCase.GetHashCode(Name);
        public bool Equals(ParameterLookupKey other) => Type == other.Type && string.Equals(Name, other.Name, StringComparison.OrdinalIgnoreCase);
        public override bool Equals(object? obj) => obj is ParameterLookupKey key && Equals(key);
    }

    // Resolves the deserialization constructor for a type using logic copied from
    // https://github.com/dotnet/runtime/blob/e12e2fa6cbdd1f4b0c8ad1b1e2d960a480c21703/src/libraries/System.Text.Json/Common/ReflectionExtensions.cs#L227-L286
    private static bool TryGetDeserializationConstructor(
#if NETCOREAPP
        [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicConstructors | DynamicallyAccessedMemberTypes.NonPublicConstructors)]
#endif
        this Type type,
        bool useDefaultCtorInAnnotatedStructs,
        out ConstructorInfo? deserializationCtor)
    {
        ConstructorInfo? ctorWithAttribute = null;
        ConstructorInfo? publicParameterlessCtor = null;
        ConstructorInfo? lonePublicCtor = null;

        ConstructorInfo[] constructors = type.GetConstructors(BindingFlags.Public | BindingFlags.Instance);

        if (constructors.Length == 1)
        {
            lonePublicCtor = constructors[0];
        }

        foreach (ConstructorInfo constructor in constructors)
        {
            if (HasJsonConstructorAttribute(constructor))
            {
                if (ctorWithAttribute != null)
                {
                    deserializationCtor = null;
                    return false;
                }

                ctorWithAttribute = constructor;
            }
            else if (constructor.GetParameters().Length == 0)
            {
                publicParameterlessCtor = constructor;
            }
        }

        // Search for non-public ctors with [JsonConstructor].
        foreach (ConstructorInfo constructor in type.GetConstructors(BindingFlags.NonPublic | BindingFlags.Instance))
        {
            if (HasJsonConstructorAttribute(constructor))
            {
                if (ctorWithAttribute != null)
                {
                    deserializationCtor = null;
                    return false;
                }

                ctorWithAttribute = constructor;
            }
        }

        // Structs will use default constructor if attribute isn't used.
        if (useDefaultCtorInAnnotatedStructs && type.IsValueType && ctorWithAttribute == null)
        {
            deserializationCtor = null;
            return true;
        }

        deserializationCtor = ctorWithAttribute ?? publicParameterlessCtor ?? lonePublicCtor;
        return true;

        static bool HasJsonConstructorAttribute(ConstructorInfo constructorInfo) =>
            constructorInfo.GetCustomAttribute<JsonConstructorAttribute>() != null;
    }

    private static bool IsBuiltInConverter(JsonConverter converter) =>
        converter.GetType().Assembly == typeof(JsonConverter).Assembly;

    // Resolves the nullable reference type annotations for a property or field,
    // additionally addressing a few known bugs of the NullabilityInfo pre .NET 9.
    private static NullabilityInfo GetMemberNullability(this NullabilityInfoContext context, MemberInfo memberInfo)
    {
        Debug.Assert(memberInfo is PropertyInfo or FieldInfo);
        return memberInfo is PropertyInfo prop
            ? context.Create(prop)
            : context.Create((FieldInfo)memberInfo);
    }

    private static bool CanBeNull(Type type) => !type.IsValueType || Nullable.GetUnderlyingType(type) is not null;

    private static partial class ThrowHelpers
    {
        [DoesNotReturn]
        public static void ThrowInvalidOperationException_MaxDepthReached() =>
            throw new InvalidOperationException("The depth of the generated JSON schema exceeds the JsonSerializerOptions.MaxDepth setting.");
    }
}
#endif
