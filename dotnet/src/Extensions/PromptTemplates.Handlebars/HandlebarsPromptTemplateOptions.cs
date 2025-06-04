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
    /// Delegate for registering custom Handlebars helpers with conflict resolution.
    /// </summary>
    /// <param name="name">The name of the helper.</param>
    /// <param name="helper">The helper to register.</param>
    public delegate void RegisterHelperCallback(string name, HandlebarsReturnHelper helper);

    /// <summary>
    /// Callback for registering custom helpers.
    /// </summary>
    /// <remarks>
    /// This callback allows users to register their custom helpers while ensuring
    /// that they don't conflict with existing system or custom helpers. Users should
    /// use the provided `registerHelper` callback when registering their custom helpers.
    /// </remarks>
    /// <example>
    /// <code>
    /// HandlebarsPromptTemplateOptions.RegisterCustomHelpers = (RegisterHelperCallback registerHelper, HandlebarsPromptTemplateOptions options, KernelArguments variables) =>
    /// {
    ///     registerHelper("customHelper", (Context context, Arguments arguments) =>
    ///     {
    ///         // Custom helper logic
    ///     });
    /// };
    /// </code>
    /// </example>
    /// <value>
    /// The callback takes three parameters:
    /// 1. A callback representing the `RegisterHelperSafe` method to register new helpers with built-in conflict handling.
    /// 2. A <see cref="HandlebarsPromptTemplateOptions"/> representing the configuration for helpers.
    /// 3. A <see cref="KernelArguments"/> instance containing variables maintained by the Handlebars context.
    /// </value>
    public Action<RegisterHelperCallback, HandlebarsPromptTemplateOptions, KernelArguments>? RegisterCustomHelpers { get; set; }

    /// <summary>
    /// Flag indicating whether to enable HTML decoding of the rendered template.
    /// </summary>
    public bool EnableHtmlDecoder { get; set; } = true;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPromptTemplateOptions"/> class.
    /// </summary>
    /// <remarks>Categories only filters built-in dotnet helpers, the ones defined here: https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki.</remarks>
    public HandlebarsPromptTemplateOptions()
    {
        this.PrefixSeparator = "-";
        this.Categories = [
            Category.Math, // Enables basic math operations (https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki/Math)
            Category.String // Enables string manipulation (https://github.com/Handlebars-Net/Handlebars.Net.Helpers/wiki/String)
        ];
    }
}
