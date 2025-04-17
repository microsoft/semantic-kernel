// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// The options for defining a template format and parser.
/// </summary>
public class TemplateOptions
{
    /// <summary>
    /// The format of the template.
    /// </summary>
    /// <remarks>
    /// The default is 'handlebars'.
    /// Used to identify which templating language is being used e.g., semantic-kernel, handlebars.
    /// </remarks>
    public string? Format
    {
        get => this._format;
        set
        {
            Verify.NotNull(value);
            this._format = value;
        }
    }

    /// <summary>
    /// The parser to use with the template.
    /// </summary>
    /// <remarks>
    /// The default is
    /// - 'semantic-kernel' for agent definitions loaded using the standard YAML format
    /// - 'prompty' for agent definitions loaded using the prompty format
    /// The parser is used to parse the rendered template into a form that can be consumed by the current API
    /// e.g., if we have api: chat then we expect the rendered template to represent a collection of chat messages.
    /// The rendered template can represent the collection of chat messages in different formats e.g. prompty or semantic-kernel or chatxml.
    /// In this example, since the prompty parser is used, the runtime will look for a prompty.chat parser to convert the block of text into the corresponding messages array.
    /// Essentially, the engine looks for the {{template.parser}}.{{model.api}} to find the appropriate parser.
    /// </remarks>
    public string? Parser
    {
        get => this._parser;
        set
        {
            Verify.NotNull(value);
            this._parser = value;
        }
    }

    /// <summary>
    /// Gets or sets a value indicating whether the template may emit structural text.
    /// </summary>
    /// <remarks>
    /// The default is true.
    /// When set to false the value of the template output is treated as safe content i.e. the template can emit structural text.
    /// </remarks>
    public bool Strict { get; set; } = true;

    #region private
    private string? _format;
    private string? _parser;
    #endregion
}
