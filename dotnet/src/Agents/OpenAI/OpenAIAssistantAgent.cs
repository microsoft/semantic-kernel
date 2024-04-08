// Copyright (c) Microsoft. All rights reserved.
using System;
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
    private readonly OpenAIAssistantConfiguration _config;

    /// <inheritdoc/>
    public override string? Description => this._assistant.Description;

    /// <inheritdoc/>
    public override string Id => this._assistant.Id;

    /// <inheritdoc/>
    public override string? Name => this._assistant.Name;

    /// <inheritdoc/>
    public new string? Instructions => base.Instructions;

    /// <summary>
    /// Expose predefined tools.
    /// </summary>
    internal IReadOnlyList<ToolDefinition> Tools => this._assistant.Tools;

    /// <summary>
    /// Set when the assistant has been deleted via <see cref="DeleteAsync(CancellationToken)"/>.
    /// An assistant removed by other means will result in an exception when invoked.
    /// </summary>
    public bool IsDeleted { get; private set; }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(AgentChannel<OpenAIAssistantAgent>).FullName;
        yield return this._config.Endpoint ?? "openai";

        if (this._config.Version.HasValue)
        {
            yield return this._config.Version!.ToString();
        }

        if (this._config.HttpClient != null)
        {
            yield return Guid.NewGuid().ToString();
        }
    }

    /// <inheritdoc/>
    protected override async Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        AssistantThread thread = await this._client.CreateThreadAsync(cancellationToken).ConfigureAwait(false);

        return new Channel(this._client, thread.Id);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            return;
        }

        await this._client.DeleteAssistantAsync(this.Id, cancellationToken).ConfigureAwait(false);

        this.IsDeleted = true;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgent"/> class.
    /// </summary>
    private OpenAIAssistantAgent(
        Kernel kernel,
        AssistantsClient client,
        Assistant model,
        OpenAIAssistantConfiguration config)
        : base(kernel)
    {
        this._assistant = model;
        this._client = client;
        this._config = config;
        base.Instructions = model.Instructions;
    }
}
