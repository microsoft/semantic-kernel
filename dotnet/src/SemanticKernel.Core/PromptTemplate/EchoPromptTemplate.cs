// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Implementation of <see cref="IPromptTemplate"/> that just returns the prompt template.
/// </summary>
internal sealed class EchoPromptTemplate : IPromptTemplate
{
    private readonly PromptTemplateConfig _promptConfig;
    private readonly Task<string> _renderResult;

    /// <summary>
    /// Constructor for <see cref="EchoPromptTemplate"/>.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    internal EchoPromptTemplate(PromptTemplateConfig promptConfig)
    {
        Verify.NotNull(promptConfig, nameof(promptConfig));
        Verify.NotNull(promptConfig.Template, nameof(promptConfig.Template));

        this._promptConfig = promptConfig;
        this._renderResult = Task.FromResult(this._promptConfig.Template);
    }

    /// <inheritdoc/>
    public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default) => this._renderResult;
}
