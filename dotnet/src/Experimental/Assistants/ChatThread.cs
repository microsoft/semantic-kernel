// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents an OpenAI assistant chat thread
/// </summary>
public sealed class ChatThread : IChatThread
{
    /// <inheritdoc/>
    public string Id { get; private set; }

    private readonly string _apiKey;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Constructor
    /// </summary>
    internal ChatThread(string id, string apiKey, HttpClient httpClient)
    {
        this.Id = id;
        this._apiKey = apiKey;
        this._httpClient = httpClient;
    }

    /// <inheritdoc/>
    public Task AddUserMessageAsync(string message, CancellationToken cancellationToken = default)
    {
        return
            this.AddMessageAsync(
                new ChatMessage(message),
                cancellationToken);
    }

    /// <inheritdoc/>
    public async Task AddMessageAsync(ChatMessage message, CancellationToken cancellationToken = default)
    {
        await this._httpClient.CreateMessageAsync(this.Id, message, this._apiKey, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public /*async*/ Task InvokeAsync(string assistantId, CancellationToken cancellationToken = default)
    {
        //ThreadRunModel threadRunModel = await this.CreatRunAsync(assistantId).ConfigureAwait(false);

        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public async Task<ChatMessage?> GetMessageAsync(string messageId, CancellationToken cancellationToken = default)
    {
        var message =
            await this._httpClient.GetMessageAsync(this.Id, messageId, this._apiKey, cancellationToken).ConfigureAwait(false) ??
            throw new ArgumentException("Uknown messageId", nameof(messageId));

        return new ChatMessage(message.Content, message.Role);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<ChatMessage>> GetMessagesAsync(CancellationToken cancellationToken = default)
    {
        var messages = await this._httpClient.GetMessagesAsync(this.Id, this._apiKey, cancellationToken).ConfigureAwait(false);;

        return messages.Select(m => new ChatMessage(m.Content, m.Role));
    }

    /// <summary>
    /// The heart of the thread interface.
    /// </summary>
    //public async Task<FunctionResult> InvokeAsync(
    //    IKernel kernel,
    //    Dictionary<string, object?> variables,
    //    bool streaming = false,
    //    CancellationToken cancellationToken = default
    //)
    //{
    //    // TODO: implement streaming so that we can pass messages back as they are created
    //    if (streaming)
    //    {
    //        throw new NotImplementedException();
    //    }

    //    if (kernel is Assistant assistantKernel)
    //    {
    //        // Create a run on the thread
    //        ThreadRunModel threadRunModel = await this.CreateThreadRunAsync(assistantKernel).ConfigureAwait(false);
    //        ThreadRunStepListModel threadRunSteps;

    //        // Poll the run until it is complete
    //        while (threadRunModel.Status == "queued" || threadRunModel.Status == "in_progress" || threadRunModel.Status == "requires_action")
    //        {
    //            // Add a delay
    //            await Task.Delay(300, cancellationToken).ConfigureAwait(false);

    //            // If the run requires action, then we need to run the tool calls
    //            if (threadRunModel.Status == "requires_action")
    //            {
    //                // Get the steps
    //                threadRunSteps = await this.GetThreadRunStepsAsync(threadRunModel.Id).ConfigureAwait(false);

    //                // TODO: make this more efficient through parallelization
    //                foreach (ThreadRunStepModel threadRunStep in threadRunSteps.Data)
    //                {
    //                    // Retrieve all of the steps that require action
    //                    if (threadRunStep.Status == "in_progress" && threadRunStep.StepDetails.Type == "tool_calls")
    //                    {
    //                        foreach (var toolCall in threadRunStep.StepDetails.ToolCalls)
    //                        {
    //                            // Run function
    //                            //var result = await this.InvokeFunctionCallAsync(kernel, toolCall.Function.Name, toolCall.Function.Arguments).ConfigureAwait(false);

    //                            //// Update the thread run
    //                            //threadRunModel = await this.SubmitToolOutputsToRunAsync(threadRunModel.Id, toolCall.Id, result).ConfigureAwait(false);
    //                        }
    //                    }
    //                }
    //            }
    //            else
    //            {
    //                threadRunModel = await this.GetThreadRunAsync(threadRunModel.Id).ConfigureAwait(false);
    //            }
    //        }

    //        // Check for errors
    //        if (threadRunModel.Status == "failed")
    //        {
    //            return new FunctionResult(this.Id, "Ask", kernel.CreateNewContext(), new List<ChatMessage>()
    //            {
    //                { new ChatMessage(threadRunModel.LastError.Message) }
    //            });
    //        }

    //        // Get the steps
    //        threadRunSteps = await this.GetThreadRunStepsAsync(threadRunModel.Id).ConfigureAwait(false);

    //        // Check step details
    //        var messages = new List<ChatMessage>();
    //        foreach (ThreadRunStepModel threadRunStep in threadRunSteps.Data)
    //        {
    //            if (threadRunStep.StepDetails.Type == "message_creation")
    //            {
    //                // Get message Id
    //                var messageId = threadRunStep.StepDetails.MessageCreation.MessageId;
    //                ChatMessage message = await this.GetMessageAsync(messageId).ConfigureAwait(false);
    //                messages.Add(message);
    //            }
    //        }

    //        return new FunctionResult(this.Id, "$$$", kernel.CreateNewContext(), messages);
    //    }

    //    throw new NotImplementedException();
    //}

    //private async Task<string> InvokeFunctionCallAsync(IKernel kernel, string name, string arguments)
    //{
    //    // split name
    //    string[] nameParts = name.Split('-');

    //    // get function from kernel
    //    var function = kernel.Functions.GetFunction(nameParts[0], nameParts[1]);
    //    // TODO: change back to Dictionary<string, object>
    //    Dictionary<string, object> variables = JsonSerializer.Deserialize<Dictionary<string, object>>(arguments)!;

    //    var results = await kernel.RunAsync(function /*, variables*/).ConfigureAwait(false);

    //    return results.GetValue<string>()!;
    //}

    //private async Task<ThreadRunModel> SubmitToolOutputsToRunAsync(string runId, string toolCallId, string output)
    //{
    //    var requestData = new
    //    {
    //        tool_outputs = new[] {
    //            new {
    //                tool_call_id = toolCallId,
    //                output = output
    //            }
    //        }
    //    };

    //    string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs/" + runId + "/submit_tool_outputs";
    //    using var httpRequestMessage = HttpRequest.CreatePostRequest(url, requestData);
    //    httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
    //    httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

    //    var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);

    //    string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
    //    return JsonSerializer.Deserialize<ThreadRunModel>(responseBody)!;
    //}

    private async Task<ThreadRunModel> CreateThreadRunAsync(string assistantId)
    {
        var tools = new List<object>();

        //foreach (FunctionView functionView in kernel.GetFunctionViews())
        //{
        //    var OpenAIFunction = functionView.ToOpenAIFunction().ToFunctionDefinition();
        //    var requiredParams = new List<string>();
        //    var paramProperties = new Dictionary<string, object>();

        //    foreach (var param in functionView.Parameters)
        //    {
        //        paramProperties.Add(
        //            param.Name,
        //            new
        //            {
        //                type = param.Type.Value.Name.ToLowerInvariant(),
        //                description = param.Description,
        //            });

        //        if (param.IsRequired ?? false)
        //        {
        //            requiredParams.Add(param.Name);
        //        }
        //    }

        //    tools.Add(new
        //    {
        //        type = "function",
        //        function = new
        //        {
        //            name = OpenAIFunction.Name,
        //            description = OpenAIFunction.Description,
        //            parameters = new
        //            {
        //                type = "object",
        //                properties = paramProperties,
        //                required = requiredParams,
        //            }
        //        }
        //    });
        //}

        var requestData = new
        {
            assistant_id = assistantId,
            //instructions = kernel.Instructions, $$$
            tools = tools
        };

        string requestDataJson = JsonSerializer.Serialize(requestData);

        string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs";
        using var httpRequestMessage = HttpRequest.CreatePostRequest(url, requestData);
        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

        var response = await this._httpClient.SendAsync(httpRequestMessage).ConfigureAwait(false);

        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<ThreadRunModel>(responseBody)!;
    }

    private async Task<ThreadRunModel> GetThreadRunAsync(string runId)
    {
        string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs/" + runId;
        using var httpRequestMessage2 = HttpRequest.CreateGetRequest(url);

        httpRequestMessage2.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage2.Headers.Add("OpenAI-Beta", "assistants=v1");

        var response = await this._httpClient.SendAsync(httpRequestMessage2).ConfigureAwait(false);

        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<ThreadRunModel>(responseBody)!;
    }

    private async Task<ThreadRunStepListModel> GetThreadRunStepsAsync(string runId)
    {
        string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs/" + runId + "/steps";
        using var httpRequestMessage = HttpRequest.CreateGetRequest(url);

        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

        var response = await this._httpClient.SendAsync(httpRequestMessage).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<ThreadRunStepListModel>(responseBody)!;
    }

    //private OpenAIFunction ToOpenAIFunction(FunctionView functionView)
    //{
    //    var openAIParams = new List<OpenAIFunctionParameter>();
    //    foreach (ParameterView param in functionView.Parameters)
    //    {
    //        openAIParams.Add(new OpenAIFunctionParameter
    //        {
    //            Name = param.Name,
    //            Description = (param.Description ?? string.Empty)
    //                + (string.IsNullOrEmpty(param.DefaultValue) ? string.Empty : $" (default value: {param.DefaultValue})"),
    //            Type = param.Type?.Name.ToLower() ?? "string",
    //            IsRequired = param.IsRequired ?? false
    //        });
    //    }

    //    return new OpenAIFunction
    //    {
    //        FunctionName = this.Id,
    //        PluginName = "$$$",
    //        Description = this.Description,
    //        Parameters = openAIParams,
    //    };
    //}
}
