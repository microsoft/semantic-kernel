// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.TemplateEngine.Blocks;

/// <summary>
/// Interface of dynamic blocks that need async IO to be rendered.
/// </summary>
internal interface ICodeRendering
{
    /// <summary>
    /// Render the block using the given context, potentially using external I/O.
    /// </summary>
    /// <param name="kernel">The kernel</param>
    /// <param name="arguments">The arguments</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Rendered content</returns>
    public Task<string> RenderCodeAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default);
}
