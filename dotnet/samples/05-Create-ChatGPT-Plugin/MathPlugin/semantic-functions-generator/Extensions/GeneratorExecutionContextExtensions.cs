// Copyright (c) Microsoft. All rights reserved.

using Microsoft.CodeAnalysis;

namespace AIPlugins.AzureFunctions.Generator.Extensions;

internal static class GeneratorExecutionContextExtensions
{
    public static string? GetMSBuildProperty(
        this GeneratorExecutionContext context,
        string name,
        string defaultValue = "")
    {
        context.AnalyzerConfigOptions.GlobalOptions.TryGetValue($"build_property.{name}", out var value);
        return value ?? defaultValue;
    }

    public static string? GetRootNamespace(this GeneratorExecutionContext context)
    {
        return context.GetMSBuildProperty("RootNamespace");
    }
}
