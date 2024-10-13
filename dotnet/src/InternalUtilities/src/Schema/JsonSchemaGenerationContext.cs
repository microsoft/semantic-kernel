// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
// Source copied from https://github.com/eiriktsarpalis/stj-schema-mapper
// It should be kept in sync with any changes made in that repo,
// and should be removed once the relevant replacements are available in STJv9.

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json.Serialization.Metadata;

namespace JsonSchemaMapper;

/// <summary>
/// Defines the context in which a JSON schema within a type graph is being generated.
/// </summary>
#if EXPOSE_JSON_SCHEMA_MAPPER
public
#else
internal
#endif
    readonly struct JsonSchemaGenerationContext
{
    internal JsonSchemaGenerationContext(
        JsonTypeInfo typeInfo,
        Type? declaringType,
        JsonPropertyInfo? propertyInfo,
        ParameterInfo? parameterInfo,
        ICustomAttributeProvider? propertyAttributeProvider)
    {
        TypeInfo = typeInfo;
        DeclaringType = declaringType;
        PropertyInfo = propertyInfo;
        ParameterInfo = parameterInfo;
        PropertyAttributeProvider = propertyAttributeProvider;
    }

    /// <summary>
    /// The <see cref="JsonTypeInfo"/> for the type being processed.
    /// </summary>
    public JsonTypeInfo TypeInfo { get; }

    /// <summary>
    /// The declaring type of the property or parameter being processed.
    /// </summary>
    public Type? DeclaringType { get; }

    /// <summary>
    /// The <see cref="JsonPropertyInfo"/> if the schema is being generated for a property.
    /// </summary>
    public JsonPropertyInfo? PropertyInfo { get; }

    /// <summary>
    /// The <see cref="System.Reflection.ParameterInfo"/> if a constructor parameter
    /// has been associated with the accompanying <see cref="PropertyInfo"/>.
    /// </summary>
    public ParameterInfo? ParameterInfo { get; }

    /// <summary>
    /// The <see cref="ICustomAttributeProvider"/> corresponding to the property or field being processed.
    /// </summary>
    public ICustomAttributeProvider? PropertyAttributeProvider { get; }

    /// <summary>
    /// Checks if the type, property, or parameter has the specified attribute applied.
    /// </summary>
    /// <typeparam name="TAttribute">The type of the attribute to resolve.</typeparam>
    /// <param name="inherit">Whether to look up the hierarchy chain for the inherited custom attribute.</param>
    /// <returns>True if the attribute is defined by the current context.</returns>
    public bool IsDefined<TAttribute>(bool inherit = false)
        where TAttribute : Attribute =>
        GetCustomAttributes(typeof(TAttribute), inherit).Any();

    /// <summary>
    /// Checks if the type, property, or parameter has the specified attribute applied.
    /// </summary>
    /// <typeparam name="TAttribute">The type of the attribute to resolve.</typeparam>
    /// <param name="inherit">Whether to look up the hierarchy chain for the inherited custom attribute.</param>
    /// <returns>The first attribute resolved from the current context, or null.</returns>
    public TAttribute? GetAttribute<TAttribute>(bool inherit = false)
        where TAttribute : Attribute =>
        (TAttribute?)GetCustomAttributes(typeof(TAttribute), inherit).FirstOrDefault();

    /// <summary>
    /// Resolves any custom attributes that might have been applied to the type, property, or parameter.
    /// </summary>
    /// <param name="type">The attribute type to resolve.</param>
    /// <param name="inherit">Whether to look up the hierarchy chain for the inherited custom attribute.</param>
    /// <returns>An enumerable of all custom attributes defined by the context.</returns>
    public IEnumerable<Attribute> GetCustomAttributes(Type type, bool inherit = false)
    {
        // Resolves attributes starting from the property, then the parameter, and finally the type itself.
        return GetAttrs(PropertyAttributeProvider)
            .Concat(GetAttrs(ParameterInfo))
            .Concat(GetAttrs(TypeInfo.Type))
            .Cast<Attribute>();

        object[] GetAttrs(ICustomAttributeProvider? provider) =>
            provider?.GetCustomAttributes(type, inherit) ?? Array.Empty<object>();
    }
}
