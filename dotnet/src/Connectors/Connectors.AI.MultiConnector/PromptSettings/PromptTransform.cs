// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a transformation of an input prompt string that can be template based or customized
/// </summary>
public class PromptTransform
{
    public PromptTransform()
    {
        this.Template = "{0}";
        this.TransformFunction = s => string.Format(CultureInfo.InvariantCulture, this.Template, s);
    }

    public string Template { get; set; }

    [JsonIgnore]
    public Func<string, string> TransformFunction { get; set; }

    public string Transform(string input)
    {
        return this.TransformFunction(input);
    }
}
