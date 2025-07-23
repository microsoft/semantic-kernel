// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// %%% COMMENT
/// </summary>
public class ValidationFailure
{
    internal ValidationFailure(string message)
    {
        this.Message = message;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public string Message { get; }

    /// <inheritdoc/>
    public override string ToString() => this.Message;
}
