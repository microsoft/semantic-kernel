// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// %%% COMMENT
/// </summary>
public class ActionValidationFailure : ElementValidationFailure
{
    internal ActionValidationFailure(DialogAction action, string message)
        : base(action, message)
    {
        this.Id = action.Id.Value;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public string Id { get; }
}
