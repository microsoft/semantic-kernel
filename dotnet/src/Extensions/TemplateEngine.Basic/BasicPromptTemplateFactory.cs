// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.TemplateEngine.Basic;

/// <summary>
/// TODO Mark
/// </summary>
public sealed class BasicPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly ILoggerFactory _loggerFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="BasicPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BasicPromptTemplateFactory(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <inheritdoc/>
    public IPromptTemplate CreatePromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        if (promptTemplateConfig.TemplateFormat.Equals(PromptTemplateConfig.SEMANTICKERNEL, System.StringComparison.Ordinal))
        {
            return new BasicPromptTemplate(templateString, promptTemplateConfig, this._loggerFactory);
        }

        return null;
    }
}
