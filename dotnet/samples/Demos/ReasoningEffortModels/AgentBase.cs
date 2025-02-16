// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using ReasoningEffortModels.Options;

#pragma warning disable SKEXP0110, SKEXP0001, SKEXP0050, CS8600, CS8604

namespace ReasoningEffortModels;

public abstract class AgentBase
{
    protected readonly Kernel _kernel;
    // Store the reasoning effort level for use later
    protected readonly ChatReasoningEffortLevel _reasoningEffort;

    public abstract string AgentName { get; }
    public abstract string AgentPrompt { get; }
    public abstract string DefaultDeploymentName { get; }

    /// <summary>
    /// Initializes a new instance of the AgentBase class.
    /// </summary>
    /// <param name="customKernel">An optional custom kernel.</param>
    /// <param name="deploymentName">An optional deployment name. If not provided, DefaultDeploymentName is used.</param>
    /// <param name="reasoningEffort">An optional reasoning effort level. Defaults to Medium if not provided.</param>
    public AgentBase(
        Kernel? customKernel = null,
        string? deploymentName = null,
        ChatReasoningEffortLevel? reasoningEffort = null)
    {
        this._reasoningEffort = reasoningEffort ?? ChatReasoningEffortLevel.Low;

        var config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        var azureOpenAIOptions = config.GetSection(AzureOpenAIOptions.SectionName).Get<AzureOpenAIOptions>();


        string chosenDeployment = string.IsNullOrWhiteSpace(deploymentName)
            ? this.DefaultDeploymentName
            : deploymentName;

        if (customKernel is null)
        {
            var builder = Kernel.CreateBuilder();
            this._kernel = builder.AddAzureOpenAIChatCompletion(
                deploymentName: chosenDeployment,
                endpoint: azureOpenAIOptions!.Endpoint,
                apiKey: azureOpenAIOptions.ApiKey)
                .Build();
        }
        else
        {
            this._kernel = customKernel;
        }
    }

    /// <summary>
    /// Determines if the provided model identifier corresponds to a reasoning model.
    /// Adjust the logic as needed for your specific model identifiers.
    /// </summary>
    /// <param name="model">The model identifier to check.</param>
    /// <returns>True if it is a reasoning model; otherwise, false.</returns>
    private bool IsReasoningModel(string model)
    {
        // Example logic: treat "o1" and "o3-mini" as reasoning models.
        return model.Equals("o1", StringComparison.OrdinalIgnoreCase) ||
               model.Equals("o3-mini", StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Creates and returns a ChatCompletionAgent with appropriate execution settings.
    /// </summary>
    /// <returns>A configured ChatCompletionAgent.</returns>
    public ChatCompletionAgent CreateAgent()
    {
        // Initialize the prompt execution settings.
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,
        };

        // If the deployment model supports reasoning, add the reasoning effort level.
        if (this.IsReasoningModel(this.DefaultDeploymentName))
        {
            executionSettings.ReasoningEffort = this._reasoningEffort;
        }

        return new ChatCompletionAgent
        {
            Name = this.AgentName,
            Instructions = this.AgentPrompt,
            Kernel = this._kernel,
            Arguments = new KernelArguments(executionSettings)
        };
    }
}
