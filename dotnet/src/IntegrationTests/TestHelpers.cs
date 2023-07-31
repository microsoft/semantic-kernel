// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.IntegrationTests;

internal static class TestHelpers
{
    internal static void ImportSampleSkills(IKernel target)
    {
        var chatSkill = GetSkills(target,
            "ChatPlugin",
            "SummarizePlugin",
            "WriterPlugin",
            "CalendarPlugin",
            "ChildrensBookPlugin",
            "ClassificationPlugin",
            "CodingPlugin",
            "FunPlugin",
            "IntentDetectionPlugin",
            "MiscPlugin",
            "QAPlugin");
    }

    internal static IDictionary<string, ISKFunction> GetSkills(IKernel target, params string[] skillNames)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }
        string skillParentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, "../../../../../../prompts/samples"));

        return target.ImportSemanticSkillFromDirectory(skillParentDirectory, skillNames);
    }
}
