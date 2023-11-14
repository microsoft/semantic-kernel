// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class FunctionViewExtensions
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="functionView"></param>
    /// <returns></returns>
    public static string GetQualifiedName(this FunctionView functionView)
    {
        return
            string.IsNullOrWhiteSpace(functionView.PluginName) ?
            functionView.Name :
            $"{functionView.PluginName}-{functionView.Name}";
    }
}
