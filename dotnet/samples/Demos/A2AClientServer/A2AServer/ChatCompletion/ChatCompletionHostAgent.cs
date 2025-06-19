// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;

namespace A2A;

internal abstract class ChatCompletionHostAgent : A2AHostAgent
{
    internal ChatCompletionHostAgent(ILogger logger) : base(logger)
    {
        this._logger = logger;
    }

    /// <summary>
    /// The name of the agent;
    /// </summary>
    protected string Name { get; set; } = "ChatCompletionHostAgent";

    /// <summary>
    /// The instructions for the agent;
    /// </summary>
    protected string Instructions { get; set; } = string.Empty;

    /// <summary>
    /// Optional: The plugins associated with the agent.
    /// </summary>
    protected IEnumerable<KernelPlugin>? Plugins { get; set; }

    public void InitializeAgent(string modelId, string apiKey)
    {
        try
        {
            this._logger.LogInformation("Initializing ChatCompletionHostAgent with model {ModelId}", modelId);

            // Define the InvoiceAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            if (this.Plugins is not null)
            {
                foreach (var plugin in this.Plugins)
                {
                    builder.Plugins.Add(plugin);
                }
            }
            var kernel = builder.Build();

            this.Agent = new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = this.Name,
                Instructions = this.Instructions,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize ChatCompletionHostAgent");
            throw;
        }
    }

    #region private
    private readonly ILogger _logger;
    #endregion

}
