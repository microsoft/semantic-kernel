// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Content type to support message annotations.
/// </summary>
public class AnnotationContent : KernelContent
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public string? FileId { get; }

    /// <summary>
    /// The citation.
    /// </summary>
    public string? Quote { get; }

    /// <summary>
    /// Start index of the citation.
    /// </summary>
    public int StartIndex { get; }

    /// <summary>
    /// End index of the citation.
    /// </summary>
    public int EndIndex { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    public AnnotationContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    /// <param name="annotation">The base annotion model.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content,</param>
    /// <param name="metadata">Additional metadata</param>
    public AnnotationContent(
        MessageTextAnnotation annotation,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Quote = annotation.Text;
        this.StartIndex = annotation.StartIndex;
        this.EndIndex = annotation.EndIndex;

        if (annotation is MessageTextFileCitationAnnotation citationAnnotation)
        {
            this.FileId = citationAnnotation.FileId;
        }
        else if (annotation is MessageTextFilePathAnnotation pathAnnotation)
        {
            this.FileId = pathAnnotation.FileId;
        }
    }
}
