// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary> Represents a singular result of a chat completion.</summary>
public class ChatModelResult : OpenAiModelResult
{
    /// <summary>
    /// The completion choice associated with this completion result.
    /// </summary>
    public ChatChoice Choice { get; }

    /// <summary> Initializes a new instance of TextModelResult. </summary>
    /// <param name="completionsData"> A completions response object to populate the fields relative the the response.</param>
    /// <param name="choiceData"> A choice object to populate the fields relative to the resulting choice.</param>
    internal ChatModelResult(ChatCompletions completionsData, ChatChoice choiceData) : base(completionsData.Id, completionsData.Created, completionsData.PromptFilterResults, completionsData.Usage)
    {
        this.Choice = choiceData;
    }
}
