// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using System.Web;
using HandlebarsDotNet;
using HandlebarsDotNet.Helpers;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars.Helpers;

namespace Microsoft.SemanticKernel.PromptTemplates.Handlebars;

/// <summary>
/// Represents a Handlebars prompt template.
/// </summary>
internal sealed class HandlebarsPromptTemplate : IPromptTemplate
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
    /// <param name="allowDangerouslySetContent">Flag indicating whether to allow potentially dangerous content to be inserted into the prompt</param>
    /// <param name="options">Handlebars prompt template options</param>
    internal HandlebarsPromptTemplate(PromptTemplateConfig promptConfig, bool allowDangerouslySetContent = false, HandlebarsPromptTemplateOptions? options = null)
    {
        this._allowDangerouslySetContent = allowDangerouslySetContent;
        this._loggerFactory ??= NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(typeof(HandlebarsPromptTemplate));
        this._promptModel = promptConfig;
        this._options = options ?? new();
    }

    /// <inheritdoc/>
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    public async Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
    {
        Verify.NotNull(kernel);

        arguments = this.GetVariables(arguments);
        var handlebarsInstance = HandlebarsDotNet.Handlebars.Create();

        // Register kernel, system, and any custom helpers
        this.RegisterHelpers(handlebarsInstance, kernel, arguments, cancellationToken);

        var template = handlebarsInstance.Compile(this._promptModel.Template);
        var text = template(arguments).Trim();
        return this._options.EnableHtmlDecoder ? System.Net.WebUtility.HtmlDecode(text) : text;
    }

    #region private

    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptModel;
    private readonly bool _allowDangerouslySetContent;

    /// <summary>
    /// Registers kernel, system, and any custom helpers.
    /// </summary>
    private void RegisterHelpers(
        IHandlebars handlebarsInstance,
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken = default)
    {
        // Add SK's built-in system helpers
        KernelSystemHelpers.Register(handlebarsInstance, kernel, arguments);

        // Add built-in helpers from the HandlebarsDotNet library
        HandlebarsHelpers.Register(handlebarsInstance, optionsCallback: options =>
        {
            options.PrefixSeparator = this._options.PrefixSeparator;
            options.Categories = this._options.Categories;
            options.UseCategoryPrefix = this._options.UseCategoryPrefix;
            options.CustomHelperPaths = this._options.CustomHelperPaths;
        });

        // Add helpers for kernel functions
        KernelFunctionHelpers.Register(handlebarsInstance, kernel, arguments, this._promptModel, this._allowDangerouslySetContent, this._options.PrefixSeparator, cancellationToken);

        // Add any custom helpers
        this._options.RegisterCustomHelpers?.Invoke(
            (string name, HandlebarsReturnHelper customHelper)
                => KernelHelpersUtils.RegisterHelperSafe(handlebarsInstance, name, customHelper),
            this._options,
            arguments);
    }

    /// <summary>
    /// Gets the variables for the prompt template, including setting any default values from the prompt config.
    /// </summary>
    private KernelArguments GetVariables(KernelArguments? arguments)
    {
        KernelArguments result = [];

        foreach (var p in this._promptModel.InputVariables)
        {
            if (p.Default is null || (p.Default is string stringDefault && stringDefault.Length == 0))
            {
                continue;
            }

            result[p.Name] = p.Default;
        }

        if (arguments is not null)
        {
            foreach (var kvp in arguments)
            {
                if (kvp.Value is not null)
                {
                    var value = kvp.Value;

                    if (this.ShouldEncodeTags(this._promptModel, kvp.Key, kvp.Value))
                    {
                        value = HttpUtility.HtmlEncode(value.ToString());
                    }

                    result[kvp.Key] = value;
                }
            }
        }

        return result;
    }

    private bool ShouldEncodeTags(PromptTemplateConfig promptTemplateConfig, string propertyName, object? propertyValue)
    {
        if (propertyValue is null || propertyValue is not string || this._allowDangerouslySetContent)
        {
            return false;
        }

        foreach (var inputVariable in promptTemplateConfig.InputVariables)
        {
            if (inputVariable.Name == propertyName)
            {
                return !inputVariable.AllowDangerouslySetContent;
            }
        }

        return true;
    }

    #endregion
}
