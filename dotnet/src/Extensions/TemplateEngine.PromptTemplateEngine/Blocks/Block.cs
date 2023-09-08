// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;

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
    private protected ILogger Logger { get; }

    /// <summary>
    /// Base constructor. Prevent external instantiation.
    /// </summary>
    /// <param name="content">Block content</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    private protected Block(string? content, ILoggerFactory? loggerFactory)
    {
        this.Content = content ?? string.Empty;
        this.Logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
    }

    /// <summary>
    /// Check if the block content is valid.
    /// </summary>
    /// <param name="errorMsg">Error message in case the content is not valid</param>
    /// <returns>True if the block content is valid</returns>
    public abstract bool IsValid(out string errorMsg);
}
