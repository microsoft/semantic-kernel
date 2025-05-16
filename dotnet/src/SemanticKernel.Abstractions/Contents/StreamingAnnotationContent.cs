// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Content type to support message annotations.
/// </summary>
[Experimental("SKEXP0110")]
public class StreamingAnnotationContent : StreamingKernelContent
{
    /// <summary>
    /// The referenced file identifier.
    /// </summary>
    /// <remarks>
    /// A file is referenced for certain tools, such as file search, and also when
    /// and image or document is produced as part of the agent response.
    /// </remarks>
    [JsonIgnore]
    [Obsolete("Use `ReferenceId` property instead.")]
    public string FileId
    {
        get => this.ReferenceId;
    }

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    [JsonIgnore]
    [Obsolete("Use `Label` property instead.")]
    public string? Quote => this.Label;

    /// <summary>
    /// Describes the annotation kind.
    /// </summary>
    /// <remarks>
    /// Provides context for using <see cref="ReferenceId"/>.
    /// </remarks>
    public AnnotationKind Kind { get; }

    /// <summary>
    /// The citation.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Label { get; init; }

    /// <summary>
    /// The referenced file identifier.
    /// </summary>
    /// <remarks>
    /// A file is referenced for certain tools, such as file search, and also when
    /// and image or document is produced as part of the agent response.
    /// </remarks>
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
    /// Initializes a new instance of the <see cref="StreamingAnnotationContent"/> class.
    /// </summary>
    /// <param name="kind">Describes the kind of annotation</param>
    /// <param name="referenceId">Identifies the referenced resource.</param>
    [JsonConstructor]
    public StreamingAnnotationContent(
        AnnotationKind kind,
        string referenceId)
    {
        Verify.NotNullOrWhiteSpace(referenceId, nameof(referenceId));

        this.Kind = kind;
        this.ReferenceId = referenceId;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        bool hasLabel = !string.IsNullOrEmpty(this.ReferenceId);

        return hasLabel ? $"{this.Label}: {this.ReferenceId}" : this.ReferenceId;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }
}
