// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// $$$
/// </summary>
internal class AnnotationContent : KernelContent
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public string? FileId { get; internal init; }

    /// <summary>
    /// The citation.
    /// </summary>
    public string? Quote { get; internal init; }

    /// <summary>
    /// Start index of the citation.
    /// </summary>
    public int StartIndex { get; internal init; }

    /// <summary>
    /// End index of the citation.
    /// </summary>
    public int EndIndex { get; internal init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    public AnnotationContent()
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnnotationContent"/> class.
    /// </summary>
    public AnnotationContent(MessageTextAnnotation annotation)
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
