// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process.Workflow.Validation;

/// <summary>
/// Represents a validation failure that is associated with an exception.
/// </summary>
public class ExceptionValidationFailure : ValidationFailure
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ExceptionValidationFailure"/> class with the specified exception and message.
    /// </summary>
    /// <param name="exception">The exception that caused the validation failure.</param>
    /// <param name="message">The validation failure message.</param>
    internal ExceptionValidationFailure(Exception exception, string message)
        : base(message)
    {
        this.Exception = exception;
    }

    /// <summary>
    /// Gets the exception that caused the validation failure.
    /// </summary>
    public Exception Exception { get; }

    /// <inheritdoc/>
    public override string ToString() => $"{this.Message} - {this.Exception.Message} [{this.Exception.GetType().Name}]";
}
