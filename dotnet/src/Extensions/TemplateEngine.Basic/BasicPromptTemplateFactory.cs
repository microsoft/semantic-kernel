// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.TemplateEngine.Basic;

/// <summary>
/// TODO Mark
/// </summary>
public sealed class BasicPromptTemplateFactory : IPromptTemplateFactory
{
    private readonly IPromptTemplateFactory? _promptTemplateFactory;
    private readonly ILoggerFactory _loggerFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="BasicPromptTemplateFactory"/> class.
    /// </summary>
    public BasicPromptTemplateFactory() : this(null, null)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BasicPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BasicPromptTemplateFactory(ILoggerFactory? loggerFactory = null) : this(null, loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BasicPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="promptTemplateFactory">Next <see cref="IPromptTemplateFactory"/> in the chain to call.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BasicPromptTemplateFactory(IPromptTemplateFactory? promptTemplateFactory = null, ILoggerFactory? loggerFactory = null)
    {
        this._promptTemplateFactory = promptTemplateFactory;
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <inheritdoc/>
    public IPromptTemplate CreatePromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        if (promptTemplateConfig.TemplateFormat.Equals(PromptTemplateConfig.SEMANTICKERNEL, System.StringComparison.Ordinal))
        {
            return new BasicPromptTemplate(templateString, promptTemplateConfig, this._loggerFactory);
        }
        else if (this._promptTemplateFactory != null)
        {
            return this._promptTemplateFactory.CreatePromptTemplate(templateString, promptTemplateConfig);
        }

        throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
    }
}
