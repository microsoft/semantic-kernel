// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Extensions;

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Orchestration;
using SkillDefinition;


public static class SKContextExtensions
{
    public static SkillCollection GetSkillCollection(this SKContext context, IEnumerable<FunctionDefinition> allowedSkills)
    {
        var skillCollection = new SkillCollection(context.LoggerFactory);
        IEnumerable<string> allowedSkillNames = allowedSkills.Select(skill => skill.Name);

        foreach (var name in allowedSkillNames)
        {
            var skillName = string.Empty;
            var functionName = string.Empty;

            if (name.Contains('_'))
            {
                var split = name.Split('_');
                skillName = split[0];
                functionName = split[1];
            }

            if (!string.IsNullOrEmpty(skillName))
            {
                if (context.Skills.TryGetFunction(skillName, functionName, out var function))
                {
                    skillCollection.AddFunction(function);
                }
            }
            else
            {
                if (context.Skills.TryGetFunction(name, out var function))
                {
                    skillCollection.AddFunction(function);
                }
            }
        }

        // foreach (var function
        //          in from skillName
        //                 in allowedSkillNames
        //             let functionView = context.Skills.GetFunctionsView()
        //             select functionView.SemanticFunctions[skillName].Concat(functionView.NativeFunctions[skillName])
        //             into matchedFunctions
        //             from function
        //                 in matchedFunctions.Select(func => context.Skills.GetFunction(func.SkillName, func.Name))
        //             select function)
        // {
        //     skillCollection.AddFunction(function);
        // }

        return skillCollection;
    }


    public static async Task<SkillCollection> GetSkillCollection(this SKContext context, StructuredPlannerConfig structuredPlannerConfig, string? semanticQuery = null)
    {
        IEnumerable<FunctionDefinition> functionDefinitions = new List<FunctionDefinition>();

        if (string.IsNullOrEmpty(semanticQuery))
        {
            functionDefinitions = context.Skills.GetFunctionDefinitions(excludedSkills: structuredPlannerConfig.ExcludedSkills, excludedFunctions: structuredPlannerConfig.ExcludedFunctions);
        }
        else
        {
            functionDefinitions = await context.GetFunctionDefinitions(semanticQuery, structuredPlannerConfig).ConfigureAwait(false);
        }

        return context.GetSkillCollection(functionDefinitions);
    }
}
