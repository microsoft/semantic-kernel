// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.PromptTemplate.Handlebars;

/// <summary>
/// Provides an <see cref="IPromptTemplateFactory"/> for the handlebars prompt template format.
/// </summary>
public class HandlebarsPromptTemplateFactory : IPromptTemplateFactory
{
    /// <summary>The name of the Handlebars template format.</summary>
    public const string HandlebarsTemplateFormat = "handlebars";

    /// <summary>Initializes the instance.</summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public HandlebarsPromptTemplateFactory(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
    }

    /// <inheritdoc/>
    public bool TryCreate(PromptTemplateConfig templateConfig, [NotNullWhen(true)] out IPromptTemplate? result)
    {
        Verify.NotNull(templateConfig);

        if (templateConfig.TemplateFormat.Equals(HandlebarsTemplateFormat, System.StringComparison.Ordinal))
        {
            result = new HandlebarsPromptTemplate(templateConfig, this._loggerFactory);
            return true;
        }

        result = null;
        return false;
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    #endregion
}
