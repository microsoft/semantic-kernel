// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a text completion provider instance with the corresponding given name.
/// </summary>
public class NamedTextCompletion
{
    /// <summary>
    /// Gets or sets the name of the text completion provider.
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// text completion provider instance, to be used for prompt answering and testing.
    /// </summary>
    public ITextCompletion TextCompletion { get; set; }

    /// <summary>
    /// Cost per completion request.
    /// </summary>
    public decimal CostPerRequest { get; set; }

    /// <summary>
    /// Cost per completion request token.
    /// </summary>
    public decimal CostPerToken { get; set; }

    public decimal? CostPerRequestToken { get; set; }

    public Func<string, int>? TokenCountFunc { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="NamedTextCompletion"/> class.
    /// </summary>
    /// <param name="name">The name of the text completion provider.</param>
    /// <param name="textCompletion">The text completion provider.</param>
    public NamedTextCompletion(string name, ITextCompletion textCompletion)
    {
        this.Name = name;
        this.TextCompletion = textCompletion;
    }

    public decimal GetCost(string text, string result)
    {
        return this.CostPerRequest + (this.CostPerRequestToken ?? 0) * (this.TokenCountFunc ?? (s => 0))(text + result);
    }
}
