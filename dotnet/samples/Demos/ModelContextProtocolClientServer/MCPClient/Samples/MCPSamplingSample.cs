// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ModelContextProtocol;
using ModelContextProtocol.Client;
using ModelContextProtocol.Protocol.Types;

namespace MCPClient.Samples;

/// <summary>
/// Demonstrates how to use the Model Context Protocol (MCP) sampling with the Semantic Kernel.
/// </summary>
internal sealed class MCPSamplingSample : BaseSample
{
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
    public static async Task RunAsync()
    {
        Console.WriteLine($"Running the {nameof(MCPSamplingSample)} sample.");

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
}
