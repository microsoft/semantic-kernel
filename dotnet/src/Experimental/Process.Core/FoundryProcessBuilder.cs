// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Agents.Persistent;
using Azure.Core;
using Azure.Identity;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder for creating a process that can be deployed to Azure Foundry.
/// </summary>
[Experimental("SKEXP0081")]
public class FoundryProcessBuilder<TProcessState> where TProcessState : class, new()
{
    private readonly ProcessBuilder _processBuilder;
    private static readonly string[] s_scopes = ["https://management.azure.com/"];

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="id">The name of the process. This is required.</param>
    /// <param name="description">The description of the Process.</param>
    public FoundryProcessBuilder(string id, string? description = null)
    {
        this._processBuilder = new ProcessBuilder(id, description, processBuilder: null, typeof(TProcessState));
    }

    /// <summary>
    /// Adds an <see cref="AzureAIAgentThread"/> to the process.
    /// </summary>
    /// <param name="threadName">The name of the thread.</param>
    /// <param name="threadPolicy">The policy that determines the lifetime of the <see cref="AzureAIAgentThread"/></param>
    /// <returns></returns>
    public ProcessBuilder AddThread(string threadName, KernelProcessThreadLifetime threadPolicy = KernelProcessThreadLifetime.Scoped)
    {
        return this._processBuilder.AddThread<AzureAIAgentThread>(threadName, threadPolicy);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="stepId">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <param name="defaultThread">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgent(AgentDefinition agentDefinition, string? stepId = null, IReadOnlyList<string>? aliases = null, string? defaultThread = null, HITLMode humanInLoopMode = HITLMode.Never)
    {
        Verify.NotNull(agentDefinition);
        if (agentDefinition.Type != AzureAIAgentFactory.AzureAIAgentType)
        {
            throw new ArgumentException($"The agent type '{agentDefinition.Type}' is not supported. Only '{AzureAIAgentFactory.AzureAIAgentType}' is supported.");
        }

        return this._processBuilder.AddStepFromAgent<TProcessState>(agentDefinition, stepId, aliases, defaultThread, humanInLoopMode);
    }

    /// <summary>
    /// Adds a step to the process from a <see cref="PersistentAgent"/>.
    /// </summary>
    /// <param name="persistantAgent">The <see cref="AgentDefinition"/></param>
    /// <param name="stepId">The unique Id of the step. If not provided, the name of the step Type will be used.</param>
    /// <param name="aliases">Aliases that have been used by previous versions of the step, used for supporting backward compatibility when reading old version Process States</param>
    /// <param name="defaultThread">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgent(PersistentAgent persistantAgent, string? stepId = null, IReadOnlyList<string>? aliases = null, string? defaultThread = null, HITLMode humanInLoopMode = HITLMode.Never)
    {
        Verify.NotNull(persistantAgent);

        var agentDefinition = new AgentDefinition
        {
            Id = persistantAgent.Id,
            Type = AzureAIAgentFactory.AzureAIAgentType,
            Name = persistantAgent.Name,
            Description = persistantAgent.Description
        };

        return this._processBuilder.AddStepFromAgent<TProcessState>(agentDefinition, stepId, aliases, defaultThread, humanInLoopMode);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="stepId">Id of the step. If not provided, the Id will come from the agent Id.</param>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="threadName">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    /// <param name="aliases"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgentProxy(string stepId, AgentDefinition agentDefinition, string? threadName = null, HITLMode humanInLoopMode = HITLMode.Never, IReadOnlyList<string>? aliases = null) // TODO: Is there a better way to model this?
    {
        Verify.NotNullOrWhiteSpace(stepId);
        Verify.NotNull(agentDefinition);
        if (agentDefinition.Type != AzureAIAgentFactory.AzureAIAgentType)
        {
            throw new ArgumentException($"The agent type '{agentDefinition.Type}' is not supported. Only '{AzureAIAgentFactory.AzureAIAgentType}' is supported.");
        }

        return this._processBuilder.AddStepFromAgentProxy<TProcessState>(agentDefinition, threadName, stepId, humanInLoopMode, aliases);
    }

    /// <summary>
    /// Provides an instance of <see cref="ProcessEdgeBuilder"/> for defining an input edge to a process.
    /// </summary>
    /// <param name="eventId">The Id of the external event.</param>
    /// <returns>An instance of <see cref="ProcessEdgeBuilder"/></returns>
    internal ProcessEdgeBuilder OnInputEvent(string eventId)
    {
        return this._processBuilder.OnInputEvent(eventId);
    }

    /// <summary>
    /// Creates a <see cref="ListenForBuilder"/> instance to define a listener for incoming messages.
    /// </summary>
    /// <param name="step"> The process step from which the message originates.</param>
    /// <param name="eventName"> The name of the event to listen for.</param>
    /// <param name="condition">An optional condition using JMESPath syntax.</param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder OnEvent(ProcessStepBuilder step, string eventName, string? condition = null)
    {
        Verify.NotNull(step);
        Verify.NotNullOrWhiteSpace(eventName);
        return new FoundryListenForBuilder(this._processBuilder).Message(eventName, step, condition);
    }

    /// <summary>
    /// Creates a <see cref="ListenForBuilder"/> instance to define a listener for when the process step is entered.
    /// </summary>
    /// <param name="step"></param>
    /// <param name="condition"></param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder OnStepEnter(ProcessStepBuilder step, string? condition = null)
    {
        Verify.NotNull(step);
        return new FoundryListenForBuilder(this._processBuilder).OnEnter(step, condition);
    }

    /// <summary>
    /// Creates a <see cref="ListenForBuilder"/> instance to define a listener for when the process step is exited.
    /// </summary>
    /// <param name="step"></param>
    /// <param name="condition"></param>
    /// <returns></returns>
    public FoundryListenForTargetBuilder OnStepExit(ProcessStepBuilder step, string? condition = null)
    {
        Verify.NotNull(step);
        return new FoundryListenForBuilder(this._processBuilder).OnExit(step, condition);
    }

    /// <summary>
    /// Creates a <see cref="ListenForBuilder"/> instance to define a listener for when the process starts.
    /// </summary>
    /// <returns></returns>
    public FoundryListenForTargetBuilder OnProcessEnter()
    {
        return new FoundryListenForBuilder(this._processBuilder).ProcessStart();
    }

    /// <summary>
    /// Builds the process.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="NotImplementedException"></exception>
    public KernelProcess Build(KernelProcessStateMetadata? stateMetadata = null)
    {
        return this._processBuilder.Build(stateMetadata);
    }

    /// <summary>
    /// Deploys the process to Azure Foundry.
    /// </summary>
    /// <param name="endpoint">Th workflow endpoint to deploy to.</param>
    /// <param name="credential">The credential to use.</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<string> DeployToFoundryAsync(string endpoint, TokenCredential? credential = null, CancellationToken cancellationToken = default)
    {
        // Build the process
        var process = this.Build();

        // Serialize and deploy
        using var httpClient = new HttpClient();
        if (credential != null)
        {
            var token = await credential.GetTokenAsync(new TokenRequestContext(s_scopes), cancellationToken).ConfigureAwait(false);
            httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {token.Token}");
        }
        else
        {
            var token = await new DefaultAzureCredential().GetTokenAsync(new TokenRequestContext(s_scopes), cancellationToken).ConfigureAwait(false);
            httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {token.Token}");
        }

        var workflow = await WorkflowBuilder.BuildWorkflow(process).ConfigureAwait(false);
        string json = WorkflowSerializer.SerializeToJson(workflow);
        using var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
        var response = await httpClient.PostAsync(new Uri($"{endpoint}/agents?api-version=2025-05-01-preview"), content, cancellationToken).ConfigureAwait(false);

        if (!response.IsSuccessStatusCode)
        {
            var errorContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            throw new KernelException($"Failed to deploy process. Response: {errorContent}");
        }

        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        var foundryWorkflow = JsonSerializer.Deserialize<FoundryWorkflow>(responseContent);
        return foundryWorkflow?.Id ?? throw new KernelException("Failed to parse the response from Foundry.");
    }

    /// <summary>
    /// Serializes the process to JSON.
    /// </summary>
    public async Task<string> ToJsonAsync()
    {
        var process = this.Build();
        var workflow = await WorkflowBuilder.BuildWorkflow(process).ConfigureAwait(false);
        return WorkflowSerializer.SerializeToJson(workflow);
    }

    private class FoundryWorkflow
    {
        [JsonPropertyName("id")]
        public string? Id { get; set; }
    }
}

/// <summary>
/// A builder for creating a process that can be deployed to Azure Foundry.
/// </summary>
public class FoundryProcessBuilder : FoundryProcessBuilder<FoundryProcessDefaultState>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FoundryProcessBuilder"/> class.
    /// </summary>
    /// <param name="id"></param>
    public FoundryProcessBuilder(string id) : base(id)
    {
    }
}

/// <summary>
/// A default process state for the <see cref="FoundryProcessBuilder"/>.
/// </summary>
public class FoundryProcessDefaultState
{
}
