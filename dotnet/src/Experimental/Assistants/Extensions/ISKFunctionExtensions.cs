// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class ISKFunctionExtensions
{
    /// <summary>
    /// Produce a fully qualified toolname.
    /// </summary>
    public static string GetQualifiedName(this ISKFunction function)
    {
        return
            string.IsNullOrWhiteSpace(function.PluginName) ?
            function.Name :
            $"{function.PluginName}-{function.Name}";
    }
}
