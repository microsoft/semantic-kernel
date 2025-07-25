// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// Represents a failure that occurred during validation.
/// </summary>
public class ValidationFailure
{
    internal ValidationFailure(string message)
    {
        this.Message = message;
    }

    /// <summary>
    /// Gets the message that describes the validation failure.
    /// </summary>
    public string Message { get; }

    /// <inheritdoc/>
    public override string ToString() => this.Message;
}
