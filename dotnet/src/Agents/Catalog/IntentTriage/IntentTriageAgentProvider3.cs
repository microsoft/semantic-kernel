// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// Provider to create a <see cref="IntentTriageAgent3"/> instance and
/// its associated <see cref="AgentThread"/>.
/// </summary>
public class IntentTriageAgentProvider3(IConfiguration configuration, ILoggerFactory loggerFactory)
    : ServiceAgentProvider(configuration, loggerFactory)
{
    /// <inheritdoc/>
    public override async ValueTask<Agent> CreateAgentAsync(string id, string? name, CancellationToken cancellationToken)
    {
        IntentTriageLanguageSettings languageSettings = IntentTriageLanguageSettings.FromConfiguration(this.Configuration);

        Kernel kernel =
            await KernelFactory.CreateKernelAsync(
                this.Client,
                this.FoundrySettings.DeploymentName,
                this.LoggerFactory);

        IntentTriageAgent3 agent =
            new(languageSettings)
            {
                Id = id,
                Name = name,
                Kernel = kernel,
            };

        return agent;
    }

    /// <inheritdoc/>
    public override async ValueTask<AgentThread> CreateThreadAsync(string threadId, CancellationToken cancellationToken)
    {
        // Only retrieve the most recent message to analyze
        IAsyncEnumerable<ChatMessageContent> messages = this.GetThreadMessagesAsync(threadId, limit: 1, cancellationToken);
        ChatHistory history = [.. await messages.ToArrayAsync(cancellationToken)];

        ChatHistoryAgentThread agentThread = new(history, threadId);

        return agentThread;
    }
}
