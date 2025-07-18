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
        //init => this.ReferenceId = value ?? string.Empty;
    }

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    [JsonIgnore]
    [Obsolete("Use `Label` property instead.")]
    public string Quote => this.Label;

    /// <summary>
    /// Describes the annotation kind.
    /// </summary>
    /// <remarks>
    /// Provides context for using <see cref="ReferenceId"/>.
    /// </remarks>
    public AnnotationKind Kind { get; }

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    /// <remarks>
    /// This is the citation reference that will be displayed in the response.
    /// </remarks>
    public string Label { get; }

    /// <summary>
    /// Identifies the referenced resource according to its <see cref="Kind"/>.
    /// </summary>
    public string ReferenceId { get; }

    /// <summary>
    /// The title of the annotation reference (when <see cref="Kind"/> == <see cref="AnnotationKind.UrlCitation"/>..
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
    /// <param name="kind">Describes the kind of annotation</param>
    /// <param name="label">The citation label.</param>
    /// <param name="referenceId">Identifies the referenced resource.</param>
    [JsonConstructor]
    public AnnotationContent(
        AnnotationKind kind,
        string label,
        string referenceId)
    {
        Verify.NotNullOrWhiteSpace(label, nameof(label));
        Verify.NotNullOrWhiteSpace(referenceId, nameof(referenceId));

        this.Kind = kind;
        this.Label = label;
        this.ReferenceId = referenceId;
    }
}
