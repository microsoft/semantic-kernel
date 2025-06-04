// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Provides extension methods for <see cref="AgentToolDefinition"/>.
/// </summary>
internal static class BedrockAgentToolDefinitionExtensions
{
    internal static Dictionary<string, Amazon.BedrockAgent.Model.ParameterDetail> CreateParameterDetails(
        this AgentToolDefinition agentToolDefinition)
    {
        Dictionary<string, Amazon.BedrockAgent.Model.ParameterDetail> parameterSpec = [];
        var parameters = agentToolDefinition.GetOption<List<object>?>("parameters");
        if (parameters is not null)
        {
            foreach (var parameter in parameters)
            {
                if (parameter is not Dictionary<object, object> parameterDict)
                {
                    throw new ArgumentException($"Invalid parameter type for function {agentToolDefinition.Id}");
                }

                var name = parameterDict.GetRequiredValue("name");
                var type = parameterDict.GetRequiredValue("type");
                var description = parameterDict.GetRequiredValue("description");
                var isRequired = parameterDict.GetRequiredValue("required").Equals("true", StringComparison.OrdinalIgnoreCase);

                parameterSpec.Add(name, new Amazon.BedrockAgent.Model.ParameterDetail
                {
                    Description = description,
                    Required = isRequired,
                    Type = new Amazon.BedrockAgent.Type(type),
                });
            }
        }

        return parameterSpec;
    }

    #region private
    private static string GetRequiredValue(this Dictionary<object, object> parameter, string key)
    {
        return parameter.TryGetValue(key, out var requiredValue) && requiredValue is string requiredString
            ? requiredString
            : throw new ArgumentException($"The option key '{key}' is required for a Bedrock function parameter.");
    }
    #endregion
}
