// Copyright (c) Microsoft. All rights reserved.

using HandlebarsDotNet;
using HandlebarsDotNet.Helpers.Enums;
using HandlebarsDotNet.Helpers.Options;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.PromptTemplate.Handlebars.Helpers;
#pragma warning restore IDE0130

/// <summary>
/// Configuration for Handlebars helpers.
/// </summary>
public sealed class HandlebarsPromptTemplateOptions : HandlebarsHelpersOptions
{
    // TODO [@teresaqhoang]: Add Categories filter for KernelSystemHelpers (i.e., KernelHelperCategories)

    /// <summary>
    /// Default character to use for delimiting plugin name and function name in a Handlebars template.
    /// </summary>
    public string DefaultNameDelimiter { get; set; } = "-";

    /// <summary>
    /// Delegate for registering custom helpers.
    /// </summary>
    /// <param name="handlebarsInstance">The Handlebars instance.</param>
    /// <param name="executionContext">Arguments maintained in the template execution context.</param>
    public delegate void RegisterCustomHelpersCallback(IHandlebars handlebarsInstance, KernelArguments executionContext);

    /// <summary>
    /// Callback for registering custom helpers.
    /// </summary>
    public RegisterCustomHelpersCallback? RegisterCustomHelpers { get; set; } = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPromptTemplateOptions"/> class.
    /// </summary>
    /// <remarks>Categories only filters built-in dotnet helpers, the ones defined here: https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki.</remarks>
    public HandlebarsPromptTemplateOptions()
    {
        this.PrefixSeparator = this.DefaultNameDelimiter;
        this.Categories = new Category[] {
            Category.Math, // Enables basic math operations (https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki/Math)
            Category.String // Enables string manipulation (https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki/String)
        };
    }
}
