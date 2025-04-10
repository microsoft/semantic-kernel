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
    /// Used to identify which templating language is being used e.g., semantic-kernel, handlebars, ...
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
    /// Used to identify which parser is used with the template e.g., semantic-kernel, prompty, ...
    /// This will be combined with the API type to determine the correct parser to use.
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

    #region
    private string? _format;
    private string? _parser;
    #endregion
}
