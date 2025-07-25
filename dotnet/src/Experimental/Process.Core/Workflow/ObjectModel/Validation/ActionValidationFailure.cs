// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// Represents a validation failure based on a <see cref="DialogAction"/>.
/// </summary>
public class ActionValidationFailure : ElementValidationFailure
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ActionValidationFailure"/> class with the specified action and error message.
    /// </summary>
    /// <param name="action">The <see cref="DialogAction"/> that caused the validation failure.</param>
    /// <param name="message">The validation error message.</param>
    internal ActionValidationFailure(DialogAction action, string message)
        : base(action, message)
    {
        this.Id = action.Id.Value;
    }

    /// <summary>
    /// Gets the identifier of the <see cref="DialogAction"/> that caused the validation failure.
    /// </summary>
    public string Id { get; }
}
