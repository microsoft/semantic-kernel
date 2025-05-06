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
    [JsonIgnore]
    [Obsolete("Use `ReferenceId` property instead.  This method will be removed after June 1st 2025.")]
    public string? FileId
    {
        get => this.ReferenceId;
        init => this.ReferenceId = value ?? string.Empty;
    }

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    [JsonIgnore]
    [Obsolete("Use `Label` property instead.  This method will be removed after June 1st 2025.")]
    public string Quote => this.Label;

    /// <summary>
    /// Identifies the referenced resource according to its <see cref="Kind"/>.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string ReferenceId { get; internal init; } = string.Empty;

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    /// <remarks>
    /// This is the citation referebce that will be displayed in the response.
    /// </remarks>
    public string Label { get; internal init; } = string.Empty;

    /// <summary>
    /// Describes the annotation kind.
    /// </summary>
    /// <remarks>
    /// Provides context for using <see cref="ReferenceId"/>.
    /// </remarks>
    public AnnotationKind Kind { get; internal init; }

    /// <summary>
    /// The title of the annotation reference.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; init; }

    /// <summary>
    /// Start index of the citation.
    /// </summary>
    public int? StartIndex { get; init; }

    /// <summary>
    /// End index of the citation.
    /// </summary>
    public int? EndIndex { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    [JsonConstructor]
    public AnnotationContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    /// <param name="label">The citation label.</param>
    /// <param name="referenceId">Identifies the referenced resource.</param>
    /// <param name="kind">Descibes the kind of annotation</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content</param>
    /// <param name="metadata">Additional metadata</param>
    public AnnotationContent(
        string label,
        string referenceId,
        AnnotationKind kind,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Label = label;
        this.Kind = kind;
        this.ReferenceId = referenceId;
    }
}
