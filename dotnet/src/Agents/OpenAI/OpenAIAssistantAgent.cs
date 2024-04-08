// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on Open AI Assistant / GPT.
/// </summary>
public sealed partial class OpenAIAssistantAgent : KernelAgent
{
    private readonly Assistant _assistant;
    private readonly AssistantsClient _client;
    private readonly OpenAIAssistantServiceOptions _options; // $$$ WHERE USED ??? (BACK TO PARTITIONKEY ???)

    /// <inheritdoc/>
    public override string? Description => this._assistant.Description;

    /// <inheritdoc/>
    public override string Id => this._assistant.Id;

    /// <inheritdoc/>
    public override string? Name => this._assistant.Name;

    /// <summary>
    /// Expose predefined tools.
    /// </summary>
    internal IReadOnlyList<ToolDefinition> Tools => this._assistant.Tools;

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(AgentChannel<OpenAIAssistantAgent>).FullName;
        yield return this._options.Endpoint ?? "openai";
    }

    /// <inheritdoc/>
    protected override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        var thread = await this._client.CreateThreadAsync(cancellationToken).ConfigureAwait(false);

        return new Channel(/*this._client, */thread.Value.Id); // $$$
    }

    // $$$ DELETEASYNC

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgent"/> class.
    /// </summary>
    private OpenAIAssistantAgent(
        Kernel kernel,
        AssistantsClient client,
        Assistant model,
        OpenAIAssistantServiceOptions options)
        : base(kernel)
    {
        this._assistant = model;
        this._client = client;
        this._options = options;
        this.Instructions = model.Instructions;
    }
}
