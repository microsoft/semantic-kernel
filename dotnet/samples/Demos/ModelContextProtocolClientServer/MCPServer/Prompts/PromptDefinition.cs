// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Prompts;

/// <summary>
/// Represents a prompt definition.
/// </summary>
public sealed class PromptDefinition
{
    /// <summary>
    /// Gets or sets the prompt.
    /// </summary>
    public required Prompt Prompt { get; init; }

    /// <summary>
    /// Gets or sets the handler for the prompt.
    /// </summary>
    public required Func<RequestContext<GetPromptRequestParams>, CancellationToken, Task<GetPromptResult>> Handler { get; init; }

    /// <summary>
    /// Gets this prompt definition.
    /// </summary>
    /// <param name="jsonPrompt">The JSON prompt template.</param>
    /// <param name="kernel">An instance of the kernel to render the prompt.
    /// If not provided, an instance registered in DI container will be used.
    /// </param>
    /// <returns>The prompt definition.</returns>
    public static PromptDefinition Create(string jsonPrompt, Kernel? kernel = null)
    {
        PromptTemplateConfig promptTemplateConfig = PromptTemplateConfig.FromJson(jsonPrompt);

        IPromptTemplate promptTemplate = new HandlebarsPromptTemplateFactory().Create(promptTemplateConfig);

        return new PromptDefinition()
        {
            Prompt = GetPrompt(promptTemplateConfig),
            Handler = (context, cancellationToken) =>
            {
                return GetPromptHandlerAsync(context, promptTemplateConfig, promptTemplate, kernel, cancellationToken);
            }
        };
    }

    /// <summary>
    /// Creates an MCP prompt from SK prompt template.
    /// </summary>
    /// <param name="promptTemplateConfig">The prompt template configuration.</param>
    /// <returns>The MCP prompt.</returns>
    private static Prompt GetPrompt(PromptTemplateConfig promptTemplateConfig)
    {
        // Create the MCP prompt arguments
        List<PromptArgument>? arguments = null;

        foreach (var inputVariable in promptTemplateConfig.InputVariables)
        {
            (arguments ??= []).Add(new()
            {
                Name = inputVariable.Name,
                Description = inputVariable.Description,
                Required = inputVariable.IsRequired
            });
        }

        // Create the MCP prompt
        return new Prompt
        {
            Name = promptTemplateConfig.Name!,
            Description = promptTemplateConfig.Description,
            Arguments = arguments
        };
    }

    /// <summary>
    /// Handles the prompt request by rendering the prompt.
    /// </summary>
    /// <param name="context">The MCP request context.</param>
    /// <param name="promptTemplateConfig">The prompt template configuration.</param>
    /// <param name="promptTemplate">The prompt template.</param>
    /// <param name="kernel">The kernel to render the prompt.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The prompt.</returns>
    private static async Task<GetPromptResult> GetPromptHandlerAsync(RequestContext<GetPromptRequestParams> context, PromptTemplateConfig promptTemplateConfig, IPromptTemplate promptTemplate, Kernel? kernel, CancellationToken cancellationToken)
    {
        // Use either explicitly provided kernel or the one registered in DI container
        kernel ??= context.Server.Services?.GetRequiredService<Kernel>() ?? throw new InvalidOperationException("Kernel is not available.");

        // Render the prompt
        string renderedPrompt = await promptTemplate.RenderAsync(
            kernel: kernel,
            arguments: context.Params?.Arguments is { } args ? new KernelArguments(args.ToDictionary(kvp => kvp.Key, kvp => (object?)kvp.Value)) : null,
            cancellationToken: cancellationToken);

        // Create prompt result
        return new GetPromptResult()
        {
            Description = promptTemplateConfig.Description,
            Messages =
            [
                new PromptMessage()
                {
                    Content = new Content()
                    {
                        Type = "text",
                        Text = renderedPrompt
                    },
                    Role = Role.Assistant
                }
            ]
        };
    }
}
