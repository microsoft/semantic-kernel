// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>
/// Interface for prompt template.
/// </summary>
public interface IPromptTemplate
{
    /// <summary>
    /// The list of parameters required by the template, using configuration and template info.
    /// </summary>
    IReadOnlyList<KernelParameterMetadata> Parameters { get; }

    /// <summary>
    /// Render the template using the information in the context
    /// </summary>
    /// <param name="kernel">The Kernel.</param>
    /// <param name="variables">The variables.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Prompt rendered to string</returns>
    public Task<string> RenderAsync(Kernel kernel, ContextVariables variables, CancellationToken cancellationToken = default);
}
