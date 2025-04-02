// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Prompts;

/// <summary>
/// Represents the GetCurrentWeatherForCity prompt.
/// </summary>
internal static class GetCurrentWeatherForCityPrompt
{
    /// <summary>
    /// The SK handlebars prompt template is embedded in the class for the convenience and simplicity of the demo.
    /// For non-demo scenarios, the JSON prompt template can be stored in a separate file so it can be versioned and updated independently.
    /// The GetCurrentWeatherForCityPrompt class itself can be generalized to use with any prompt template and accept the template name as a parameter.
    /// </summary>
    private static readonly PromptTemplateConfig s_promptTemplateConfig = PromptTemplateConfig.FromJson("""
    {
        "name": "GetCurrentWeatherForCity",
        "description": "Provides current weather information for a specified city.",
        "template_format": "handlebars",
        "template": "What is the weather in {{city}} as of {{DateTimeUtils-GetCurrentDateTimeInUtc}}?",
        "input_variables": [
            {
                "name": "city",
                "description": "The city for which to get the weather.",
                "is_required": true
            }
        ]
    }
    """);

    private static readonly IPromptTemplate s_promptTemplate = new HandlebarsPromptTemplateFactory().Create(s_promptTemplateConfig);

    /// <summary>
    /// Gets this prompt definition.
    /// </summary>
    /// <param name="kernel">An instance of the kernel to render the prompt.</param>
    /// <returns>The prompt definition.</returns>
    public static PromptDefinition GetDefinition(Kernel kernel)
    {
        return new()
        {
            Prompt = GetPrompt(),
            Handler = (context, cancellationToken) => GetPromptHandlerAsync(context, kernel, cancellationToken)
        };
    }

    /// <summary>
    /// Creates an MCP prompt from SK prompt template.
    /// </summary>
    /// <returns>The MCP prompt.</returns>
    private static Prompt GetPrompt()
    {
        // Create the MCP prompt arguments
        List<PromptArgument>? arguments = null;

        foreach (var inputVariable in s_promptTemplateConfig.InputVariables)
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
            Name = s_promptTemplateConfig.Name!,
            Description = s_promptTemplateConfig.Description,
            Arguments = arguments
        };
    }

    /// <summary>
    /// Handles the prompt request by rendering the prompt.
    /// </summary>
    /// <param name="context">The prompt request context.</param>
    /// <param name="kernel">The kernel to render the prompt.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The prompt.</returns>
    private static async Task<GetPromptResult> GetPromptHandlerAsync(RequestContext<GetPromptRequestParams> context, Kernel kernel, CancellationToken cancellationToken)
    {
        // Render the prompt
        string renderedPrompt = await s_promptTemplate.RenderAsync(
            kernel: kernel,
            arguments: context.Params?.Arguments is { } args ? new KernelArguments(args!) : null,
            cancellationToken: cancellationToken);

        // Create prompt result
        return new GetPromptResult()
        {
            Description = s_promptTemplateConfig.Description,
            Messages =
            [
                new PromptMessage()
                {
                    Content = new Content()
                    {
                        Type = "text",
                        Text = renderedPrompt
                    },
                    Role = Role.User
                }
            ]
        };
    }
}
