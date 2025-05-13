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
    [Obsolete("Use `ReferenceId` property instead.  This method will be removed after June 1st 2025.")]
    public string? FileId
    {
        get => this.ReferenceId;
        init => this.ReferenceId = value;
    }

    /// <summary>
    /// The citation label in the associated response.
    /// </summary>
    [JsonIgnore]
    [Obsolete("Use `Label` property instead.")]
    public string Quote => this.Label;

    /// <summary>
    /// The referenced file identifier.
    /// </summary>
    /// <remarks>
    /// A file is referenced for certain tools, such as file search, and also when
    /// and image or document is produced as part of the agent response.
    /// </remarks>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ReferenceId { get; init; }

    /// <summary>
    /// The title of the annotation reference.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; init; }

    /// <summary>
    /// The citation.
    /// </summary>
    public string Label { get; init; } = string.Empty;

    /// <summary>
    /// Describes the annotation kind.
    /// </summary>
    /// <remarks>
    /// Provides context for using <see cref="ReferenceId"/>.
    /// </remarks>
    public AnnotationKind Kind { get; init; }

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
    [JsonConstructor]
    public StreamingAnnotationContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingAnnotationContent"/> class.
    /// </summary>
    /// <param name="label">The citation label.</param>
    /// <param name="kind">Describes the kind of annotation</param>
    /// <param name="referenceId">Identifies the referenced resource.</param>
    public StreamingAnnotationContent(
        string label,
        AnnotationKind kind,
        string referenceId)
    {
        this.Label = label;
        this.ReferenceId = referenceId;
        this.Kind = kind;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        bool hasFileId = !string.IsNullOrEmpty(this.ReferenceId);

        if (hasFileId)
        {
            return $"{this.Label}: {this.ReferenceId}";
        }

        return this.Label;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }
}
