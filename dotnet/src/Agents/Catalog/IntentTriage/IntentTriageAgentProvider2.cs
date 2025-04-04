// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;
using Foundry = Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// Provider to create a <see cref="IntentTriageAgent2"/> instance and
/// its associated <see cref="AgentThread"/>.
/// </summary>
public class IntentTriageAgentProvider2 : ServiceAgentProvider
{
    private readonly IntentTriageServiceSettings _serviceSettings;
    private readonly IntentTriageLanguageSettings _languagSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="IntentTriageAgentProvider2"/> class.
    /// </summary>
    /// <param name="configuration">The configuration used to initialize the agent.</param>
    /// <param name="loggerFactory">The logging services for the agent.</param>
    public IntentTriageAgentProvider2(IConfiguration configuration, ILoggerFactory loggerFactory)
        : base(configuration, loggerFactory)
    {
        this._serviceSettings = IntentTriageServiceSettings.FromConfiguration(configuration);
        this._languagSettings = IntentTriageLanguageSettings.FromConfiguration(configuration);
    }

    /// <inheritdoc/>
    public override ValueTask<Agent> CreateAgentAsync(string id, string? name, CancellationToken cancellationToken)
    {
        Kernel kernel = KernelFactory.CreateKernel(this._serviceSettings, this.LoggerFactory);
        IntentTriageAgent2 agent =
            new(this._languagSettings)
            {
                Id = id,
                Name = name,
                Kernel = kernel,
            };
        return ValueTask.FromResult<Agent>(agent);
    }

    /// <inheritdoc/>
    public override async ValueTask<AgentThread> CreateThreadAsync(string threadId, CancellationToken cancellationToken)
    {
        Foundry.AIProjectClient client = new(
            this.Configuration.GetRequiredValue(this._serviceSettings.ConnectionString),
            new AzureCliCredential());

        // We only need the most recent message to analyze
        IAsyncEnumerable<ChatMessageContent> messages = GetThreadMessagesAsync(client.GetAgentsClient(), threadId, limit: 1, cancellationToken);
        ChatHistory history = [.. await messages.ToArrayAsync(cancellationToken)];

        ChatHistoryAgentThread agentThread = new(history, threadId);

        return agentThread;
    }
}
