// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Content type to support message annotations.
/// </summary>
[Experimental("SKEXP0110")]
public class AnnotationContent : KernelContent
{
    /// <summary>
    /// The referenced file identifier.
    /// </summary>
    /// <remarks>
    /// A file is referenced for certain tools, such as file search, and also when
    /// and image or document is produced as part of the agent response.
    /// </remarks>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? FileId { get; init; }

    /// <summary>
    /// The title of the annotation reference.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; init; }

    /// <summary>
    /// The referenced url.
    /// </summary>
    /// <remarks>
    /// A url may be referenced for certain tools, such as bing grounding.
    /// </remarks>    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Uri? Url { get; init; }

    /// <summary>
    /// The citation.
    /// </summary>
    public string Quote { get; init; } = string.Empty;

    /// <summary>
    /// Start index of the citation.
    /// </summary>
    public int StartIndex { get; init; }

    /// <summary>
    /// End index of the citation.
    /// </summary>
    public int EndIndex { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    [JsonConstructor]
    public AnnotationContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    /// <param name="quote">The source text being referenced.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public AnnotationContent(
        string quote,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Quote = quote;
    }
}
