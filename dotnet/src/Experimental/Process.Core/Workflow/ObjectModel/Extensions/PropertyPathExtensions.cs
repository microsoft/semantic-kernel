// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal static class PropertyPathExtensions
{
    public static string Format(this PropertyPath path) => $"{path.VariableScopeName}.{path.VariableName}";
}
