using System;
using System.ComponentModel;

namespace JsonSchemaMapper;

/// <summary>
/// Controls the behavior of the <see cref="JsonSchemaMapper"/> class.
/// </summary>
internal sealed class JsonSchemaMapperConfiguration
{
    /// <summary>
    /// Gets the default configuration object used by <see cref="JsonSchemaMapper"/>.
    /// </summary>
    public static JsonSchemaMapperConfiguration Default { get; } = new();

    private readonly int _maxDepth = 64;

    /// <summary>
    /// Determines whether schema references using JSON pointers should be generated for repeated complex types.
    /// </summary>
    /// <remarks>
    /// Defaults to <see langword="true"/>. Should be left enabled if recursive types (e.g. trees, linked lists) are expected.
    /// </remarks>
    public bool AllowSchemaReferences { get; init; } = true;

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
    /// Determines whether nullability should be included in the schema for reference types.
    /// </summary>
    /// <remarks>
    /// Defaults to false. Currently STJ doesn't recognize non-nullable reference types
    /// (https://github.com/dotnet/runtime/issues/1256) so the serializer will always treat
    /// them as nullable. Enabling this option improves accuracy of the generated schema
    /// with respect to the actual serialization behavior but can result in more noise.
    /// </remarks>
    public bool AllowNullForReferenceTypes { get; init; }

    /// <summary>
    /// Determines the maximum permitted depth when traversing the generated type graph.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when the value is less than 0.</exception>
    /// <remarks>
    /// Defaults to 64.
    /// </remarks>
    public int MaxDepth
    {
        get => this._maxDepth;
        init
        {
            if (value < 0)
            {
                Throw();
                static void Throw() => throw new ArgumentOutOfRangeException(nameof(value));
            }

            this._maxDepth = value;
        }
    }
}
