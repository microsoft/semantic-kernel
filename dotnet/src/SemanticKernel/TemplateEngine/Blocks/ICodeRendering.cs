// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

/// <summary>
/// Interface of dynamic blocks that need async IO to be rendered.
/// </summary>
public interface ICodeRendering
{
    /// <summary>
    /// Render the block using the given context, potentially using external I/O.
    /// </summary>
    /// <param name="context">SK execution context</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Rendered content</returns>
    public Task<string> RenderCodeAsync(SKContext context, CancellationToken cancellationToken = default);
}
