// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace LoadPromptsFromCloud;

/// <summary>
/// The default method included in the Semantic Kernel SDK allows to load prompt templates from disk.
/// You can use `RegisterSemanticFunction` to implement a different prompt template provider.
/// For instance, this class shows what a provider loading prompts from the cloud would look like.
/// Note that the code is not complete, this is only a proof-of-concept.
/// </summary>
public static class SemanticKernelExtensions
{
    /// <summary>
    /// Sample function showing how to load skills from an external endpoint
    /// </summary>
    /// <param name="kernel">Kernel instance where the skill is loaded</param>
    /// <param name="skillName">Name of the skill. Only alphanumeric chars and underscore.</param>
    /// <param name="endpoint">Name of the skill. Only alphanumeric chars and underscore.</param>
    /// <returns>A skill containing a list of functions</returns>
    public static async Task<IDictionary<string, ISKFunction>> ImportSemanticSkillFromCloudAsync(
        this IKernel kernel, string skillName, string endpoint)
    {
        // Prepare a skill, ie a list of functions to be populated in the loop below
        var skill = new Dictionary<string, ISKFunction>();

        // This is where the code would make a request, e.g. to Azure Storage, to fetch a list of prompt definitions
        await Task.Delay(0);
        Dictionary<string, string> promptsInTheCloud = new(); // FetchListFrom(endpoint)
        promptsInTheCloud.Add("...", "...");

        // Loop through the definitions and create semantic functions
        foreach (var kv in promptsInTheCloud)
        {
            var functionName = kv.Key;
            var promptTemplate = kv.Value;

            // Load prompt configuration, you could download this too from the cloud
            var config = new PromptTemplateConfig
            {
                Services = new List<PromptTemplateConfig.ServiceConfig>
                {
                    new PromptTemplateConfig.ServiceConfig
                    {
                        ModelId = "text-davinci-003",
                        Settings = new JsonObject
                        {
                            { "temperature", 0.5 },
                            { "max_tokens", 100 },
                        }
                    }
                }
            };

            // Create template
            var template = new PromptTemplate(promptTemplate, config, kernel.PromptTemplateEngine);

            // Wrap AI logic into a function and store it
            var functionConfig = new SemanticFunctionConfig(config, template);
            skill[functionName] = kernel.RegisterSemanticFunction(skillName, functionName, functionConfig);
        }

        return skill;
    }
}
