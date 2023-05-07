// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class KernelSemanticFunctionsExtensions
{
    /// <summary>
    /// Build and register a semantic function in the kernel skill collection, in a global generic skill.
    /// </summary>
    /// /// <param name="kernel">Kernel instance to extend</param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    public static ISKFunction ImportSemanticFunction(this IKernel kernel,
        string functionName,
        SemanticFunctionConfig functionConfig)
    {
        return ImportSemanticFunction(kernel, SkillCollection.GlobalSkill, functionName, functionConfig);
    }

    /// <summary>
    /// Build and register a semantic function in the kernel skill collection.
    /// </summary>
    /// <param name="kernel">Kernel instance to extend</param>
    /// <param name="skillName">Name of the skill containing the function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    public static ISKFunction ImportSemanticFunction(this IKernel kernel,
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig)
    {
        // Future-proofing the name not to contain special chars
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);

        ISKFunction function = CreateSemanticFunction(kernel, skillName, functionName, functionConfig);
        kernel.ImportFunction(skillName, function);

        return function;
    }

    private static ISKFunction CreateSemanticFunction(IKernel kernel,
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig)
    {
        if (!functionConfig.PromptTemplateConfig.Type.Equals("completion", StringComparison.OrdinalIgnoreCase))
        {
            throw new AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                $"Function type not supported: {functionConfig.PromptTemplateConfig}");
        }

        ISKFunction func = SKFunction.FromSemanticConfig(skillName, functionName, functionConfig, kernel.Log);

        // Connect the function to the current kernel skill collection, in case the function
        // is invoked manually without a context and without a way to find other functions.
        func.SetDefaultSkillCollection(kernel.Skills);

        func.SetAIConfiguration(CompleteRequestSettings.FromCompletionConfig(functionConfig.PromptTemplateConfig.Completion));

        // Note: the service is instantiated using the kernel configuration state when the function is invoked
        func.SetAIService(() => kernel.GetService<ITextCompletion>());

        return func;
    }
}
