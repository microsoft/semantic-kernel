// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
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
[ExcludeFromCodeCoverage]
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
    /// <returns>A new <see cref="JsonNode"/> instance defining the JSON schema for <paramref name="type"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    /// <exception cref="NotSupportedException">The <paramref name="options"/> parameter contains unsupported configuration.</exception>
    public static JsonNode GetJsonSchema(this JsonSerializerOptions options, Type type, JsonSchemaMapperConfiguration? configuration = null)
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
        configuration ??= JsonSchemaMapperConfiguration.Default;
        JsonTypeInfo typeInfo = options.GetTypeInfo(type);
        return MapRootTypeJsonSchema(typeInfo, configuration);
    }

    /// <summary>
    /// Generates a JSON object schema with properties corresponding to the specified method parameters.
    /// </summary>
    /// <param name="options">The options instance from which to resolve the contract metadata.</param>
    /// <param name="method">The method from whose parameters to generate the JSON schema.</param>
    /// <param name="configuration">The configuration object controlling the schema generation.</param>
    /// <returns>A new <see cref="JsonNode"/> instance defining the JSON schema for <paramref name="method"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    /// <exception cref="NotSupportedException">The <paramref name="options"/> parameter contains unsupported configuration.</exception>
    public static JsonNode GetJsonSchema(this JsonSerializerOptions options, MethodBase method, JsonSchemaMapperConfiguration? configuration = null)
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

        JsonObject schema = new();

        if (configuration.IncludeSchemaVersion)
        {
            schema.Add(JsonSchemaConstants.SchemaPropertyName, SchemaVersion);
        }

        schema.Add(JsonSchemaConstants.TitlePropertyName, method.Name);

        if (configuration.ResolveDescriptionAttributes &&
            method.GetCustomAttribute<DescriptionAttribute>() is DescriptionAttribute attr)
        {
            schema.Add(JsonSchemaConstants.DescriptionPropertyName, attr.Description);
        }

        schema.Add(JsonSchemaConstants.TypePropertyName, "object");

        NullabilityInfoContext nullabilityInfoContext = new();
        JsonObject? paramSchemas = null;
        JsonArray? requiredParams = null;

        foreach (ParameterInfo parameterInfo in method.GetParameters())
        {
            if (parameterInfo.Name is null)
            {
                ThrowHelpers.ThrowInvalidOperationException_TrimmedMethodParameters(method);
            }

            JsonTypeInfo parameterTypeInfo = options.GetTypeInfo(parameterInfo.ParameterType);
            JsonNode parameterSchema = MapMethodParameterJsonSchema(
                parameterInfo,
                parameterTypeInfo,
                configuration,
                nullabilityInfoContext,
                out bool isRequired);

            (paramSchemas ??= new()).Add(parameterInfo.Name, parameterSchema);
            if (isRequired)
            {
                (requiredParams ??= new()).Add((JsonNode)parameterInfo.Name);
            }
        }

        if (paramSchemas != null)
        {
            schema.Add(JsonSchemaConstants.PropertiesPropertyName, paramSchemas);
        }

        if (requiredParams != null)
        {
            schema.Add(JsonSchemaConstants.RequiredPropertyName, requiredParams);
        }

        return schema;
    }

    /// <summary>
    /// Generates a JSON schema corresponding to the specified contract metadata.
    /// </summary>
    /// <param name="typeInfo">The contract metadata for which to generate the schema.</param>
    /// <param name="configuration">The configuration object controlling the schema generation.</param>
    /// <returns>A new <see cref="JsonNode"/> instance defining the JSON schema for <paramref name="typeInfo"/>.</returns>
    /// <exception cref="ArgumentNullException">One of the specified parameters is <see langword="null" />.</exception>
    /// <exception cref="NotSupportedException">The <paramref name="typeInfo"/> parameter contains unsupported configuration.</exception>
    public static JsonNode GetJsonSchema(this JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration? configuration = null)
    {
        if (typeInfo is null)
        {
            ThrowHelpers.ThrowArgumentNullException(nameof(typeInfo));
        }

        ValidateOptions(typeInfo.Options);
        typeInfo.MakeReadOnly();
        configuration ??= JsonSchemaMapperConfiguration.Default;
        return MapRootTypeJsonSchema(typeInfo, configuration);
    }

    /// <summary>
    /// Renders the specified <see cref="JsonNode"/> instance as a JSON string.
    /// </summary>
    /// <param name="node">The node to serialize.</param>
    /// <param name="writeIndented">Whether to indent the resultant JSON text.</param>
    /// <returns>The JSON node rendered as a JSON string.</returns>
    public static string ToJsonString(this JsonNode? node, bool writeIndented = false)
    {
        return node is null ? "null" : node.ToJsonString(writeIndented ? s_writeIndentedOptions : null);
    }

    private static readonly JsonSerializerOptions s_writeIndentedOptions = new() { WriteIndented = true };

    private static partial JsonNode MapRootTypeJsonSchema(JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration configuration);

    private static partial JsonNode MapMethodParameterJsonSchema(
        ParameterInfo parameterInfo,
        JsonTypeInfo parameterTypeInfo,
        JsonSchemaMapperConfiguration configuration,
        NullabilityInfoContext nullabilityContext,
        out bool isRequired);

    private static void ValidateOptions(JsonSerializerOptions options)
    {
        if (options.ReferenceHandler == ReferenceHandler.Preserve)
        {
            ThrowHelpers.ThrowNotSupportedException_ReferenceHandlerPreserveNotSupported();
        }

        options.MakeReadOnly();
    }

    private static void ResolveParameterInfo(
        ParameterInfo parameter,
        JsonTypeInfo parameterTypeInfo,
        NullabilityInfoContext nullabilityInfoContext,
        JsonSchemaMapperConfiguration configuration,
        out bool hasDefaultValue,
        out JsonNode? defaultValue,
        out bool isNonNullable,
        ref string? description,
        ref bool isRequired)
    {
        Debug.Assert(parameterTypeInfo.Type == parameter.ParameterType);

        if (configuration.ResolveDescriptionAttributes)
        {
            // Resolve parameter-level description attributes.
            description ??= parameter.GetCustomAttribute<DescriptionAttribute>()?.Description;
        }

        // Incorporate the nullability information from the parameter.
        isNonNullable = nullabilityInfoContext.GetParameterNullability(parameter) is NullabilityState.NotNull;

        if (parameter.HasDefaultValue)
        {
            // Append the default value to the description.
            object? defaultVal = parameter.GetNormalizedDefaultValue();
            defaultValue = JsonSerializer.SerializeToNode(defaultVal, parameterTypeInfo);
            hasDefaultValue = true;
        }
        else
        {
            // Parameter is not optional, mark as required.
            isRequired = true;
            defaultValue = null;
            hasDefaultValue = false;
        }
    }

    private static NullabilityState GetParameterNullability(this NullabilityInfoContext context, ParameterInfo parameterInfo)
    {
#if !NET9_0_OR_GREATER
        // Workaround for https://github.com/dotnet/runtime/issues/92487
        if (GetGenericParameterDefinition(parameterInfo) is { ParameterType: { IsGenericParameter: true } typeParam })
        {
            // Step 1. Look for nullable annotations on the type parameter.
            if (GetNullableFlags(typeParam) is byte[] flags)
            {
                return TranslateByte(flags[0]);
            }

            // Step 2. Look for nullable annotations on the generic method declaration.
            if (typeParam.DeclaringMethod != null && GetNullableContextFlag(typeParam.DeclaringMethod) is byte flag)
            {
                return TranslateByte(flag);
            }

            // Step 3. Look for nullable annotations on the generic method declaration.
            if (GetNullableContextFlag(typeParam.DeclaringType!) is byte flag2)
            {
                return TranslateByte(flag2);
            }

            // Default to nullable.
            return NullabilityState.Nullable;

#if NETCOREAPP
            [UnconditionalSuppressMessage("Trimming", "IL2075:'this' argument does not satisfy 'DynamicallyAccessedMembersAttribute' in call to target method. The return value of the source method does not have matching annotations.",
                Justification = "We're resolving private fields of the built-in enum converter which cannot have been trimmed away.")]
#endif
            static byte[]? GetNullableFlags(MemberInfo member)
            {
                Attribute? attr = member.GetCustomAttributes().FirstOrDefault(attr =>
                {
                    Type attrType = attr.GetType();
                    return attrType.Namespace == "System.Runtime.CompilerServices" && attrType.Name == "NullableAttribute";
                });

                return (byte[])attr?.GetType().GetField("NullableFlags")?.GetValue(attr)!;
            }

#if NETCOREAPP
            [UnconditionalSuppressMessage("Trimming", "IL2075:'this' argument does not satisfy 'DynamicallyAccessedMembersAttribute' in call to target method. The return value of the source method does not have matching annotations.",
                Justification = "We're resolving private fields of the built-in enum converter which cannot have been trimmed away.")]
#endif
            static byte? GetNullableContextFlag(MemberInfo member)
            {
                Attribute? attr = member.GetCustomAttributes().FirstOrDefault(attr =>
                {
                    Type attrType = attr.GetType();
                    return attrType.Namespace == "System.Runtime.CompilerServices" && attrType.Name == "NullableContextAttribute";
                });

                return (byte?)attr?.GetType().GetField("Flag")?.GetValue(attr)!;
            }

            static NullabilityState TranslateByte(byte b)
            {
                return b switch
                {
                    1 => NullabilityState.NotNull,
                    2 => NullabilityState.Nullable,
                    _ => NullabilityState.Unknown
                };
            }
        }

        static ParameterInfo GetGenericParameterDefinition(ParameterInfo parameter)
        {
            if (parameter.Member is { DeclaringType.IsConstructedGenericType: true }
                                    or MethodInfo { IsGenericMethod: true, IsGenericMethodDefinition: false })
            {
                var genericMethod = (MethodBase)GetGenericMemberDefinition(parameter.Member);
                return genericMethod.GetParameters()[parameter.Position];
            }

            return parameter;
        }

#if NETCOREAPP
        [UnconditionalSuppressMessage("Trimming", "IL2075:'this' argument does not satisfy 'DynamicallyAccessedMembersAttribute' in call to target method. The return value of the source method does not have matching annotations.",
            Justification = "Looking up the generic member definition of the provided member.")]
#endif
        static MemberInfo GetGenericMemberDefinition(MemberInfo member)
        {
            if (member is Type type)
            {
                return type.IsConstructedGenericType ? type.GetGenericTypeDefinition() : type;
            }

            if (member.DeclaringType!.IsConstructedGenericType)
            {
                const BindingFlags AllMemberFlags =
                    BindingFlags.Static | BindingFlags.Instance |
                    BindingFlags.Public | BindingFlags.NonPublic;

                return member.DeclaringType.GetGenericTypeDefinition()
                    .GetMember(member.Name, AllMemberFlags)
                    .First(m => m.MetadataToken == member.MetadataToken);
            }

            if (member is MethodInfo { IsGenericMethod: true, IsGenericMethodDefinition: false } method)
            {
                return method.GetGenericMethodDefinition();
            }

            return member;
        }
#endif
        return context.Create(parameterInfo).WriteState;
    }

    // Taken from https://github.com/dotnet/runtime/blob/903bc019427ca07080530751151ea636168ad334/src/libraries/System.Text.Json/Common/ReflectionExtensions.cs#L288-L317
    private static object? GetNormalizedDefaultValue(this ParameterInfo parameterInfo)
    {
        Type parameterType = parameterInfo.ParameterType;
        object? defaultValue = parameterInfo.DefaultValue;

        if (defaultValue is null)
        {
            return null;
        }

        // DBNull.Value is sometimes used as the default value (returned by reflection) of nullable params in place of null.
        if (defaultValue == DBNull.Value && parameterType != typeof(DBNull))
        {
            return null;
        }

        // Default values of enums or nullable enums are represented using the underlying type and need to be cast explicitly
        // cf. https://github.com/dotnet/runtime/issues/68647
        if (parameterType.IsEnum)
        {
            return Enum.ToObject(parameterType, defaultValue);
        }

        if (Nullable.GetUnderlyingType(parameterType) is Type underlyingType && underlyingType.IsEnum)
        {
            return Enum.ToObject(underlyingType, defaultValue);
        }

        return defaultValue;
    }

    private static class JsonSchemaConstants
    {
        public const string SchemaPropertyName = "$schema";
        public const string RefPropertyName = "$ref";
        public const string CommentPropertyName = "$comment";
        public const string TitlePropertyName = "title";
        public const string DescriptionPropertyName = "description";
        public const string TypePropertyName = "type";
        public const string FormatPropertyName = "format";
        public const string PatternPropertyName = "pattern";
        public const string PropertiesPropertyName = "properties";
        public const string RequiredPropertyName = "required";
        public const string ItemsPropertyName = "items";
        public const string AdditionalPropertiesPropertyName = "additionalProperties";
        public const string EnumPropertyName = "enum";
        public const string NotPropertyName = "not";
        public const string AnyOfPropertyName = "anyOf";
        public const string ConstPropertyName = "const";
        public const string DefaultPropertyName = "default";
        public const string MinLengthPropertyName = "minLength";
        public const string MaxLengthPropertyName = "maxLength";
    }

    private static partial class ThrowHelpers
    {
        [DoesNotReturn]
        public static void ThrowArgumentNullException(string name) => throw new ArgumentNullException(name);

        [DoesNotReturn]
        public static void ThrowInvalidOperationException_TrimmedMethodParameters(MethodBase method) =>
            throw new InvalidOperationException($"The parameters for method '{method}' have been trimmed away.");

        [DoesNotReturn]
        public static void ThrowNotSupportedException_ReferenceHandlerPreserveNotSupported() =>
            throw new NotSupportedException("Schema generation not supported with ReferenceHandler.Preserve enabled.");
    }
}
