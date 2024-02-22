// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents result of classification of content that is classified by an AI model.
/// </summary>
public class ClassificationContent : KernelContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ClassificationContent"/> class.
    /// </summary>
    /// <param name="innerContent">The inner content representation</param>
    /// <param name="classifiedContent">Content which has been classified</param>
    /// <param name="result">The results of content classification by an AI model.</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Metadata associated with the content</param>
    public ClassificationContent(
        object? innerContent,
        string classifiedContent,
        IReadOnlyDictionary<string, object?> result,
        string? modelId = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.ClassifiedContent = classifiedContent;
        this.Result = result;
    }

    /// <summary>
    /// Represents the classified content.
    /// </summary>
    public string ClassifiedContent { get; }

    /// <summary>
    /// Represents the result of the classification of content that is classified by an AI model.
    /// </summary>
    public IReadOnlyDictionary<string, object?> Result { get; }
}
