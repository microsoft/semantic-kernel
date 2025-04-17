// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Transport;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient;

internal sealed class Program
{
    public static async Task Main(string[] args)
    {
        await UseMCPToolsAsync();

        await UseMCPPromptAsync();

        await UseMCPResourcesAsync();

        await UseMCPResourceTemplatesAsync();

        await UseMCPSamplingAsync();

        await UseChatCompletionAgentWithMCPToolsAsync();

        await UseAzureAIAgentWithMCPToolsAsync();
    }

    /// <summary>
    /// Demonstrates how to use the MCP resources with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of resources provided by the MCP server.
    /// 3. Retrieves the `image://cat.jpg` resource content from the MCP server.
    /// 4. Adds the image to the chat history and prompts the AI model to describe the content of the image.
    /// </summary>
    private static async Task UseMCPResourcesAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPResourcesAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve list of resources provided by the MCP server and display them
        IList<Resource> resources = await mcpClient.ListResourcesAsync();
        DisplayResources(resources);

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        // Retrieve the `image://cat.jpg` resource from the MCP server
        ReadResourceResult resource = await mcpClient.ReadResourceAsync("image://cat.jpg");

        // Add the resource to the chat history and prompt the AI model to describe the content of the image
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage(resource.ToChatMessageContentItemCollection());
        chatHistory.AddUserMessage("Describe the content of the image?");

        // Execute a prompt using the MCP resource and prompt added to the chat history
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The image features a fluffy cat sitting in a lush, colorful garden.
        // The garden is filled with various flowers and plants, creating a vibrant and serene atmosphere...
    }

    /// <summary>
    /// Demonstrates how to use the MCP resource templates with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of resource templates provided by the MCP server.
    /// 3. Reads relevant to the prompt records from the `vectorStore://records/{prompt}` MCP resource template.
    /// 4. Adds the records to the chat history and prompts the AI model to explain what SK is.
    /// </summary>
    private static async Task UseMCPResourceTemplatesAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPResourceTemplatesAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve list of resource templates provided by the MCP server and display them
        IList<ResourceTemplate> resourceTemplates = await mcpClient.ListResourceTemplatesAsync();
        DisplayResourceTemplates(resourceTemplates);

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        string prompt = "What is the Semantic Kernel?";

        // Retrieve relevant to the prompt records via MCP resource template
        ReadResourceResult resource = await mcpClient.ReadResourceAsync($"vectorStore://records/{prompt}");

        // Add the resource content/records to the chat history and prompt the AI model to explain what SK is
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage(resource.ToChatMessageContentItemCollection());
        chatHistory.AddUserMessage(prompt);

        // Execute a prompt using the MCP resource and prompt added to the chat history
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The Semantic Kernel (SK) is a lightweight software development kit (SDK) designed for use in .NET applications.
        // It acts as an orchestrator that facilitates interaction between AI models and available plugins, enabling them to work together to produce desired outputs.
    }

    /// <summary>
    /// Demonstrates how to use the MCP tools with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 4. Sends the prompt to AI model together with the MCP tools represented as Kernel functions.
    /// 5. The AI model calls DateTimeUtils-GetCurrentDateTimeInUtc function to get the current date time in UTC required as an argument for the next function.
    /// 6. The AI model calls WeatherUtils-GetWeatherForCity function with the current date time and the `Boston` arguments extracted from the prompt to get the weather information.
    /// 7. Having received the weather information from the function call, the AI model returns the answer to the prompt.
    /// </summary>
    private static async Task UseMCPToolsAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPToolsAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list provided by the MCP server
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        DisplayTools(tools);

        // Create a kernel and register the MCP tools
        Kernel kernel = CreateKernelWithChatCompletionService();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        string prompt = "What is the likely color of the sky in Boston today?";
        Console.WriteLine(prompt);

        // Execute a prompt using the MCP tools. The AI model will automatically call the appropriate MCP tools to answer the prompt.
        FunctionResult result = await kernel.InvokePromptAsync(prompt, new(executionSettings));

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: The likely color of the sky in Boston today is gray, as it is currently rainy.
    }

    /// <summary>
    /// Demonstrates how to use the MCP prompt with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of prompts provided by the MCP server.
    /// 3. Gets the current weather for Boston and Sydney using the `GetCurrentWeatherForCity` prompt.
    /// 4. Adds the MCP server prompts to the chat history and prompts the AI model to compare the weather in the two cities and suggest the best place to go for a walk.
    /// 5. After receiving and processing the weather data for both cities and the prompt, the AI model returns an answer.
    /// </summary>
    private static async Task UseMCPPromptAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPPromptAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list of prompts provided by the MCP server
        IList<McpClientPrompt> prompts = await mcpClient.ListPromptsAsync();
        DisplayPrompts(prompts);

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Get weather for Boston using the `GetCurrentWeatherForCity` prompt from the MCP server
        GetPromptResult bostonWeatherPrompt = await mcpClient.GetPromptAsync("GetCurrentWeatherForCity", new Dictionary<string, object?>() { ["city"] = "Boston", ["time"] = DateTime.UtcNow.ToString() });

        // Get weather for Sydney using the `GetCurrentWeatherForCity` prompt from the MCP server
        GetPromptResult sydneyWeatherPrompt = await mcpClient.GetPromptAsync("GetCurrentWeatherForCity", new Dictionary<string, object?>() { ["city"] = "Sydney", ["time"] = DateTime.UtcNow.ToString() });

        // Add the prompts to the chat history
        ChatHistory chatHistory = [];
        chatHistory.AddRange(bostonWeatherPrompt.ToChatMessageContents());
        chatHistory.AddRange(sydneyWeatherPrompt.ToChatMessageContents());
        chatHistory.AddUserMessage("Compare the weather in the two cities and suggest the best place to go for a walk.");

        // Execute a prompt using the MCP tools and prompt
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, kernel: kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is: Given these conditions, Sydney would be the better choice for a pleasant walk, as the sunny and warm weather is ideal for outdoor activities.
        // The rain in Boston could make walking less enjoyable and potentially inconvenient.
    }

    /// <summary>
    /// Demonstrates how to use the MCP sampling with the Semantic Kernel.
    /// The code in this method:
    /// 1. Creates an MCP client and register the sampling request handler.
    /// 2. Retrieves the list of tools provided by the MCP server and registers them as Kernel functions.
    /// 3. Prompts the AI model to create a schedule based on the latest unread emails in the mailbox.
    /// 4. The AI model calls the `MailboxUtils-SummarizeUnreadEmails` function to summarize the unread emails.
    /// 5. The `MailboxUtils-SummarizeUnreadEmails` function creates a few sample emails with attachments and
    ///    sends a sampling request to the client to summarize them:
    ///    5.1. The client receive sampling request from server and invokes the sampling request handler.
    ///    5.2. SK intercepts the sampling request invocation via `HumanInTheLoopFilter` filter to enable human-in-the-loop processing.
    ///    5.3. The `HumanInTheLoopFilter` allows invocation of the sampling request handler.
    ///    5.5. The sampling request handler sends the sampling request to the AI model to summarize the emails.
    ///    5.6. The AI model processes the request and returns the summary to the handler which sends it back to the server.
    ///    5.7. The `MailboxUtils-SummarizeUnreadEmails` function receives the result and returns it to the AI model.
    /// 7. Having received the summary, the AI model creates a schedule based on the unread emails.
    /// </summary>
    private static async Task UseMCPSamplingAsync()
    {
        Console.WriteLine($"Running the {nameof(UseMCPSamplingAsync)} sample.");

        // Create a kernel
        Kernel kernel = CreateKernelWithChatCompletionService();

        // Register the human-in-the-loop filter that intercepts function calls allowing users to review and approve or reject them
        kernel.FunctionInvocationFilters.Add(new HumanInTheLoopFilter());

        // Create an MCP client with a custom sampling request handler
        await using IMcpClient mcpClient = await CreateMcpClientAsync(kernel, SamplingRequestHandlerAsync);

        // Import MCP tools as Kernel functions so AI model can call them
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            Temperature = 0,
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        // Execute a prompt
        string prompt = "Create a schedule for me based on the latest unread emails in my inbox.";
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(prompt, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine();

        // The expected output is:
        // ### Today
        // - **Review Sales Report:**
        //   - **Task:** Provide feedback on the Carretera Sales Report for January to June 2014.
        //   - **Deadline:** End of the day.
        //   - **Details:** Check the attached spreadsheet for sales data.
        //
        // ### Tomorrow
        // - **Update Employee Information:**
        //   - **Task:** Update the list of employee birthdays and positions.
        //   - **Deadline:** By the end of the day.
        //   - **Details:** Refer to the attached table for employee details.
        //
        // ### Saturday
        // - **Attend BBQ:**
        //   - **Event:** BBQ Invitation
        //   - **Details:** Join the BBQ as mentioned in the sales report email.
        //
        // ### Sunday
        // - **Join Hike:**
        //   - **Event:** Hiking Invitation
        //   - **Details:** Participate in the hike as mentioned in the HR email.
    }

    /// <summary>
    /// Demonstrates how to use <see cref="ChatCompletionAgent"/> with MCP tools represented as Kernel functions.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 4. Defines chat completion agent with instructions, name, kernel, and arguments.
    /// 5. Invokes the agent with a prompt.
    /// 6. The agent sends the prompt to the AI model, together with the MCP tools represented as Kernel functions.
    /// 7. The AI model calls DateTimeUtils-GetCurrentDateTimeInUtc function to get the current date time in UTC required as an argument for the next function.
    /// 8. The AI model calls WeatherUtils-GetWeatherForCity function with the current date time and the `Boston` arguments extracted from the prompt to get the weather information.
    /// 9. Having received the weather information from the function call, the AI model returns the answer to the agent and the agent returns the answer to the user.
    /// </summary>
    private static async Task UseChatCompletionAgentWithMCPToolsAsync()
    {
        Console.WriteLine($"Running the {nameof(UseChatCompletionAgentWithMCPToolsAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list provided by the MCP server
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        DisplayTools(tools);

        // Create a kernel and register the MCP tools as kernel functions
        Kernel kernel = CreateKernelWithChatCompletionService();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Enable automatic function calling
        OpenAIPromptExecutionSettings executionSettings = new()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new() { RetainArgumentTypes = true })
        };

        string prompt = "What is the likely color of the sky in Boston today?";
        Console.WriteLine(prompt);

        // Define the agent
        ChatCompletionAgent agent = new()
        {
            Instructions = "Answer questions about the weather.",
            Name = "WeatherAgent",
            Kernel = kernel,
            Arguments = new KernelArguments(executionSettings),
        };

        // Invokes agent with a prompt
        ChatMessageContent response = await agent.InvokeAsync(prompt).FirstAsync();

        Console.WriteLine(response);
        Console.WriteLine();

        // The expected output is: The sky in Boston today is likely gray due to rainy weather.
    }

    /// <summary>
    /// Demonstrates how to use <see cref="AzureAIAgent"/> with MCP tools represented as Kernel functions.
    /// The code in this method:
    /// 1. Creates an MCP client.
    /// 2. Retrieves the list of tools provided by the MCP server.
    /// 3. Creates a kernel and registers the MCP tools as Kernel functions.
    /// 4. Defines Azure AI agent with instructions, name, kernel, and arguments.
    /// 5. Invokes the agent with a prompt.
    /// 6. The agent sends the prompt to the AI model, together with the MCP tools represented as Kernel functions.
    /// 7. The AI model calls DateTimeUtils-GetCurrentDateTimeInUtc function to get the current date time in UTC required as an argument for the next function.
    /// 8. The AI model calls WeatherUtils-GetWeatherForCity function with the current date time and the `Boston` arguments extracted from the prompt to get the weather information.
    /// 9. Having received the weather information from the function call, the AI model returns the answer to the agent and the agent returns the answer to the user.
    /// </summary>
    private static async Task UseAzureAIAgentWithMCPToolsAsync()
    {
        Console.WriteLine($"Running the {nameof(UseAzureAIAgentWithMCPToolsAsync)} sample.");

        // Create an MCP client
        await using IMcpClient mcpClient = await CreateMcpClientAsync();

        // Retrieve and display the list provided by the MCP server
        IList<McpClientTool> tools = await mcpClient.ListToolsAsync();
        DisplayTools(tools);

        // Create a kernel and register the MCP tools as Kernel functions
        Kernel kernel = new();
        kernel.Plugins.AddFromFunctions("Tools", tools.Select(aiFunction => aiFunction.AsKernelFunction()));

        // Define the agent using the kernel with registered MCP tools
        AzureAIAgent agent = await CreateAzureAIAgentAsync(
            name: "WeatherAgent",
            instructions: "Answer questions about the weather.",
            kernel: kernel
        );

        // Invokes agent with a prompt
        string prompt = "What is the likely color of the sky in Boston today?";
        Console.WriteLine(prompt);

        AgentResponseItem<ChatMessageContent> response = await agent.InvokeAsync(message: prompt).FirstAsync();
        Console.WriteLine(response.Message);
        Console.WriteLine();

        // The expected output is: Today in Boston, the weather is 61°F and rainy. Due to the rain, the likely color of the sky will be gray.

        // Delete the agent thread after use
        await response!.Thread.DeleteAsync();

        // Delete the agent after use
        await agent.Client.DeleteAgentAsync(agent.Id);
    }

    /// <summary>
    /// Creates an instance of <see cref="Kernel"/> with the OpenAI chat completion service registered.
    /// </summary>
    /// <returns>An instance of <see cref="Kernel"/>.</returns>
    private static Kernel CreateKernelWithChatCompletionService()
    {
        // Load and validate configuration
        IConfigurationRoot config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        if (config["OpenAI:ApiKey"] is not { } apiKey)
        {
            const string Message = "Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.";
            Console.Error.WriteLine(Message);
            throw new InvalidOperationException(Message);
        }

        string modelId = config["OpenAI:ChatModelId"] ?? "gpt-4o-mini";

        // Create kernel
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddOpenAIChatCompletion(serviceId: "openai", modelId: modelId, apiKey: apiKey);

        return kernelBuilder.Build();
    }

    /// <summary>
    /// Creates an MCP client and connects it to the MCPServer server.
    /// </summary>
    /// <param name="kernel">Optional kernel instance to use for the MCP client.</param>
    /// <param name="samplingRequestHandler">Optional handler for MCP sampling requests.</param>
    /// <returns>An instance of <see cref="IMcpClient"/>.</returns>
    private static Task<IMcpClient> CreateMcpClientAsync(
        Kernel? kernel = null,
        Func<Kernel, CreateMessageRequestParams?, IProgress<ProgressNotificationValue>, CancellationToken, Task<CreateMessageResult>>? samplingRequestHandler = null)
    {
        KernelFunction? skSamplingHandler = null;

        // Create and return the MCP client
        return McpClientFactory.CreateAsync(
            clientTransport: new StdioClientTransport(new StdioClientTransportOptions
            {
                Name = "MCPServer",
                Command = GetMCPServerPath(), // Path to the MCPServer executable
            }),
            clientOptions: samplingRequestHandler != null ? new McpClientOptions()
            {
                Capabilities = new ClientCapabilities
                {
                    Sampling = new SamplingCapability
                    {
                        SamplingHandler = InvokeHandlerAsync
                    },
                },
            } : null
         );

        async ValueTask<CreateMessageResult> InvokeHandlerAsync(CreateMessageRequestParams? request, IProgress<ProgressNotificationValue> progress, CancellationToken cancellationToken)
        {
            if (request is null)
            {
                throw new ArgumentNullException(nameof(request));
            }

            skSamplingHandler ??= KernelFunctionFactory.CreateFromMethod(
                (CreateMessageRequestParams? request, IProgress<ProgressNotificationValue> progress, CancellationToken ct) =>
                {
                    return samplingRequestHandler(kernel!, request, progress, ct);
                },
                "MCPSamplingHandler"
            );

            // The argument names must match the parameter names of the delegate the SK Function is created from
            KernelArguments kernelArguments = new()
            {
                ["request"] = request,
                ["progress"] = progress
            };

            FunctionResult functionResult = await skSamplingHandler.InvokeAsync(kernel!, kernelArguments, cancellationToken);

            return functionResult.GetValue<CreateMessageResult>()!;
        }
    }

    /// <summary>
    /// Handles sampling requests from the MCP client.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="request">The sampling request.</param>
    /// <param name="progress">The progress notification.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the sampling request.</returns>
    private static async Task<CreateMessageResult> SamplingRequestHandlerAsync(Kernel kernel, CreateMessageRequestParams? request, IProgress<ProgressNotificationValue> progress, CancellationToken cancellationToken)
    {
        if (request is null)
        {
            throw new ArgumentNullException(nameof(request));
        }

        // Map the MCP sampling request to the Semantic Kernel prompt execution settings
        OpenAIPromptExecutionSettings promptExecutionSettings = new()
        {
            Temperature = request.Temperature,
            MaxTokens = request.MaxTokens,
            StopSequences = request.StopSequences?.ToList(),
        };

        // Create a chat history from the MCP sampling request
        ChatHistory chatHistory = [];
        if (!string.IsNullOrEmpty(request.SystemPrompt))
        {
            chatHistory.AddSystemMessage(request.SystemPrompt);
        }
        chatHistory.AddRange(request.Messages.ToChatMessageContents());

        // Prompt the AI model to generate a response
        IChatCompletionService chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        ChatMessageContent result = await chatCompletion.GetChatMessageContentAsync(chatHistory, promptExecutionSettings, cancellationToken: cancellationToken);

        return result.ToCreateMessageResult();
    }

    private static async Task<AzureAIAgent> CreateAzureAIAgentAsync(Kernel kernel, string name, string instructions)
    {
        // Load and validate configuration
        IConfigurationRoot config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        if (config["AzureAI:ConnectionString"] is not { } connectionString)
        {
            const string Message = "Please provide a valid `AzureAI:ConnectionString` secret to run this sample. See the associated README.md for more details.";
            Console.Error.WriteLine(Message);
            throw new InvalidOperationException(Message);
        }

        string modelId = config["AzureAI:ChatModelId"] ?? "gpt-4o-mini";

        // Create the Azure AI Agent
        AIProjectClient projectClient = AzureAIAgent.CreateAzureAIClient(connectionString, new AzureCliCredential());

        AgentsClient agentsClient = projectClient.GetAgentsClient();

        Azure.AI.Projects.Agent agent = await agentsClient.CreateAgentAsync(modelId, name, null, instructions);

        return new AzureAIAgent(agent, agentsClient)
        {
            Kernel = kernel
        };
    }

    /// <summary>
    /// Returns the path to the MCPServer server executable.
    /// </summary>
    /// <returns>The path to the MCPServer server executable.</returns>
    private static string GetMCPServerPath()
    {
        // Determine the configuration (Debug or Release)  
        string configuration;

#if DEBUG
        configuration = "Debug";
#else
        configuration = "Release";
#endif

        return Path.Combine("..", "..", "..", "..", "MCPServer", "bin", configuration, "net8.0", "MCPServer.exe");
    }

    /// <summary>
    /// Displays the list of available MCP tools.
    /// </summary>
    /// <param name="tools">The list of the tools to display.</param>
    private static void DisplayTools(IList<McpClientTool> tools)
    {
        Console.WriteLine("Available MCP tools:");
        foreach (var tool in tools)
        {
            Console.WriteLine($"- Name: {tool.Name}, Description: {tool.Description}");
        }
        Console.WriteLine();
    }

    /// <summary>
    /// Displays the list of available MCP prompts.
    /// </summary>
    /// <param name="prompts">The list of the prompts to display.</param>
    private static void DisplayPrompts(IList<McpClientPrompt> prompts)
    {
        Console.WriteLine("Available MCP prompts:");
        foreach (var prompt in prompts)
        {
            Console.WriteLine($"- Name: {prompt.Name}, Description: {prompt.Description}");
        }
        Console.WriteLine();
    }

    private static void DisplayResources(IList<Resource> resources)
    {
        Console.WriteLine("Available MCP resources:");
        foreach (var resource in resources)
        {
            Console.WriteLine($"- Name: {resource.Name}, Uri: {resource.Uri}, Description: {resource.Description}");
        }
        Console.WriteLine();
    }

    private static void DisplayResourceTemplates(IList<ResourceTemplate> resourceTemplates)
    {
        Console.WriteLine("Available MCP resource templates:");
        foreach (var template in resourceTemplates)
        {
            Console.WriteLine($"- Name: {template.Name}, Description: {template.Description}");
        }
        Console.WriteLine();
    }
}
