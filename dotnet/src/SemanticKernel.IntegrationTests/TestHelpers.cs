// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.IntegrationTests;

internal static class TestHelpers
{
    internal static void ImportSampleSkills(IKernel target)
    {
        var chatSkill = GetSkill("ChatSkill", target);
        var summarizeSkill = GetSkill("SummarizeSkill", target);
        var writerSkill = GetSkill("WriterSkill", target);
        var calendarSkill = GetSkill("CalendarSkill", target);
        var childrensBookSkill = GetSkill("ChildrensBookSkill", target);
        var classificationSkill = GetSkill("ClassificationSkill", target);
        var codingSkill = GetSkill("CodingSkill", target);
        var funSkill = GetSkill("FunSkill", target);
        var intentDetectionSkill = GetSkill("IntentDetectionSkill", target);
        var miscSkill = GetSkill("MiscSkill", target);
        var qaSkill = GetSkill("QASkill", target);
    }

    internal static IDictionary<string, ISKFunction> GetSkill(string skillName, IKernel target)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string skillParentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, "../../../../../../samples/skills"));

        IDictionary<string, ISKFunction> skill = target.ImportSemanticSkillFromDirectory(skillParentDirectory, skillName);
        return skill;
    }
}
