// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
[Experimental("SKEXP0110")]
public static class AgentDefinitionExtensions
{
    private const string FunctionType = "function";
    private const string FunctionNameSeparator = ".";

    /// <summary>
    /// Creates default <see cref="KernelArguments"/> from the <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition to retrieve default arguments from.</param>
    /// <param name="kernel">Kernel instance.</param>
    public static KernelArguments GetDefaultKernelArguments(this AgentDefinition agentDefinition, Kernel kernel)
    {
        Verify.NotNull(agentDefinition);

        PromptExecutionSettings executionSettings = new()
        {
            ExtensionData = agentDefinition.Model?.Options ?? new Dictionary<string, object>()
        };

        // Enable automatic function calling if functions are defined.
        var functions = agentDefinition.GetToolDefinitions(FunctionType);
        if (functions is not null)
        {
            List<KernelFunction> kernelFunctions = [];
            foreach (var function in functions)
            {
                var nameParts = FunctionName.Parse(function.Id!, FunctionNameSeparator);

                // Look up the function in the kernel.
                if (kernel is not null && kernel.Plugins.TryGetFunction(nameParts.PluginName, nameParts.Name, out var kernelFunction))
                {
                    kernelFunctions.Add(kernelFunction);
                    continue;
                }
                throw new KernelException($"The specified function {function.Id} is not available in the kernel.");
            }

            executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(kernelFunctions);
        }

        var arguments = new KernelArguments(executionSettings);
        if (agentDefinition?.Inputs is not null)
        {
            // Add default arguments for the agent
            foreach (var keyValuePair in agentDefinition.Inputs)
            {
                if (keyValuePair.Value.Default is not null)
                {
                    arguments.Add(keyValuePair.Key, keyValuePair.Value.Default);
                }
            }
        }

        return arguments;
    }

    /// <summary>
    /// Creates a <see cref="IPromptTemplate"/> from the <see cref="AgentDefinition"/> if required.
    /// </summary>
    /// <param name="agentDefinition">Agent definition to retrieve default arguments from.</param>
    /// <param name="kernel">Kernel instance.</param>
    /// <param name="templateFactory">Optional prompt template factory</param>
    public static IPromptTemplate? GetPromptTemplate(this AgentDefinition agentDefinition, Kernel kernel, IPromptTemplateFactory? templateFactory)
    {
        Verify.NotNull(agentDefinition);

        if (templateFactory == null || agentDefinition.Template is null || agentDefinition.Instructions is null)
        {
            return null;
        }

        PromptTemplateConfig templateConfig = new(agentDefinition.Instructions)
        {
            TemplateFormat = agentDefinition.Template.Format,
        };

        return templateFactory.Create(templateConfig);
    }

    /// <summary>
    /// Get the first tool definition of the specified type.
    /// </summary>
    /// <param name="agentDefinition">Agent definition to retrieve the first tool from.</param>
    /// <param name="toolType">Tool type</param>
    public static AgentToolDefinition? GetFirstToolDefinition(this AgentDefinition agentDefinition, string toolType)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(toolType);
        return agentDefinition.Tools?.FirstOrDefault(tool => tool.Type == toolType);
    }

    /// <summary>
    /// Get all of the tool definitions of the specified type.
    /// </summary>
    /// <param name="agentDefinition">Agent definition to retrieve the tools from.</param>
    /// <param name="toolType">Tool type</param>
    public static IEnumerable<AgentToolDefinition>? GetToolDefinitions(this AgentDefinition agentDefinition, string toolType)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(toolType);
        return agentDefinition.Tools?.Where(tool => tool.Type == toolType);
    }

    /// <summary>
    /// Determines if the agent definition has a tool of the specified type.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    /// <param name="toolType">Tool type</param>
    public static bool HasToolType(this AgentDefinition agentDefinition, string toolType)
    {
        Verify.NotNull(agentDefinition);

        return agentDefinition.Tools?.Any(tool => tool?.Type?.Equals(toolType, System.StringComparison.Ordinal) ?? false) ?? false;
    }

    /// <summary>
    /// Processes the properties of the specified <see cref="AgentDefinition" />, including nested objects and collections.
    /// </summary>
    /// <param name="agentDefinition">Instance of <see cref="AgentDefinition"/> to normalize.</param>
    /// <param name="configuration">Instance of <see cref="IConfiguration"/> which provides the configuration values.</param>
    public static void Normalize(this AgentDefinition agentDefinition, IConfiguration configuration)
    {
        Verify.NotNull(agentDefinition);

        NormalizeObject(agentDefinition, configuration);
    }

    #region private
    private static void NormalizeObject(object? obj, IConfiguration configuration)
    {
        if (obj is null)
        {
            return;
        }

        if (obj is IList<object> objList)
        {
            for (int i = 0; i < objList.Count; i++)
            {
                if (objList[i] is string listValueString)
                {
                    if (RequiresNormalization(listValueString))
                    {
                        objList[i] = GetNormalizedValue(listValueString, configuration);
                    }
                }
                else
                {
                    NormalizeObject(objList[i], configuration);
                }
            }
        }
        else if (obj is IEnumerable enumerableValue)
        {
            foreach (var enumerableItem in enumerableValue)
            {
                NormalizeObject(enumerableItem, configuration);
            }
        }
        else
        {
            Type type = obj.GetType();
            foreach (PropertyInfo property in type.GetProperties())
            {
                if (!property.CanRead || !property.CanWrite)
                {
                    continue;
                }

                if (property.Name.Equals("Options", StringComparison.OrdinalIgnoreCase))
                {
                    Console.WriteLine("");
                }

                var value = property.GetValue(obj);
                if (value is null)
                {
                    continue;
                }

                if (value is string stringValue)
                {
                    if (RequiresNormalization(stringValue))
                    {
                        NormalizeString(obj, property, stringValue!, configuration);
                    }
                }
                else if (value is IDictionary<string, object> dictionaryValue)
                {
                    foreach (var entryKey in dictionaryValue.Keys)
                    {
                        var entryValue = dictionaryValue[entryKey];
                        if (entryValue is string entryStringValue)
                        {
                            if (RequiresNormalization(entryStringValue))
                            {
                                var normalizedValue = GetNormalizedValue(entryStringValue, configuration);
                                dictionaryValue[entryKey] = normalizedValue;
                            }
                        }
                        else
                        {
                            NormalizeObject(entryValue, configuration);
                        }
                    }
                }
                else if (value is IList<object> listValue)
                {
                    if (listValue is not null)
                    {
                        for (int i = 0; i < listValue.Count; i++)
                        {
                            if (listValue[i] is string listValueString)
                            {
                                if (RequiresNormalization(listValueString))
                                {
                                    listValue[i] = GetNormalizedValue(listValueString, configuration);
                                }
                            }
                            else
                            {
                                NormalizeObject(listValue[i], configuration);
                            }
                        }
                    }
                }
                else
                {
                    NormalizeObject(value, configuration);
                }
            }
        }
    }

    private static bool RequiresNormalization(string? value)
    {
        return !string.IsNullOrEmpty(value) && value.StartsWith("${", StringComparison.InvariantCulture) && value.EndsWith("}", StringComparison.InvariantCulture);
    }

    private static void NormalizeString(object instance, PropertyInfo property, string input, IConfiguration configuration)
    {
        property.SetValue(instance, GetNormalizedValue(input, configuration));
    }

    private static string GetNormalizedValue(string input, IConfiguration configuration)
    {
        string key = input.Substring(2, input.Length - 3);
        return configuration[key] ?? input;
    }
    #endregion
}
