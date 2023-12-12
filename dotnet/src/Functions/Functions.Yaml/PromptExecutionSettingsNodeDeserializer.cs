// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using YamlDotNet.Core;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Deserializer for <see cref="PromptExecutionSettings"/>.
/// </summary>
internal sealed class PromptExecutionSettingsNodeDeserializer : INodeDeserializer
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
            switch (kv.Key)
            {
                case "service_id":
                    modelSettings.ServiceId = (string)kv.Value;
                    break;

                case "model_id":
                    modelSettings.ModelId = (string)kv.Value;
                    break;

                default:
                    (modelSettings.ExtensionData ??= new()).Add(kv.Key, kv.Value);
                    break;
            }
        }

        value = modelSettings;
        return true;
    }
}
