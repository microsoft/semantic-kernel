// Copyright (c) Microsoft. All rights reserved.

using Amazon;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Services;

/// <summary>
/// Represents a chat completion service using Amazon Bedrock API.
/// </summary>
public class BedrockChatCompletionService : BedrockChatCompletionClient<IChatCompletionRequest, IChatCompletionResponse>, IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];

    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService using an IAmazonBedrockRuntime object passed in by the user.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="bedrockApi">The IAmazonBedrockRuntime object to be used for DI.</param>
    public BedrockChatCompletionService(string modelId, IAmazonBedrockRuntime bedrockApi)
        : base(modelId, bedrockApi)
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService by creating a new AmazonBedrockRuntimeClient().
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    public BedrockChatCompletionService(string modelId)
        : base(modelId, new AmazonBedrockRuntimeClient())
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with the credentials loaded from the application's
    /// default configuration, and if unsuccessful from the Instance Profile service on an EC2 instance.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="region">The region to connect.</param>
    public BedrockChatCompletionService(string modelId, RegionEndpoint region)
        : base(modelId, new AmazonBedrockRuntimeClient(region))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with the credentials loaded from the application's
    /// default configuration, and if unsuccessful from the Instance Profile service on an EC2 instance.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="clientConfig">The AmazonBedrockRuntimeClient Configuration Object.</param>
    public BedrockChatCompletionService(string modelId, AmazonBedrockRuntimeConfig clientConfig)
        : base(modelId, new AmazonBedrockRuntimeClient(clientConfig))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService with AWSCredentials object for authentication.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion. </param>
    /// <param name="awsCredentials">AWS Credentials. </param>
    public BedrockChatCompletionService(string modelId, AWSCredentials awsCredentials)
        : base(modelId, new AmazonBedrockRuntimeClient(awsCredentials))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService with AWSCredentials object for authentication.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsCredentials">AWS Credentials.</param>
    /// <param name="region">The region to connect.</param>
    public BedrockChatCompletionService(string modelId, AWSCredentials awsCredentials, RegionEndpoint region)
        : base(modelId, new AmazonBedrockRuntimeClient(awsCredentials, region))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Credentials and an
    /// AmazonBedrockRuntimeClient Configuration object.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsCredentials">AWS Credentials.</param>
    /// <param name="clientConfig">The AmazonBedrockRuntimeClient Configuration Object</param>
    public BedrockChatCompletionService(string modelId, AWSCredentials awsCredentials, AmazonBedrockRuntimeConfig clientConfig)
        : base(modelId, new AmazonBedrockRuntimeClient(awsCredentials, clientConfig))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Access Key ID and AWS Secret Key
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsAccessKeyId">AWS Access Key ID</param>
    /// <param name="awsSecretAccessKey">AWS Secret Access Key</param>
    public BedrockChatCompletionService(string modelId, string awsAccessKeyId, string awsSecretAccessKey)
        : base(modelId, new AmazonBedrockRuntimeClient(awsAccessKeyId, awsSecretAccessKey))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Access Key ID and AWS Secret Key.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsAccessKeyId">AWS Access Key ID</param>
    /// <param name="awsSecretAccessKey">AWS Secret Access Key</param>
    /// <param name="region">The region to connect.</param>
    public BedrockChatCompletionService(string modelId, string awsAccessKeyId, string awsSecretAccessKey, RegionEndpoint region)
        : base(modelId, new AmazonBedrockRuntimeClient(awsAccessKeyId, awsSecretAccessKey, region))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Access Key ID, AWS Secret Key and an
    /// AmazonBedrockRuntimeClient Configuration object.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsAccessKeyId">AWS Access Key ID</param>
    /// <param name="awsSecretAccessKey">AWS Secret Access Key</param>
    /// <param name="clientConfig">The AmazonBedrockRuntimeClient Configuration Object</param>
    public BedrockChatCompletionService(string modelId, string awsAccessKeyId, string awsSecretAccessKey, AmazonBedrockRuntimeConfig clientConfig)
        : base(modelId, new AmazonBedrockRuntimeClient(awsAccessKeyId, awsSecretAccessKey, clientConfig))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Access Key ID and AWS Secret Key and AWS Session Token.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsAccessKeyId">AWS Access Key ID</param>
    /// <param name="awsSecretAccessKey">AWS Secret Access Key</param>
    /// <param name="awsSessionToken">AWS Session Token</param>
    public BedrockChatCompletionService(string modelId, string awsAccessKeyId, string awsSecretAccessKey, string awsSessionToken)
        : base(modelId, new AmazonBedrockRuntimeClient(awsAccessKeyId, awsSecretAccessKey, awsSessionToken))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Access Key ID and AWS Secret Key and AWS Session Token.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsAccessKeyId">AWS Access Key ID</param>
    /// <param name="awsSecretAccessKey">AWS Secret Access Key</param>
    /// <param name="awsSessionToken">AWS Session Token</param>
    /// <param name="region">The region to connect.</param>
    public BedrockChatCompletionService(string modelId, string awsAccessKeyId, string awsSecretAccessKey, string awsSessionToken, RegionEndpoint region)
        : base(modelId, new AmazonBedrockRuntimeClient(awsAccessKeyId, awsSecretAccessKey, awsSessionToken, region))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService.
    /// Constructs AmazonBedrockRuntimeClient with AWS Access Key ID, AWS Secret Key and an
    /// AmazonBedrockRuntimeClient Configuration object.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="awsAccessKeyId">AWS Access Key ID</param>
    /// <param name="awsSecretAccessKey">AWS Secret Access Key</param>
    /// <param name="awsSessionToken">AWS Session Token</param>
    /// <param name="clientConfig">The AmazonBedrockRuntimeClient Configuration Object</param>
    public BedrockChatCompletionService(string modelId, string awsAccessKeyId, string awsSecretAccessKey, string awsSessionToken, AmazonBedrockRuntimeConfig clientConfig)
        : base(modelId, new AmazonBedrockRuntimeClient(awsAccessKeyId, awsSecretAccessKey, awsSessionToken, clientConfig))
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.GenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.StreamChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
