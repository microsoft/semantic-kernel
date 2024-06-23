// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using YamlDotNet.Core;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Deserializer for <see cref="FunctionSettings"/>.
/// </summary>
internal sealed class FunctionSettingsNodeDeserializer : INodeDeserializer
{
    /// <inheritdoc/>
    public bool Deserialize(IParser reader, Type expectedType, Func<IParser, Type, object?> nestedObjectDeserializer, out object? value)
    {
        if (expectedType != typeof(FunctionSettings))
        {
            value = null;
            return false;
        }

        var dictionary = nestedObjectDeserializer.Invoke(reader, typeof(Dictionary<string, object>));
        var functionSettings = new FunctionSettings();
        foreach (var kv in (Dictionary<string, object>)dictionary!)
        {
            switch (kv.Key)
            {
                default:
                    (functionSettings.ExtensionData ??= new Dictionary<string, object>()).Add(kv.Key, kv.Value);
                    break;
            }
        }

        value = functionSettings;
        return true;
    }
}
