// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>
/// Interface for prompt template.
/// </summary>
public interface IPromptTemplate
{
    /// <summary>
    /// Render the template using the information in the context
    /// </summary>
    /// <param name="kernel">The Kernel.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Prompt rendered to string</returns>
    public Task<string> RenderAsync(Kernel kernel, IDictionary<string, string> arguments, CancellationToken cancellationToken = default);
}
