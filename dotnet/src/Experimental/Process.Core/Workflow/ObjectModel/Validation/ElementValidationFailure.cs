// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

/// <summary>
/// %%% COMMENT
/// </summary>
public class ElementValidationFailure : ValidationFailure
{
    internal ElementValidationFailure(BotElement element, string message)
        : base(message)
    {
        this.Kind = element.Kind;
        this.StartPosition = element.Syntax?.Position;
        this.EndPosition = element.Syntax?.EndPosition;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public BotElementKind Kind { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public int? StartPosition { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public int? EndPosition { get; }
}
