// Copyright (c) Microsoft. All rights reserved.

using System;
using HandlebarsDotNet;
using HandlebarsDotNet.Helpers.Enums;
using HandlebarsDotNet.Helpers.Options;

namespace Microsoft.SemanticKernel.PromptTemplate.Handlebars;

/// <summary>
/// Configuration for Handlebars helpers.
/// </summary>
public sealed class HandlebarsPromptTemplateOptions : HandlebarsHelpersOptions
{
    // TODO [@teresaqhoang]: Issue #3947 Add Categories filter for KernelSystemHelpers (i.e., KernelHelperCategories)

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
        this.PrefixSeparator = "-";
        this.Categories = new Category[] {
            Category.Math, // Enables basic math operations (https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki/Math)
            Category.String // Enables string manipulation (https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki/String)
        };
    }
}
