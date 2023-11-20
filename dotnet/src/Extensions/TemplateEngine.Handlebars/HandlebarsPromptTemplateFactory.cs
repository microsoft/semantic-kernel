// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.TemplateEngine.Handlebars;

/// <summary>
/// Implementation of <see cref="IPromptTemplateFactory"/> for the handlebars prompt template format.
/// </summary>
public class HandlebarsPromptTemplateFactory : IPromptTemplateFactory
{
    /// <summary>
    /// Handlebars template format.
    /// </summary>
    public const string HandlebarsTemplateFormat = "handlebars";

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public HandlebarsPromptTemplateFactory(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <inheritdoc/>
    public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        if (promptTemplateConfig.TemplateFormat.Equals(HandlebarsTemplateFormat, System.StringComparison.Ordinal))
        {
            return new HandlebarsPromptTemplate(templateString, promptTemplateConfig, this._loggerFactory);
        }

        throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    #endregion

}
