// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel;

namespace SemanticKernel.IntegrationTests;

internal static class TestHelpers
{
    internal static void ImportSamplePlugins(IKernel target)
    {
        var chatSkill = GetPlugins(target,
            "ChatSkill",
            "SummarizeSkill",
            "WriterSkill",
            "CalendarSkill",
            "ChildrensBookSkill",
            "ClassificationSkill",
            "CodingSkill",
            "FunSkill",
            "IntentDetectionSkill",
            "MiscSkill",
            "QASkill");
    }

    internal static IDictionary<string, ISKFunction> GetPlugins(IKernel target, params string[] pluginNames)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string parentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, "../../../../../../samples/skills"));

        return target.ImportSemanticFunctionsFromDirectory(parentDirectory, pluginNames);
    }
}
