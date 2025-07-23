// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// %%% COMMENT
/// </summary>
public class ExceptionValidationFailure : ValidationFailure
{
    internal ExceptionValidationFailure(Exception exception, string message)
        : base(message)
    {
        this.Exception = exception;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public Exception Exception { get; }

    /// <inheritdoc/>
    public override string ToString() => $"{this.Message} - {this.Exception.Message} [{this.Exception.GetType().Name}]";
}
