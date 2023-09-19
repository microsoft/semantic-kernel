// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

// TODO: remove this temporary class

/// <summary>
/// Represents the settings for a chat request to the OpenAI API
/// </summary>
public class OpenAIChatRequestSettings : ChatRequestSettings
{
    /// <summary>
    /// The set of functions to choose from if function calling is enabled by the model.
    /// </summary>
    public IList<OpenAIFunction>? Functions { get; set; } = null;
}
