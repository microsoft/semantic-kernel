// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal static class DataValueExtensions
{
    public static string? GetParentId(this BotElement element) => element.Parent?.GetId();

    public static string GetId(this BotElement element)
    {
        return element switch
        {
            DialogAction action => action.Id.Value,
            ConditionItem conditionItem => conditionItem.Id ?? throw new InvalidActionException($"Undefined identifier for {nameof(ConditionItem)} that is member of {conditionItem.GetParentId() ?? "(root)"}."),
            OnActivity activity => activity.Id.Value,
            _ => throw new InvalidActionException($"Unknown element type: {element.GetType().Name}"),
        };
    }
}
