// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Base class for all AI results
/// </summary>
public abstract class CompleteContent
{
    /// <summary>
    /// Raw content object reference. (Breaking glass).
    /// </summary>
    public object InnerContent { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public Dictionary<string, object> Metadata { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CompleteContent"/> class.
    /// </summary>
    /// <param name="rawContent">Raw content object reference</param>
    /// <param name="metadata">Metadata associated with the content</param>
    protected CompleteContent(object rawContent, Dictionary<string, object>? metadata = null)
    {
        this.InnerContent = rawContent;
        this.Metadata = metadata ?? new();
    }

    /// <summary>
    /// Get the raw content from the result.
    /// </summary>
    /// <typeparam name="T">Expected type</typeparam>
    /// <returns></returns>
    public virtual T GetContentAs<T>() => (T)this.InnerContent;
}
