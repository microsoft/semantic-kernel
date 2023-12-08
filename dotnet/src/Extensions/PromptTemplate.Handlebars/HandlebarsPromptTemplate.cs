// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars.Helpers;

namespace Microsoft.SemanticKernel.PromptTemplates.Handlebars;

/// <summary>
/// Represents a Handlebars prompt template.
/// </summary>
internal class HandlebarsPromptTemplate : IPromptTemplate
{
    /// <summary>
    /// Default options for built-in Handlebars helpers.
    /// </summary>
    /// TODO [@teresaqhoang]: Support override of default options
    private readonly HandlebarsPromptTemplateOptions _options;

    /// <summary>
    /// Constructor for Handlebars PromptTemplate.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <param name="options">Handlebars promnpt template options</param>
    public HandlebarsPromptTemplate(PromptTemplateConfig promptConfig, ILoggerFactory? loggerFactory = null, HandlebarsPromptTemplateOptions? options = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(typeof(HandlebarsPromptTemplate));
        this._promptModel = promptConfig;
        this._options = options ?? new();
    }

    /// <inheritdoc/>
    public async Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        arguments = this.GetVariables(arguments);
        var handlebarsInstance = HandlebarsDotNet.Handlebars.Create();

        // Add helpers for kernel functions
        KernelFunctionHelpers.Register(handlebarsInstance, kernel, arguments, this._options.PrefixSeparator, cancellationToken);

        // Add built-in system helpers
        KernelSystemHelpers.Register(handlebarsInstance, arguments, this._options);

        // Register any custom helpers
        this._options.RegisterCustomHelpers?.Invoke(handlebarsInstance, arguments);

        var template = handlebarsInstance.Compile(this._promptModel.Template);
        var prompt = template(arguments);

        return await Task.FromResult(prompt).ConfigureAwait(false);
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;

    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptModel;

    private KernelArguments GetVariables(KernelArguments? arguments)
    {
        KernelArguments result = new();

        foreach (var p in this._promptModel.InputVariables)
        {
            if (!string.IsNullOrEmpty(p.Default))
            {
                result[p.Name] = p.Default;
            }
        }

        if (arguments is not null)
        {
            foreach (var kvp in arguments)
            {
                if (kvp.Value is not null)
                {
                    result[kvp.Key] = kvp.Value;
                }
            }
        }

        return result;
    }
    #endregion
}
