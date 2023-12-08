// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.PromptTemplates.Handlebars;

/// <summary>
/// Provides an <see cref="IPromptTemplateFactory"/> for the handlebars prompt template format.
/// </summary>
public sealed class HandlebarsPromptTemplateFactory : IPromptTemplateFactory
{
    /// <summary>The name of the Handlebars template format.</summary>
    public const string HandlebarsTemplateFormat = "handlebars";

    /// <summary>
    /// Default options for built-in Handlebars helpers.
    /// </summary>
    /// TODO [@teresaqhoang]: Support override of default options
    private readonly HandlebarsPromptTemplateOptions _options;

    /// <summary>
    /// The character used to delimit plugin, function, or variable names in a Handlebars template.
    /// </summary>
    public string NameDelimiter => this._options.PrefixSeparator;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPromptTemplateFactory"/> class.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="options">Handlebars promnpt template options</param>
    public HandlebarsPromptTemplateFactory(ILoggerFactory? loggerFactory = null, HandlebarsPromptTemplateOptions? options = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._options = options ?? new();
    }

    /// <inheritdoc/>
    public bool TryCreate(PromptTemplateConfig templateConfig, [NotNullWhen(true)] out IPromptTemplate? result)
    {
        Verify.NotNull(templateConfig);

        if (templateConfig.TemplateFormat.Equals(HandlebarsTemplateFormat, System.StringComparison.Ordinal))
        {
            result = new HandlebarsPromptTemplate(templateConfig, this._loggerFactory, this._options);
            return true;
        }

        result = null;
        return false;
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    #endregion
}
