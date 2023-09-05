// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Extensions;

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Connectors.AI.OpenAI.FunctionCalling.Extensions;
using Orchestration;
using SkillDefinition;


/// <summary>
///  SKContext extensions for structured planning
/// </summary>
public static class SKContextExtensions
{
    /// <summary>
    ///  Get a skill collection from a list of function definitions
    /// </summary>
    /// <param name="context"></param>
    /// <param name="allowedSkills"></param>
    /// <returns></returns>
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

        return skillCollection;
    }


    /// <summary>
    ///  Get a skill collection from a StructuredPlannerConfig and a semantic query
    /// </summary>
    /// <param name="context"></param>
    /// <param name="structuredPlannerConfig"></param>
    /// <param name="semanticQuery"></param>
    /// <returns></returns>
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
