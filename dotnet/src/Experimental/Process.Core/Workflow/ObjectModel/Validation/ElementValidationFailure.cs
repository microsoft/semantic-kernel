// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// Represents a validation failure that is associated with a specific <see cref="BotElement"/>.
/// </summary>
public class ElementValidationFailure : ValidationFailure
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ElementValidationFailure"/> class with the specified element and error message.
    /// </summary>
    /// <param name="element">The <see cref="BotElement"/> that caused the validation failure.</param>
    /// <param name="message">The validation error message.</param>
    internal ElementValidationFailure(BotElement element, string message)
        : base(message)
    {
        this.Kind = element.Kind;
        this.StartPosition = element.Syntax?.Position;
        this.EndPosition = element.Syntax?.EndPosition;
    }

    /// <summary>
    /// Gets the kind of the <see cref="BotElement"/> that caused the validation failure.
    /// </summary>
    public BotElementKind Kind { get; }

    /// <summary>
    /// Gets the start position of the <see cref="BotElement"/> in the source, if available.
    /// </summary>
    public int? StartPosition { get; }

    /// <summary>
    /// Gets the end position of the <see cref="BotElement"/> in the source, if available.
    /// </summary>
    public int? EndPosition { get; }
}
