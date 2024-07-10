// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Optional options when calling <see cref="ITextSearch{T}.SearchAsync"/>.
/// </summary>
/// <remarks>
/// Implementors of <see cref="ITextSearch{T}"/> can extend this
/// if the service they are calling supports additional properties.
/// </remarks>
[Experimental("SKEXP0001")]
public class SearchOptions

{
    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel? Kernel { get; set; }

    /// <summary>
    /// The name of the search index.
    /// </summary>
    [JsonPropertyName("index")]
    public string? Index { get; set; }

    /// <summary>
    /// The filter expression to apply to the search query.
    /// </summary>
    [JsonPropertyName("filter")]
    public FormattableString? Filter { get; set; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    [JsonPropertyName("count")]
    public int Count { get; set; } = 1;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    [JsonPropertyName("offset")]
    public int Offset { get; set; } = 0;

    /// <summary>
    /// Extra properties that may be included in the serialized execution settings.
    /// </summary>
    /// <remarks>
    /// Avoid using this property if possible. Instead, use one of the classes that extends <see cref="SearchOptions"/>.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object>? ExtensionData { get; set; }
}
