// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
using Extensions;
using SemanticFunctions;


/// <summary>
///  Configuration for a function call
/// </summary>
public class SKFunctionCallConfig
{
    /// <summary>
    /// Prompt template configuration.
    /// </summary>
    public PromptTemplateConfig PromptTemplateConfig { get; }

    /// <summary>
    /// Prompt template.
    /// </summary>
    public IPromptTemplate PromptTemplate { get; }

    /// <summary>
    ///  The function to call
    /// </summary>
    public FunctionDefinition TargetFunction { get; }

    /// <summary>
    ///  The functions that can be called by the LLM
    /// </summary>
    public List<FunctionDefinition> CallableFunctions { get; }

    /// <summary>
    ///  Whether to call functions automatically
    /// </summary>
    public bool CallFunctionsAutomatically { get; set; } = false;


    /// <summary>
    ///  Constructor
    /// </summary>
    /// <param name="template"></param>
    /// <param name="config"></param>
    /// <param name="targetFunction"></param>
    /// <param name="callableFunctions"></param>
    /// <param name="callFunctionsAutomatically"></param>
    public SKFunctionCallConfig(
        IPromptTemplate template,
        PromptTemplateConfig config,
        FunctionDefinition? targetFunction = null,
        IEnumerable<FunctionDefinition>? callableFunctions = null,
        bool callFunctionsAutomatically = false)
    {
        PromptTemplateConfig = config;
        PromptTemplate = template;
        TargetFunction = targetFunction ?? FunctionExtensions.Default;
        CallFunctionsAutomatically = callFunctionsAutomatically;
        CallableFunctions = callableFunctions?.ToList() ?? new List<FunctionDefinition>();
    }
}
