// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// HTTP schema to perform oobabooga chat completion request. Inherits from TextCompletionRequest.
/// </summary>
public sealed class ChatCompletionRequest : CompletionRequest
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
    public ChatHistory History { get; set; } = new ChatHistory();

    /// <summary>
    /// The mode of chat completion. Valid options: 'chat', 'chat-instruct', 'instruct'.
    /// </summary>
    [JsonPropertyName("mode")]
    public string Mode { get; set; } = "chat";

    /// <summary>
    /// The character name for the chat completion.
    /// </summary>
    [JsonPropertyName("character")]
    public string Character { get; set; } = "Example";

    /// <summary>
    /// The instruction template for the chat completion.
    /// </summary>
    [JsonPropertyName("instruction_template")]
    public string InstructionTemplate { get; set; } = "Vicuna-v1.1";

    /// <summary>
    /// The name to use for the user in the chat completion.
    /// </summary>
    [JsonPropertyName("your_name")]
    public string YourName { get; set; } = "You";

    /// <summary>
    /// Determines whether to regenerate the chat completion.
    /// </summary>
    [JsonPropertyName("regenerate")]
    public bool Regenerate { get; set; }

    /// <summary>
    /// Determines whether to continue the chat completion.
    /// </summary>
    [JsonPropertyName("_continue")]
    public bool Continue { get; set; }

    /// <summary>
    /// Determines whether to stop at newline in the chat completion.
    /// </summary>
    [JsonPropertyName("stop_at_newline")]
    public bool StopAtNewline { get; set; }

    /// <summary>
    /// The number of chat generation attempts.
    /// </summary>
    [JsonPropertyName("chat_generation_attempts")]
    public int ChatGenerationAttempts { get; set; } = 1;

    /// <summary>
    /// The chat-instruct command for the chat completion.
    /// </summary>
    [JsonPropertyName("chat-instruct_command")]
    public string ChatInstructCommand { get; set; } = "Continue the chat dialogue below. Write a single reply for the character \"<|character|>\".\n\n<|prompt|>";
}
