// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text.Json.Nodes;

namespace JsonSchemaMapper;

/// <summary>
/// Controls the behavior of the <see cref="JsonSchemaMapper"/> class.
/// </summary>
#if EXPOSE_JSON_SCHEMA_MAPPER
public
#else
internal
#endif
    class JsonSchemaMapperConfiguration
{
    /// <summary>
    /// Gets the default configuration object used by <see cref="JsonSchemaMapper"/>.
    /// </summary>
    public static JsonSchemaMapperConfiguration Default { get; } = new();

    /// <summary>
    /// Determines whether the '$schema' property should be included in the root schema document.
    /// </summary>
    /// <remarks>
    /// Defaults to true.
    /// </remarks>
    public bool IncludeSchemaVersion { get; init; } = true;

    /// <summary>
    /// Determines whether the <see cref="DescriptionAttribute"/> should be resolved for types and properties.
    /// </summary>
    /// <remarks>
    /// Defaults to true.
    /// </remarks>
    public bool ResolveDescriptionAttributes { get; init; } = true;

    /// <summary>
    /// Specifies whether the type keyword should be included in enum type schemas.
    /// </summary>
    /// <remarks>
    /// Defaults to false.
    /// </remarks>
    public bool IncludeTypeInEnums { get; init; }

    /// <summary>
    /// Determines whether non-nullable schemas should be generated for null oblivious reference types.
    /// </summary>
    /// <remarks>
    /// Defaults to <see langword="false"/>. Due to restrictions in the run-time representation of nullable reference types
    /// most occurrences are null oblivious and are treated as nullable by the serializer. A notable exception to that rule
    /// are nullability annotations of field, property and constructor parameters which are represented in the contract metadata.
    /// </remarks>
    public bool TreatNullObliviousAsNonNullable { get; init; }

    /// <summary>
    /// Defines a callback that is invoked for every schema that is generated within the type graph.
    /// </summary>
    public Func<JsonSchemaGenerationContext, JsonNode, JsonNode>? TransformSchemaNode { get; init; }
}
