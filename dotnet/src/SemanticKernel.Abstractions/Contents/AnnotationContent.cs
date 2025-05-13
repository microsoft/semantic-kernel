// Copyright (c) Microsoft. All rights reserved.
using System;
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
    [Obsolete("Use `ReferenceId` property instead.")]
    public string? FileId
    {
        get => this.ReferenceId;
        init => this.ReferenceId = value ?? string.Empty;
    }

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    [JsonIgnore]
    [Obsolete("Use `Label` property instead.")]
    public string Quote => this.Label;

    /// <summary>
    /// Identifies the referenced resource according to its <see cref="Kind"/>.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string ReferenceId { get; init; } = string.Empty;

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    /// <remarks>
    /// This is the citation referebce that will be displayed in the response.
    /// </remarks>
    public string Label { get; init; } = string.Empty;

    /// <summary>
    /// Describes the annotation kind.
    /// </summary>
    /// <remarks>
    /// Provides context for using <see cref="ReferenceId"/>.
    /// </remarks>
    public AnnotationKind Kind { get; init; }

    /// <summary>
    /// The title of the annotation reference.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; init; }

    /// <summary>
    /// Start index of the citation.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? StartIndex { get; init; }

    /// <summary>
    /// End index of the citation.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
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
    /// <param name="kind">Describes the kind of annotation</param>
    /// <param name="referenceId">Identifies the referenced resource.</param>
    public AnnotationContent(
        string label,
        AnnotationKind kind,
        string referenceId)
    {
        this.Label = label;
        this.Kind = kind;
        this.ReferenceId = referenceId;
    }
}
