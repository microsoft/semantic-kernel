// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;
using YamlDotNet.Core;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Functions.Yaml;

/// <summary>
/// Deserializer for <see cref="PromptExecutionSettings"/>.
/// </summary>
internal class PromptExecutionSettingsNodeDeserializer : INodeDeserializer
{
    /// <inheritdoc/>
    public bool Deserialize(IParser reader, Type expectedType, Func<IParser, Type, object?> nestedObjectDeserializer, out object? value)
    {
        if (expectedType != typeof(PromptExecutionSettings))
        {
            value = null;
            return false;
        }

        var dictionary = nestedObjectDeserializer.Invoke(reader, typeof(Dictionary<string, object>));
        var modelSettings = new PromptExecutionSettings();
        foreach (var kv in (Dictionary<string, object>)dictionary!)
        {
            if (kv.Key == "service_id")
            {
                modelSettings.ServiceId = (string)kv.Value;
            }
            else if (kv.Key == "model_id")
            {
                modelSettings.ModelId = (string)kv.Value;
            }
            else
            {
                modelSettings.ExtensionData.Add(kv.Key, kv.Value);
            }
        }

        value = modelSettings;
        return true;
    }
}
