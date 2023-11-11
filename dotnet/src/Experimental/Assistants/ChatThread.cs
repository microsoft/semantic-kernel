// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents an OpenAI assistant chat thread
/// </summary>
public sealed class ChatThread : IChatThread
{
    /// <inheritdoc/>
    public string Id { get; set; }

    /// <inheritdoc/>
    public string Name { get { return this.Id; } }

    /// <inheritdoc/>
    public string PluginName { get; }

    /// <inheritdoc/>
    public string Description => throw new NotImplementedException();

    /// <inheritdoc/>
    public AIRequestSettings? RequestSettings => throw new NotImplementedException();

    /// <inheritdoc/>
    public string SkillName => throw new NotImplementedException();

    /// <inheritdoc/>
    public bool IsSemantic => throw new NotImplementedException();

    /// <inheritdoc/>
    public IEnumerable<AIRequestSettings> ModelSettings => throw new NotImplementedException();

    private readonly Assistant _primaryAssistant;

    private readonly string _apiKey;

    private readonly HttpClient _client = new();

    /// <summary>
    /// Constructor
    /// </summary>
    public ChatThread(string id, string apiKey, Assistant primaryAssistant)
    {
        this.PluginName = primaryAssistant.Name;
        this.Id = id;
        this._apiKey = apiKey;
        this._primaryAssistant = primaryAssistant;
    }

    /// <inheritdoc/>
    public Task AddUserMessageAsync(string message)
    {
        return
            this.AddMessageAsync(
                new ModelMessage(message));
    }

    /// <inheritdoc/>
    public async Task AddMessageAsync(ModelMessage message)
    {
        var requestData = new // $$$ MODEL
        {
            role = message.Role,
            content = message.Content.ToString()
        };

        var url = $"{BaseUrl}/{this.Id}/messages";

        using var httpRequestMessage = HttpRequest.CreatePostRequest(url, requestData);

        using var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);

        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<ModelMessage> RetrieveMessageAsync(string messageId)
    {
        var url = $"{BaseUrl}/{this.Id}/messages/"+messageId;
        using var httpRequestMessage = HttpRequest.CreateGetRequest(url);

        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

        using var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        ThreadMessageModel message = JsonSerializer.Deserialize<ThreadMessageModel>(responseBody);

        List<object> content = new();
        foreach(var item in message.Content)
        {
            content.Add(item.Text.Value);
        }

        return new ModelMessage(content, message.Role);
    }

    /// <summary>
    /// The heart of the thread interface.
    /// </summary>
    public async Task<FunctionResult> InvokeAsync(
        IKernel kernel,
        Dictionary<string, object?> variables,
        bool streaming = false,
        CancellationToken cancellationToken = default
    )
    {
        // TODO: implement streaming so that we can pass messages back as they are created
        if (streaming)
        {
            throw new NotImplementedException();
        }

        if (kernel is Assistant assistantKernel)
        {
            // Create a run on the thread
            ThreadRunModel threadRunModel = await this.CreateThreadRunAsync(assistantKernel).ConfigureAwait(false);
            ThreadRunStepListModel threadRunSteps;

            // Poll the run until it is complete
            while (threadRunModel.Status == "queued" || threadRunModel.Status == "in_progress" || threadRunModel.Status == "requires_action")
            {
                // Add a delay
                await Task.Delay(300, cancellationToken).ConfigureAwait(false);

                // If the run requires action, then we need to run the tool calls
                if (threadRunModel.Status == "requires_action")
                {
                    // Get the steps
                    threadRunSteps = await this.GetThreadRunStepsAsync(threadRunModel.Id).ConfigureAwait(false);

                    // TODO: make this more efficient through parallelization
                    foreach (ThreadRunStepModel threadRunStep in threadRunSteps.Data)
                    {
                        // Retrieve all of the steps that require action
                        if (threadRunStep.Status == "in_progress" && threadRunStep.StepDetails.Type == "tool_calls")
                        {
                            foreach (var toolCall in threadRunStep.StepDetails.ToolCalls)
                            {
                                // Run function
                                //var result = await this.InvokeFunctionCallAsync(kernel, toolCall.Function.Name, toolCall.Function.Arguments).ConfigureAwait(false);

                                //// Update the thread run
                                //threadRunModel = await this.SubmitToolOutputsToRunAsync(threadRunModel.Id, toolCall.Id, result).ConfigureAwait(false);
                            }
                        }
                    }
                }
                else
                {
                    threadRunModel = await this.GetThreadRunAsync(threadRunModel.Id).ConfigureAwait(false);
                }
            }

            // Check for errors
            if (threadRunModel.Status == "failed")
            {
                return new FunctionResult(this.Name, "Ask", kernel.CreateNewContext(), new List<ModelMessage>()
                {
                    { new ModelMessage(threadRunModel.LastError.Message) }
                });
            }

            // Get the steps
            threadRunSteps = await this.GetThreadRunStepsAsync(threadRunModel.Id).ConfigureAwait(false);

            // Check step details
            var messages = new List<ModelMessage>();
            foreach (ThreadRunStepModel threadRunStep in threadRunSteps.Data)
            {
                if (threadRunStep.StepDetails.Type == "message_creation")
                {
                    // Get message Id
                    var messageId = threadRunStep.StepDetails.MessageCreation.MessageId;
                    ModelMessage message = await this.RetrieveMessageAsync(messageId).ConfigureAwait(false);
                    messages.Add(message);
                }
            }

            return new FunctionResult(this.Name, this.PluginName, kernel.CreateNewContext(), messages);
        }

        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<Orchestration.FunctionResult> InvokeAsync(Orchestration.SKContext context, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<List<ModelMessage>> ListMessagesAsync()
    {
        throw new NotImplementedException();
    }

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

    private async Task<ThreadRunModel> CreateThreadRunAsync(Assistant kernel)
    {
        var tools = new List<object>();

        // Much of this code was copied from the existing function calling code
        // Ideally it can reuse the same code without having to duplicate it
        foreach (FunctionView functionView in kernel.GetFunctionViews())
        {
            var OpenAIFunction = functionView.ToOpenAIFunction().ToFunctionDefinition();
            var requiredParams = new List<string>();
            var paramProperties = new Dictionary<string, object>();

            foreach (var param in functionView.Parameters)
            {
                paramProperties.Add(
                    param.Name,
                    new
                    {
                        type = param.Type.Value.Name.ToLowerInvariant(),
                        description = param.Description,
                    });

                if (param.IsRequired ?? false)
                {
                    requiredParams.Add(param.Name);
                }
            }

            tools.Add(new
            {
                type = "function",
                function = new
                {
                    name = OpenAIFunction.Name,
                    description = OpenAIFunction.Description,
                    parameters = new
                    {
                        type = "object",
                        properties = paramProperties,
                        required = requiredParams,
                    }
                }
            });
        }

        var requestData = new
        {
            assistant_id = kernel.Id,
            instructions = kernel.Instructions,
            tools = tools
        };

        string requestDataJson = JsonSerializer.Serialize(requestData);

        string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs";
        using var httpRequestMessage = HttpRequest.CreatePostRequest(url, requestData);
        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

        var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);

        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<ThreadRunModel>(responseBody)!;
    }

    private async Task<ThreadRunModel> GetThreadRunAsync(string runId)
    {
        string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs/" + runId;
        using var httpRequestMessage2 = HttpRequest.CreateGetRequest(url);

        httpRequestMessage2.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage2.Headers.Add("OpenAI-Beta", "assistants=v1");

        var response = await this._client.SendAsync(httpRequestMessage2).ConfigureAwait(false);

        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<ThreadRunModel>(responseBody)!;
    }

    private async Task<ThreadRunStepListModel> GetThreadRunStepsAsync(string runId)
    {
        string url = "https://api.openai.com/v1/threads/" + this.Id + "/runs/" + runId + "/steps";
        using var httpRequestMessage = HttpRequest.CreateGetRequest(url);

        httpRequestMessage.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        httpRequestMessage.Headers.Add("OpenAI-Beta", "assistants=v1");

        var response = await this._client.SendAsync(httpRequestMessage).ConfigureAwait(false);
        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        return JsonSerializer.Deserialize<ThreadRunStepListModel>(responseBody)!;
    }

    private OpenAIFunction ToOpenAIFunction(FunctionView functionView)
    {
        var openAIParams = new List<OpenAIFunctionParameter>();
        foreach (ParameterView param in functionView.Parameters)
        {
            openAIParams.Add(new OpenAIFunctionParameter
            {
                Name = param.Name,
                Description = (param.Description ?? string.Empty)
                    + (string.IsNullOrEmpty(param.DefaultValue) ? string.Empty : $" (default value: {param.DefaultValue})"),
                Type = param.Type?.Name.ToLower() ?? "string",
                IsRequired = param.IsRequired ?? false
            });
        }

        return new OpenAIFunction
        {
            FunctionName = this.Name,
            PluginName = this.PluginName,
            Description = this.Description,
            Parameters = openAIParams,
        };
    }

    public Task AddUserMessageAsync(string message, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task AddMessageAsync(ModelMessage message, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task<ModelMessage> RetrieveMessageAsync(string messageId, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task<IEnumerable<ModelMessage>> ListMessagesAsync(CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task InvokeAsync(string assistantId, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
