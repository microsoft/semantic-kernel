// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

/// <summary>
/// Base class for blocks parsed from a prompt template
/// </summary>
public abstract class Block
{
    internal virtual BlockTypes Type => BlockTypes.Undefined;

    // internal virtual bool? SynchronousRendering => null;

    /// <summary>
    /// The block content
    /// </summary>
    internal string Content { get; }

    /// <summary>
    /// App logger
    /// </summary>
    protected ILogger Logger { get; } = NullLogger.Instance;

    /// <summary>
    /// Base constructor
    /// </summary>
    /// <param name="content">Block content</param>
    /// <param name="logger">App logger</param>
    protected Block(string? content, ILogger? logger = null)
    {
        if (logger != null) { this.Logger = logger; }

        this.Content = content ?? string.Empty;
    }

    /// <summary>
    /// Check if the block content is valid.
    /// </summary>
    /// <param name="errorMsg">Error message in case the content is not valid</param>
    /// <returns>True if the block content is valid</returns>
    public abstract bool IsValid(out string errorMsg);
}
