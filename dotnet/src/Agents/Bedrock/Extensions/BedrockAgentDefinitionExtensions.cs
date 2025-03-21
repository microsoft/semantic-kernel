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
    private const string KnowledgeBaseType = "knowledge_base";
    private const string FunctionType = "function";
    private const string KnowledgeBaseId = "knowledge_base_id";

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

        var knowledgeBases = agentDefinition.GetToolDefinitions(KnowledgeBaseType);
        if (knowledgeBases is not null)
        {
            foreach (var knowledgeBase in knowledgeBases)
            {
                if (knowledgeBase.Options?.TryGetValue(KnowledgeBaseId, out var value) ?? false && value is not null && value is string)
                {
                    var knowledgeBaseId = value as string;
                    var description = knowledgeBase.Description ?? string.Empty;
                    await agent.AssociateAgentKnowledgeBaseAsync(knowledgeBaseId!, description, cancellationToken).ConfigureAwait(false);
                }
            }
        }
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
                Name = functionTool.Id,
                Description = functionTool.Description,
                Parameters = functionTool.CreateParameterDetails(),
                // This field controls whether user confirmation is required to invoke the function.
                // If this is set to "ENABLED", the user will be prompted to confirm the function invocation.
                // Only after the user confirms, the function call request will be issued by the agent.
                // If the user denies the confirmation, the agent will act as if the function does not exist.
                // Currently, we do not support this feature, so we set it to "DISABLED".
                RequireConfirmation = Amazon.BedrockAgent.RequireConfirmation.DISABLED,
            });
        }

        return functions.Count == 0 ? null : new FunctionSchema { Functions = functions };
    }
}
