// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

/// <summary>
/// Base class for blocks parsed from a prompt template
/// </summary>
public abstract class Block
{
    internal virtual BlockTypes Type => BlockTypes.Undefined;

    internal virtual bool? SynchronousRendering => null;

    /// <summary>
    /// The block content
    /// </summary>
    internal string Content { get; }

    /// <summary>
    /// App logger
    /// </summary>
    protected ILogger Log { get; } = NullLogger.Instance;

    /// <summary>
    /// Base constructor
    /// </summary>
    /// <param name="content">Block content</param>
    /// <param name="log">App logger</param>
    protected Block(string? content, ILogger? log = null)
    {
        if (log != null) { this.Log = log; }

        this.Content = content ?? string.Empty;
    }

    internal virtual Task<string> RenderCodeAsync(SKContext executionContext)
    {
        throw new NotImplementedException("This block doesn't support async code execution, use Render(ContextVariables) instead.");
    }

    internal virtual string Render(ContextVariables? variables)
    {
        throw new NotImplementedException("This block requires async code execution, use RenderCodeAsync(SKContext) instead.");
    }

    internal abstract bool IsValid(out string error);
}
