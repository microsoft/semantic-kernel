// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Default implementation of <see cref="IPromptTemplateFactory"/> for the semantic-kernel prompt template format.
/// </summary>
public sealed class KernelPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly ILoggerFactory _loggerFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public KernelPromptTemplateFactory(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <inheritdoc/>
    public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        if (promptTemplateConfig.TemplateFormat.Equals(PromptTemplateConfig.SemanticKernelTemplateFormat, System.StringComparison.Ordinal))
        {
            return new KernelPromptTemplate(templateString, promptTemplateConfig, this._loggerFactory);
        }

        throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
    }
}
