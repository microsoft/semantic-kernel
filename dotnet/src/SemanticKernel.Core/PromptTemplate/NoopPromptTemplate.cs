// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// No operation implementation of <see cref="IPromptTemplate"/> that just returns the prompt template.
/// </summary>
internal sealed class NoopPromptTemplate : IPromptTemplate
{
    private readonly PromptTemplateConfig _promptConfig;

    /// <summary>
    /// Constructor for NoopPromptTemplate.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    internal NoopPromptTemplate(PromptTemplateConfig promptConfig)
    {
        Verify.NotNull(promptConfig, nameof(promptConfig));
        Verify.NotNull(promptConfig.Template, nameof(promptConfig.Template));

        this._promptConfig = promptConfig;
    }

    /// <inheritdoc/>
    public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._promptConfig.Template);
    }
}
