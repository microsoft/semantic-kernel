// Copyright (c) Microsoft. All rights reserved.

internal static class FunctionUtils
{
    internal static void SplitPluginFunctionName(string pluginFunctionName, out string pluginName, out string functionName)
    {
        var pluginFunctionNameParts = pluginFunctionName.Split('.');
        pluginName = pluginFunctionNameParts?.Length > 1 ? pluginFunctionNameParts[0] : string.Empty;
        functionName = pluginFunctionNameParts?.Length > 1 ? pluginFunctionNameParts[1] : pluginFunctionName;
    }
}
