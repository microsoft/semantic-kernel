// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent.Model;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
internal static class BedrockAgentDefinitionExtensions
{
    private const string CodeInterpreterType = "code_interpreter";
    private const string FileSearchType = "file_search";
    private const string FunctionType = "function";

    private static readonly string[] s_validToolTypes = new string[]
    {
        CodeInterpreterType,
        FileSearchType,
        FunctionType,
    };

    internal static async Task CreateToolsAsync(this AgentDefinition agentDefinition, BedrockAgent agent, CancellationToken cancellationToken)
    {
        if (agentDefinition.Tools is null || agentDefinition.Tools.Count == 0)
        {
            return;
        }

        var codeInterpreter = agentDefinition.GetFirstToolDefinition(CodeInterpreterType);
        if (codeInterpreter is not null)
        {
            await agent.CreateCodeInterpreterActionGroupAsync(cancellationToken).ConfigureAwait(false);
        }

        var functionSchema = agentDefinition.GetFunctionSchema();
        if (functionSchema is not null)
        {
            await agent.CreateKernelFunctionActionGroupAsync(functionSchema, cancellationToken).ConfigureAwait(false);
        }

        /*
        foreach (var tool in agentDefinition.Tools)
        {
            switch (tool.Type)
            {
                case CodeInterpreterType:
                    await agent.CreateCodeInterpreterActionGroupAsync(cancellationToken).ConfigureAwait(false);
                    break;
                case FunctionType:
                    await agent.CreateFunctionActionGroupAsync(cancellationToken).ConfigureAwait(false);
                    break;
                default:
                    throw new NotSupportedException($"Unable to create Bedrock tool because of unsupported tool type: {tool.Type}, supported tool types are: {string.Join(",", s_validToolTypes)}");
            }
        }
        */
    }

    internal static FunctionSchema? GetFunctionSchema(this AgentDefinition agentDefinition)
    {
        var functionTools = agentDefinition.GetToolDefinitions(FunctionType);
        if (functionTools is null)
        {
            return null;
        }

        List<Function> functions = [];
        foreach (var functionTool in functionTools)
        {
            functions.Add(new Function
            {
                Name = functionTool.Name,
                Description = functionTool.Description,
                Parameters = functionTool.CreateParameterSpec(),
                // This field controls whether user confirmation is required to invoke the function.
                // If this is set to "ENABLED", the user will be prompted to confirm the function invocation.
                // Only after the user confirms, the function call request will be issued by the agent.
                // If the user denies the confirmation, the agent will act as if the function does not exist.
                // Currently, we do not support this feature, so we set it to "DISABLED".
                RequireConfirmation = Amazon.BedrockAgent.RequireConfirmation.DISABLED,
            });
        }

        return new FunctionSchema
        {
            Functions = functions,
        };
    }

}
