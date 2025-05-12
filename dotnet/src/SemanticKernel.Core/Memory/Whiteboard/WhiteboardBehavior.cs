// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An <see cref="AIContextBehavior"/> that maintains a whiteboard during a conversation.
/// </summary>
[Experimental("SKEXP0130")]
public class WhiteboardBehavior : AIContextBehavior
{
    private const int MaxQueueSize = 3;
    private readonly int _maxWhiteboardMessages;

    private readonly Kernel _kernel;

    private List<string> _currentWhiteboardContent = [];

    private readonly ConcurrentQueue<ChatMessage> _recentMessages = new();
    private ChatMessage? _messageBeingProcessed = null;
    private Task _updateWhiteboardTask = Task.CompletedTask;

    /// <summary>
    /// Initializes a new instance of the <see cref="WhiteboardBehavior"/> class.
    /// </summary>
    /// <param name="kernel">A kernel to use for making chat completion calls.</param>
    /// <param name="options">Options for configuring the behavior.</param>
    public WhiteboardBehavior(Kernel kernel, WhiteboardBehaviorOptions? options = default)
    {
        this._kernel = kernel;
        this._maxWhiteboardMessages = options?.MaxWhiteboardMessages ?? 10;
    }

    /// <inheritdoc/>
    public override IReadOnlyCollection<AIFunction> AIFunctions => Array.Empty<AIFunction>();

    /// <summary>
    /// Gets the current whiteboard content.
    /// </summary>
    public IReadOnlyList<string> CurrentWhiteboardContent => this._currentWhiteboardContent;

    /// <inheritdoc/>
    public override async Task OnNewMessageAsync(string? threadId, ChatMessage newMessage, CancellationToken cancellationToken = default)
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
    public override Task<string> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        if (this._currentWhiteboardContent.Count == 0)
        {
            return Task.FromResult("The whiteboard is currently empty.");
        }

        var numberedMessages = this._currentWhiteboardContent.Select((x, i) => $"{i} {x}");
        var joinedMessages = string.Join(Environment.NewLine, numberedMessages);
        return Task.FromResult($"The following list has all messages currently on the whiteboard:\n{joinedMessages}");
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

        // Extrac the most important information from the input mesages.
        var basicMessages = recentMessagesList
            .Select(m => new BasicMessage
            {
                AuthorName = m.AuthorName,
                Role = m.Role.ToString(),
                Text = m.Text
            });

        // Serialize the input messages and the current whiteboard content to JSON.
        var inputMessagesJson = JsonSerializer.Serialize(basicMessages, WhiteboardBehaviorSourceGenerationContext.Default.IEnumerableBasicMessage);
        var currentWhiteboardJson = JsonSerializer.Serialize(this._currentWhiteboardContent, WhiteboardBehaviorSourceGenerationContext.Default.ListString);

        // Inovke the LLM to extract the latest information from the input messages and update the whiteboard.
        var result = await this._kernel.InvokePromptAsync(
            new JsonSerializerOptions(),
            MaintenancePromptTemplate,
            new KernelArguments()
            {
                ["formattedMessages"] = inputMessagesJson,
                ["newMessageAuthorName"] = newMessage.AuthorName,
                ["newMessageRole"] = newMessage.Role.ToString(),
                ["currentWhiteboard"] = currentWhiteboardJson,
                ["maxWhiteboardMessages"] = this._maxWhiteboardMessages,
            },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        // Update the current whiteboard content with the LLM result.
        this._currentWhiteboardContent = JsonSerializer.Deserialize(result.ToString(), WhiteboardBehaviorSourceGenerationContext.Default.ListString) ?? [];
    }

    /// <summary>
    /// Gets the prompt template to use for maintaining the whiteboard.
    /// </summary>
    private const string MaintenancePromptTemplate =
        """
        You are an expert in maintaining a whiteboard during a conversation.
        The whiteboard should maintain the requirements that the user is trying to meet, the latest proposal and any decisions that have been made by the users.
        A proposal is a suggested solution to requirements provided by the user or the assistant.
        Existing information on the whiteboard should be updated with new information as requirements change and new proposals and decisions are made.
        Decisions should contain all information about the decision made.
        When a decision is made, the proposals and requirements that led to the decision should be removed from the whiteboard.
        Whiteboard entries should be concise and to the point.
        The whiteboard can contain more than one piece of information for each category.
        The maximum number of messages allowed on the whiteboard at one time is {{$maxWhiteboardMessages}}.
        Combine messages or remove the least important messages from the list if the maximum number of messages is reached.
        Prioritize keeping detailed decisions for longer than requirements and proposals.
        Categorize whiteboard entries with a prefix of REQUIREMENT, PROPOSAL or DECISION.
        
        Here are 7 few shot examples:

        EXAMPLES START

        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"I want the colour scheme to be green and brown."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to create a presentation."]
        New Whiteboard:
        ["REQUIREMENT - Mary wants to create a presentation.", "REQUIREMENT - The presentation colour schema should be green and brown."]
        
        New Message:
        [{"AuthorName":"John","Role":"user","Text":"I need you to help me with my homework."}]
        Current Whiteboard:
        []
        New Whiteboard:
        ["REQUIREMENT - John wants help with homework."]

        New Message:
        [{"AuthorName":"John","Role":"user","Text":"Hello"}]
        Current Whiteboard:
        []
        New Whiteboard:
        []
        
        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"I've changed my mind, I want to go to London instead."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris."]
        New Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to London."]
        
        New Message:
        [{"AuthorName":"TravelAgent","Role":"assistant","Text":"Here is an itinerary for your trip to Paris. Departing on the 17th of June at 10:00 AM and returning on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025."]
        New Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "PROPOSAL - The current proposed itinerary by the TravelAgent Assistant is to depart on the 17th of June at 10:00 AM and return on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]
        
        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"That sounds good, let's book that."}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "PROPOSAL - The current proposed itinerary by the TravelAgent Assistant is to depart on the 17th of June at 10:00 AM and return on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]
        New Whiteboard:
        [""DECISION - Mary decided to book the flight departing on the 17th of June at 10:00 AM and returning on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]

        New Message:
        [{"AuthorName":"Mary","Role":"user","Text":"I don't like the suggested option. Can I leave a day earlier and fly with anyone but NotsocheapoAir?"}]
        Current Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "PROPOSAL - The current proposed itinerary by the TravelAgent Assistant is to depart on the 17th of June at 10:00 AM and return on the 20th of June at 5:00 PM with direct flights to Paris Charles de Gaul airport on NotsocheapoAir. The cost of the flights are EUR 243."]
        New Whiteboard:
        ["REQUIREMENT - Mary wants to book a flight.", "REQUIREMENT - The flight should be to Paris during the week of 16th of June 2025.", "REQUIREMENT - Mary does not want to fly with NotsocheapoAir."]
        
        EXAMPLES END

        Return a new whiteboard for the following inputs like shown in the examples above:

        New Message:
        {{$formattedMessages}}
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
}

/// <summary>
/// Source generated json serializer for <see cref="WhiteboardBehavior"/>.
/// </summary>
[Experimental("SKEXP0130")]
[JsonSourceGenerationOptions(JsonSerializerDefaults.General,
    UseStringEnumConverter = false,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    WriteIndented = false)]
[JsonSerializable(typeof(IEnumerable<WhiteboardBehavior.BasicMessage>))]
[JsonSerializable(typeof(WhiteboardBehavior.BasicMessage))]
[JsonSerializable(typeof(List<string>))]
internal partial class WhiteboardBehaviorSourceGenerationContext : JsonSerializerContext
{
}
