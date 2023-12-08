// Copyright (c) Microsoft. All rights reserved.

using System;
using HandlebarsDotNet;
using HandlebarsDotNet.Helpers.Enums;
using HandlebarsDotNet.Helpers.Options;

namespace Microsoft.SemanticKernel.PromptTemplates.Handlebars;

/// <summary>
/// Configuration for Handlebars helpers.
/// </summary>
public sealed class HandlebarsPromptTemplateOptions : HandlebarsHelpersOptions
{
    // TODO [@teresaqhoang]: Issue #3947 Add Categories filter for KernelSystemHelpers (i.e., KernelHelperCategories)

    /// <summary>
    /// Default character to use for delimiting plugin name and function name in a Handlebars template.
    /// </summary>
    public string DefaultNameDelimiter { get; set; } = "-";

    /// <summary>
    /// Callback for registering custom helpers.
    /// </summary>
    public Action<IHandlebars, KernelArguments>? RegisterCustomHelpers { get; set; }

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
