// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An <see cref="AIContextProvider"/> that maintains a whiteboard during a conversation.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class WhiteboardProvider : AIContextProvider
{
    private readonly static JsonDocument s_structuredOutputSchema = JsonDocument.Parse("""{"type":"object","properties":{"newWhiteboard":{"type":"array","items":{"type":"string"}}}}""");
    private const string DefaultContextPrompt = "## Whiteboard\nThe following list of messages are currently on the whiteboard:";
    private const string DefaultWhiteboardEmptyPrompt = "## Whiteboard\nThe whiteboard is currently empty.";
    private const int MaxQueueSize = 3;

    private readonly int _maxWhiteboardMessages;
    private readonly string _contextPrompt;
    private readonly string _whiteboardEmptyPrompt;
    private readonly string _maintenancePrompt;

    private readonly IChatClient _chatClient;
    private readonly ILogger? _logger;

    private List<string> _currentWhiteboardContent = [];

    private readonly ConcurrentQueue<ChatMessage> _recentMessages = new();
    private ChatMessage? _messageBeingProcessed = null;
    private Task _updateWhiteboardTask = Task.CompletedTask;

    /// <summary>
    /// Initializes a new instance of the <see cref="WhiteboardProvider"/> class.
    /// </summary>
    /// <param name="chatClient">A <see cref="IChatClient"/> to use for making chat completion calls.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="options">Options for configuring the provider.</param>
    public WhiteboardProvider(IChatClient chatClient, ILoggerFactory? loggerFactory = default, WhiteboardProviderOptions? options = default)
    {
        Verify.NotNull(chatClient);

        this._chatClient = chatClient;
        this._maxWhiteboardMessages = options?.MaxWhiteboardMessages ?? 10;
        this._contextPrompt = options?.ContextPrompt ?? DefaultContextPrompt;
        this._whiteboardEmptyPrompt = options?.WhiteboardEmptyPrompt ?? DefaultWhiteboardEmptyPrompt;
        this._maintenancePrompt = options?.MaintenancePromptTemplate ?? MaintenancePromptTemplate;
        this._logger = loggerFactory?.CreateLogger<WhiteboardProvider>();
    }

    /// <summary>
    /// Gets the current whiteboard content.
    /// </summary>
    public IReadOnlyList<string> CurrentWhiteboardContent => this._currentWhiteboardContent;

    /// <inheritdoc/>
    public override async Task MessageAddingAsync(string? conversationId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(newMessage.Text))
        {
            return;
        }

        if (newMessage.Role == ChatRole.User || newMessage.Role == ChatRole.Assistant)
        {
            this._recentMessages.Enqueue(newMessage);

            // Store the last message that we got as a way to avoid doing multiple updates at the same time.
            Interlocked.CompareExchange(ref this._messageBeingProcessed, newMessage, this._messageBeingProcessed);

            // If a whiteboard update task is already running, wait for it to finish before starting a new one.
            if (!this._updateWhiteboardTask.IsCompleted)
            {
                await this._updateWhiteboardTask.ConfigureAwait(false);
            }

            // If our message isn't the last one we got, we don't need to do anything since
            // we will run the update, on the thread that received the last message.
            if (this._messageBeingProcessed != newMessage)
            {
                return;
            }

            this._updateWhiteboardTask = this.UpdateWhiteboardAsync(newMessage, cancellationToken);
        }
    }

    /// <inheritdoc/>
    public override Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        // Take a reference to the current whiteboard to avoid inconsistent logging and results
        // if it's updated during this method's execution.
        var currentWhiteboard = this._currentWhiteboardContent;

        if (currentWhiteboard.Count == 0)
        {
            this._logger?.LogTrace("WhiteboardBehavior: Output context instructions:\n{Context}", this._whiteboardEmptyPrompt);
            return Task.FromResult(new AIContext() { Instructions = this._whiteboardEmptyPrompt });
        }

        var numberedMessages = currentWhiteboard.Select((x, i) => $"{i} {x}");
        var joinedMessages = string.Join(Environment.NewLine, numberedMessages);
        var context = $"{this._contextPrompt}\n{joinedMessages}";

        this._logger?.LogInformation("WhiteboardBehavior: Whiteboard contains {Count} messages.", currentWhiteboard.Count);
        this._logger?.LogTrace("WhiteboardBehavior: Output context instructions:\n{Context}", context);

        return Task.FromResult(new AIContext()
        {
            Instructions = context
        });
    }

    /// <summary>
    /// Wait for all messages to be processed and the whiteboard to be up to date.
    /// </summary>
    /// <returns>A task that completes when all messages are processed.</returns>
    public async Task WhenProcessingCompleteAsync()
    {
        if (!this._updateWhiteboardTask.IsCompleted)
        {
            await this._updateWhiteboardTask.ConfigureAwait(false);
        }
    }

    private async Task UpdateWhiteboardAsync(ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        var recentMessagesList = this._recentMessages.ToList();

        // If there are more than MaxQueueSize messages in the queue, remove the oldest ones
        for (int i = MaxQueueSize; i < recentMessagesList.Count; i++)
        {
            this._recentMessages.TryDequeue(out _);
        }

        // Extract the most important information from the input messages.
        var basicMessages = recentMessagesList
            .Select(m => new BasicMessage
            {
                AuthorName = m.AuthorName,
                Role = m.Role.ToString(),
                Text = m.Text
            });

        // Serialize the input messages and the current whiteboard content to JSON.
        var inputMessagesJson = JsonSerializer.Serialize(basicMessages, WhiteboardProviderSourceGenerationContext.Default.IEnumerableBasicMessage);
        var currentWhiteboardJson = JsonSerializer.Serialize(this._currentWhiteboardContent, WhiteboardProviderSourceGenerationContext.Default.ListString);

        // Inovke the LLM to extract the latest information from the input messages and update the whiteboard.
        var result = await this._chatClient.GetResponseAsync(
            this.FormatPromptTemplate(inputMessagesJson, currentWhiteboardJson, this._maxWhiteboardMessages),
            new()
            {
                Temperature = 0,
                ResponseFormat = new ChatResponseFormatJson(s_structuredOutputSchema.RootElement),
            },
            cancellationToken).ConfigureAwait(false);

        // Update the current whiteboard content with the LLM result.
        var newWhiteboardResponse = JsonSerializer.Deserialize(result.ToString(), WhiteboardProviderSourceGenerationContext.Default.NewWhiteboardResponse);
        this._currentWhiteboardContent = newWhiteboardResponse?.NewWhiteboard ?? [];

        this._logger?.LogTrace(
            "WhiteboardBehavior: Updated whiteboard.\nInputMessages:\n{InputMessagesJson}\nCurrentWhiteboard:\n{CurrentWhiteboardJson}\nNew Whiteboard:\n{NewWhiteboard}",
            inputMessagesJson,
            currentWhiteboardJson,
            result);
    }

    private string FormatPromptTemplate(string inputMessagesJson, string currentWhiteboardJson, int maxWhiteboardMessages)
    {
        var sb = new StringBuilder(this._maintenancePrompt);
        sb.Replace("{{$inputMessages}}", inputMessagesJson);
        sb.Replace("{{$currentWhiteboard}}", currentWhiteboardJson);
        sb.Replace("{{$maxWhiteboardMessages}}", maxWhiteboardMessages.ToString());
        return sb.ToString();
    }

    /// <summary>
    /// Gets the prompt template to use for maintaining the whiteboard.
    /// </summary>
    private const string MaintenancePromptTemplate =
        """
        You are an expert in maintaining a whiteboard during a conversation.The whiteboard should capture:
        - **Requirements**: Goals or needs expressed by the user.
        - **Proposals**: Suggested solutions to the requirements, provided by the assistant.
        - **Decisions**: Decisions made by the user, including all relevant details.
        - **Actions**: Actions that had been taken to implement a proposal or decision, including all relevant details.

        ## Transitions:
        - **Requirements -> Proposal**: When a proposal is made to satisfy one or more requirements.
        - **Proposal -> Decision**: When a proposal is accepted by the user.
        - **Proposal -> Actions**: When an action has been taken to execute a proposal.
        - **Decision -> Actions**: When an action has been taken to implement a decision.

        ## Guidelines:
        1. **Update Existing Entries**: Modify whiteboard entries as requirements change or new proposals and decisions are made.
        2. **User is decision maker**: Only users can make decisions. The assistant can only make proposals and execute them.
        3. **Remove Redundant Information**: When a decision is made or an action is taken, remove the requirements and proposals that led to it.
        4. **Keep Requirements Concise**: Ensure requirements are clear and to the point.
        5. **Keep Decisions, Proposals and Actions Detailed**: Ensure decisions, proposals and actions are comprehensive and include all requirements that went into the decision, proposal or action.
        6. **Keep Decisions, Proposals and Actions Self Contained**: Ensure decisions, proposals and actions are self-contained and do not reference other entries, e.g. output "ACTION - The agent booked flight going out, COA 1133 DUB to CDG, 14 April 2025 and return, COA 1134 CDG to DUB, 16 April 2025", instead of "ACTION - The agent booked the flights as defined in requirements.".
        7. **Categorize Entries**: Prefix each entry with `REQUIREMENT`, `PROPOSAL`, `DECISION` or `ACTION`.
        8. **Prioritize Decisions and Actions**: Retain detailed decisions and actions longer than requirements or proposals.
        9. **Limit Entries**: Maintain a maximum of {{$maxWhiteboardMessages}} entries. If the limit is exceeded, combine or remove the least important entries, prioritize keeping decisions and actions.

        ## Examples:

        ### Example 1:

        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"I want the colour scheme to be green and brown."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to create a presentation."]
        New Whiteboard:
        {"newWhiteboard":["REQUIREMENT - Mary wants to create a presentation.", "REQUIREMENT - The presentation colour schema should be green and brown."]}

        ### Example 2:

        New Message:
        [{"AuthorName":"John","Role":"user","Text":"I need you to help me with my homework."}]
        Current Whiteboard:
        []
        New Whiteboard:
        {"newWhiteboard":["REQUIREMENT - John wants help with homework."]}

        ### Example 3:

        New Message:
        [{"AuthorName":"John","Role":"user","Text":"Hello"}]
        Current Whiteboard:
        []
        New Whiteboard:
        {"newWhiteboard":[]}

        ### Example 4:

        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"I've changed my mind, I want to go to London instead."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris."]
        New Whiteboard:
        {"newWhiteboard":["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to London."]}

        ### Example 5:

        New Message:
        [{"AuthorName":"TravelAgent","Role":"assistant","Text":"Here is an itinerary for your trip to Paris. Departing on the 17th of June at 10:00 AM and returning on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025."]
        New Whiteboard:
        {"newWhiteboard":["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "PROPOSAL - The current proposed itinerary by the TravelAgent Assistant is to depart on the 17th of June at 10:00 AM and return on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]}

        ### Example 6:

        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"That sounds good, let's book that."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "PROPOSAL - The current proposed itinerary by the TravelAgent Assistant is to depart on the 17th of June at 10:00 AM and return on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]
        New Whiteboard:
        {"newWhiteboard":["DECISION - Mary decided to book the flight departing on the 17th of June at 10:00 AM and returning on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]}

        ### Example 7:
        
        New Message:
        [{"AuthorName":"TravelAgent","Role":"assistant","Text":"OK, I've booked that for you."}]
        Current Whiteboard:
        [""DECISION - Mary decided to book the flight departing on the 17th of June at 10:00 AM and returning on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]
        New Whiteboard:
        {"newWhiteboard":["ACTION - TravelAgent booked a flight for Mary departing on the 17th of June at 10:00 AM and returning on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir for EUR 243."]}
        
        ### Example 8:

        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"I don't like the suggested option. Can I leave a day earlier and fly with anyone but NotsocheapoAir?"}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "PROPOSAL - The current proposed itinerary by the TravelAgent Assistant is to depart on the 17th of June at 10:00 AM and return on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]
        New Whiteboard:
        {"newWhiteboard":["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "REQUIREMENT - Mary does not want to fly with NotsocheapoAir."]}

        ## Action

        Now return a new whiteboard for the following inputs like shown in the examples above and using the previously mentioned instructions:

        New Message:
        {{$inputMessages}}
        Current Whiteboard:
        {{$currentWhiteboard}}
        New Whiteboard:
        """;

    /// <summary>
    /// A simple message class that contains just the most basic msessage information
    /// that is required to pass to the LLM.
    /// </summary>
    internal class BasicMessage
    {
        public string? AuthorName { get; set; }
        public string Role { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
    }

    /// <summary>
    /// Represents the response from the LLM when updating the whiteboard.
    /// </summary>
    internal class NewWhiteboardResponse
    {
        [JsonPropertyName("newWhiteboard")]
        public List<string> NewWhiteboard { get; set; } = [];
    }
}

/// <summary>
/// Source generated json serializer for <see cref="WhiteboardProvider"/>.
/// </summary>
[Experimental("SKEXP0130")]
[JsonSourceGenerationOptions(JsonSerializerDefaults.General,
    UseStringEnumConverter = false,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    WriteIndented = false)]
[JsonSerializable(typeof(IEnumerable<WhiteboardProvider.BasicMessage>))]
[JsonSerializable(typeof(WhiteboardProvider.BasicMessage))]
[JsonSerializable(typeof(List<string>))]
[JsonSerializable(typeof(WhiteboardProvider.NewWhiteboardResponse))]
internal partial class WhiteboardProviderSourceGenerationContext : JsonSerializerContext
{
}
