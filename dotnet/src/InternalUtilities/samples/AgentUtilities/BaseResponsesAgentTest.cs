// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;
using OpenAI.Files;
using OpenAI.Responses;
using OpenAI.VectorStores;

/// <summary>
/// Base class for samples that demonstrate the usage of <see cref="OpenAIResponseAgent"/>.
/// </summary>
public abstract class BaseResponsesAgentTest : BaseAgentsTest<ResponsesClient>
{
    protected BaseResponsesAgentTest(ITestOutputHelper output, string? model = null) : base(output)
    {
        var options = new OpenAIClientOptions();
        if (this.EnableLogging)
        {
            options.MessageLoggingPolicy = new MessageLoggingPolicy(new()
            {
                EnableLogging = true,
                EnableMessageLogging = true,
                EnableMessageContentLogging = true,
                LoggerFactory = this.LoggerFactory
            });
        }

        this.Client = new(model: model ?? TestConfiguration.OpenAI.ChatModelId, credential: new ApiKeyCredential(TestConfiguration.OpenAI.ApiKey), options: options);
        this.FileClient = new OpenAIFileClient(TestConfiguration.OpenAI.ApiKey);
        this.VectorStoreClient = new VectorStoreClient(TestConfiguration.OpenAI.ApiKey);
    }

    protected OpenAIFileClient FileClient { get; set; }

    protected VectorStoreClient VectorStoreClient { get; set; }

    protected bool EnableLogging { get; set; } = false;

    /// <inheritdoc/>
    protected override ResponsesClient Client { get; }
}
