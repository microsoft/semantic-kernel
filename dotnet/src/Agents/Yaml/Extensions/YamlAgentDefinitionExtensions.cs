// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
internal static class YamlAgentDefinitionExtensions
{
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
