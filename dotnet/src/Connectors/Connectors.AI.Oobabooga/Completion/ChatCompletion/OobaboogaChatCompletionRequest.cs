// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// HTTP schema to perform oobabooga chat completion request.
/// </summary>
public sealed class OobaboogaChatCompletionRequest : OobaboogaChatCompletionParameters
{
    /// <summary>
    /// The user input for the chat completion.
    /// </summary>
    [JsonPropertyName("user_input")]
    public string UserInput { get; set; } = string.Empty;

    /// <summary>
    /// The chat history.
    /// </summary>
    [JsonPropertyName("history")]
    public OobaboogaChatHistory History { get; set; } = new OobaboogaChatHistory();

    /// <summary>
    /// Creates a new ChatCompletionRequest with the given Chat history, oobabooga settings and semantic-kernel settings.
    /// </summary>
    public static OobaboogaChatCompletionRequest Create(ChatHistory chat, OobaboogaCompletionSettings<OobaboogaChatCompletionParameters> settings, ChatRequestSettings requestSettings)
    {
        var chatMessages = chat.Messages.Take(chat.Messages.Count - 1).Select(@base => @base.Content).ToList();
        var toReturn = new OobaboogaChatCompletionRequest()
        {
            UserInput = chat.Messages.Last().Content,
            History = new OobaboogaChatHistory()
            {
                Internal = chatMessages.Count > 1 ? new() { chatMessages } : new(),
                Visible = chatMessages.Count > 1 ? new() { chatMessages } : new(),
            },
        };
        toReturn.Apply(settings.OobaboogaParameters);
        if (!settings.OverrideSKSettings)
        {
            toReturn.MaxNewTokens = requestSettings.MaxTokens;
            toReturn.Temperature = requestSettings.Temperature;
            toReturn.TopP = requestSettings.TopP;
            toReturn.RepetitionPenalty = GetRepetitionPenalty(requestSettings.PresencePenalty);
            toReturn.StoppingStrings = requestSettings.StopSequences.ToList();
        }

        return toReturn;
    }
}
