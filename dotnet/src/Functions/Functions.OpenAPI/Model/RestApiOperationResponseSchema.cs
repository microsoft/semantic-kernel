// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Model;

/// <summary>
/// The REST API operation response schema
/// </summary>
public sealed class RestApiOperationResponseSchema
{
    /// <summary>
    /// The title of the schema.
    /// </summary>
    public string? Title { get; set; }

    /// <summary>
    /// The type of the schema (e.g., object, array, string, integer).
    /// </summary>
    public string? Type { get; set; }

    /// <summary>
    /// Properties of the schema, applicable if the schema is an object.
    /// </summary>
    public IDictionary<string, RestApiOperationResponseSchema> Properties { get; set; }

    /// <summary>
    /// Items schema, applicable if the schema is an array.
    /// </summary>
    public RestApiOperationResponseSchema? Items { get; set; }

    // You can add additional fields as necessary, such as Format, Enum, etc.

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationResponseSchema"/> class.
    /// </summary>
    public RestApiOperationResponseSchema(string? title = null, string? type = null, IDictionary<string, RestApiOperationResponseSchema>? properties = null, RestApiOperationResponseSchema? items = null)
    {
        this.Title = title;
        this.Type = type;
        this.Properties = properties ?? new Dictionary<string, RestApiOperationResponseSchema>();
        this.Items = items;
    }
}
