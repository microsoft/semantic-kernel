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

    internal string Content { get; set; } = string.Empty;

    /// <summary>
    /// App logger
    /// </summary>
    protected ILogger Log { get; } = NullLogger.Instance;

    /// <summary>
    /// Base constructor
    /// </summary>
    /// <param name="log">App logger</param>
    protected Block(ILogger? log = null)
    {
        if (log != null) { this.Log = log; }
    }

    internal virtual Task<string> RenderCodeAsync(SKContext executionContext)
    {
        throw new NotImplementedException("This block doesn't support code execution");
    }

    internal abstract bool IsValid(out string error);

    internal abstract string Render(ContextVariables? variables);
}
