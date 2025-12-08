// Copyright (c) Microsoft. All rights reserved.

#if NET

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Google.GenAI;
using Google.GenAI.Types;
using Microsoft.Extensions.AI;

// Type aliases to distinguish between Semantic Kernel and M.E.AI types
using AITextContent = Microsoft.Extensions.AI.TextContent;
using AIDataContent = Microsoft.Extensions.AI.DataContent;
using AIUriContent = Microsoft.Extensions.AI.UriContent;
using AIFunctionCallContent = Microsoft.Extensions.AI.FunctionCallContent;
using AIFunctionResultContent = Microsoft.Extensions.AI.FunctionResultContent;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Provides an <see cref="IChatClient"/> implementation based on Google.GenAI <see cref="Client"/>.
/// </summary>
internal sealed class GoogleGenAIChatClient : IChatClient
{
    /// <summary>A thought signature that can be used to skip thought validation when sending foreign function calls.</summary>
    /// <remarks>
    /// See https://ai.google.dev/gemini-api/docs/thought-signatures#faqs.
    /// This is more common in agentic scenarios, where a chat history is built up across multiple providers/models.
    /// </remarks>
    private static readonly byte[] s_skipThoughtValidation = Encoding.UTF8.GetBytes("skip_thought_signature_validator");

    /// <summary>The wrapped <see cref="Client"/> instance (optional).</summary>
    private readonly Client? _client;

    /// <summary>The wrapped <see cref="Models"/> instance.</summary>
    private readonly Models _models;

    /// <summary>The default model that should be used when no override is specified.</summary>
    private readonly string? _defaultModelId;

    /// <summary>Lazily-initialized metadata describing the implementation.</summary>
    private ChatClientMetadata? _metadata;

    /// <summary>Initializes a new <see cref="GoogleGenAIChatClient"/> instance.</summary>
    /// <param name="client">The <see cref="Client"/> to wrap.</param>
    /// <param name="defaultModelId">The default model ID to use for chat requests if not specified.</param>
    public GoogleGenAIChatClient(Client client, string? defaultModelId)
    {
        Verify.NotNull(client);

        this._client = client;
        this._models = client.Models;
        this._defaultModelId = defaultModelId;
    }

    /// <summary>Initializes a new <see cref="GoogleGenAIChatClient"/> instance.</summary>
    /// <param name="models">The <see cref="Models"/> client to wrap.</param>
    /// <param name="defaultModelId">The default model ID to use for chat requests if not specified.</param>
    public GoogleGenAIChatClient(Models models, string? defaultModelId)
    {
        Verify.NotNull(models);

        this._models = models;
        this._defaultModelId = defaultModelId;
    }

    /// <inheritdoc />
    public async Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        // Create the request.
        (string? modelId, List<Content> contents, GenerateContentConfig config) = this.CreateRequest(messages, options);

        // Send it.
        GenerateContentResponse generateResult = await this._models.GenerateContentAsync(modelId!, contents, config).ConfigureAwait(false);

        // Create the response.
        ChatResponse chatResponse = new(new ChatMessage(ChatRole.Assistant, new List<AIContent>()))
        {
            CreatedAt = generateResult.CreateTime is { } dt ? new DateTimeOffset(dt) : null,
            ModelId = !string.IsNullOrWhiteSpace(generateResult.ModelVersion) ? generateResult.ModelVersion : modelId,
            RawRepresentation = generateResult,
            ResponseId = generateResult.ResponseId,
        };

        // Populate the response messages.
        chatResponse.FinishReason = PopulateResponseContents(generateResult, chatResponse.Messages[0].Contents);

        // Populate usage information if there is any.
        if (generateResult.UsageMetadata is { } usageMetadata)
        {
            chatResponse.Usage = ExtractUsageDetails(usageMetadata);
        }

        // Return the response.
        return chatResponse;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        // Create the request.
        (string? modelId, List<Content> contents, GenerateContentConfig config) = this.CreateRequest(messages, options);

        // Send it, and process the results.
        await foreach (GenerateContentResponse generateResult in this._models.GenerateContentStreamAsync(modelId!, contents, config).WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            // Create a response update for each result in the stream.
            ChatResponseUpdate responseUpdate = new(ChatRole.Assistant, new List<AIContent>())
            {
                CreatedAt = generateResult.CreateTime is { } dt ? new DateTimeOffset(dt) : null,
                ModelId = !string.IsNullOrWhiteSpace(generateResult.ModelVersion) ? generateResult.ModelVersion : modelId,
                RawRepresentation = generateResult,
                ResponseId = generateResult.ResponseId,
            };

            // Populate the response update contents.
            responseUpdate.FinishReason = PopulateResponseContents(generateResult, responseUpdate.Contents);

            // Populate usage information if there is any.
            if (generateResult.UsageMetadata is { } usageMetadata)
            {
                responseUpdate.Contents.Add(new UsageContent(ExtractUsageDetails(usageMetadata)));
            }

            // Yield the update.
            yield return responseUpdate;
        }
    }

    /// <inheritdoc />
    public object? GetService(System.Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        if (serviceKey is null)
        {
            // If there's a request for metadata, lazily-initialize it and return it. We don't need to worry about race conditions,
            // as there's no requirement that the same instance be returned each time, and creation is idempotent.
            if (serviceType == typeof(ChatClientMetadata))
            {
                return this._metadata ??= new("gcp.gen_ai", new Uri("https://generativelanguage.googleapis.com/"), defaultModelId: this._defaultModelId);
            }

            // Allow a consumer to "break glass" and access the underlying client if they need it.
            if (serviceType.IsInstanceOfType(this._models))
            {
                return this._models;
            }

            if (this._client is not null && serviceType.IsInstanceOfType(this._client))
            {
                return this._client;
            }

            if (serviceType.IsInstanceOfType(this))
            {
                return this;
            }
        }

        return null;
    }

    /// <inheritdoc />
    void IDisposable.Dispose() { /* nop */ }

    /// <summary>Creates the message parameters for <see cref="Models.GenerateContentAsync(string, List{Content}, GenerateContentConfig?)"/> from <paramref name="messages"/> and <paramref name="options"/>.</summary>
    private (string? ModelId, List<Content> Contents, GenerateContentConfig Config) CreateRequest(IEnumerable<ChatMessage> messages, ChatOptions? options)
    {
        // Create the GenerateContentConfig object. If the options contains a RawRepresentationFactory, try to use it to
        // create the request instance, allowing the caller to populate it with GenAI-specific options. Otherwise, create
        // a new instance directly.
        string? model = this._defaultModelId;
        List<Content> contents = [];
        GenerateContentConfig config = options?.RawRepresentationFactory?.Invoke(this) as GenerateContentConfig ?? new();

        if (options is not null)
        {
            if (options.FrequencyPenalty is { } frequencyPenalty)
            {
                config.FrequencyPenalty ??= frequencyPenalty;
            }

            if (options.Instructions is { } instructions)
            {
                ((config.SystemInstruction ??= new()).Parts ??= []).Add(new() { Text = instructions });
            }

            if (options.MaxOutputTokens is { } maxOutputTokens)
            {
                config.MaxOutputTokens ??= maxOutputTokens;
            }

            if (!string.IsNullOrWhiteSpace(options.ModelId))
            {
                model = options.ModelId;
            }

            if (options.PresencePenalty is { } presencePenalty)
            {
                config.PresencePenalty ??= presencePenalty;
            }

            if (options.Seed is { } seed)
            {
                config.Seed ??= (int)seed;
            }

            if (options.StopSequences is { } stopSequences)
            {
                (config.StopSequences ??= []).AddRange(stopSequences);
            }

            if (options.Temperature is { } temperature)
            {
                config.Temperature ??= temperature;
            }

            if (options.TopP is { } topP)
            {
                config.TopP ??= topP;
            }

            if (options.TopK is { } topK)
            {
                config.TopK ??= topK;
            }

            // Populate tools. Each kind of tool is added on its own, except for function declarations,
            // which are grouped into a single FunctionDeclaration.
            List<FunctionDeclaration>? functionDeclarations = null;
            if (options.Tools is { } tools)
            {
                foreach (var tool in tools)
                {
                    switch (tool)
                    {
                        case AIFunction af:
                            functionDeclarations ??= [];
                            functionDeclarations.Add(new()
                            {
                                Name = af.Name,
                                Description = af.Description ?? "",
                            });
                            break;

                        case HostedCodeInterpreterTool:
                            (config.Tools ??= []).Add(new() { CodeExecution = new() });
                            break;

                        case HostedFileSearchTool:
                            (config.Tools ??= []).Add(new() { Retrieval = new() });
                            break;

                        case HostedWebSearchTool:
                            (config.Tools ??= []).Add(new() { GoogleSearch = new() });
                            break;
                    }
                }
            }

            if (functionDeclarations is { Count: > 0 })
            {
                Tool functionTools = new();
                (functionTools.FunctionDeclarations ??= []).AddRange(functionDeclarations);
                (config.Tools ??= []).Add(functionTools);
            }

            // Transfer over the tool mode if there are any tools.
            if (options.ToolMode is { } toolMode && config.Tools?.Count > 0)
            {
                switch (toolMode)
                {
                    case NoneChatToolMode:
                        config.ToolConfig = new() { FunctionCallingConfig = new() { Mode = FunctionCallingConfigMode.NONE } };
                        break;

                    case AutoChatToolMode:
                        config.ToolConfig = new() { FunctionCallingConfig = new() { Mode = FunctionCallingConfigMode.AUTO } };
                        break;

                    case RequiredChatToolMode required:
                        config.ToolConfig = new() { FunctionCallingConfig = new() { Mode = FunctionCallingConfigMode.ANY } };
                        if (required.RequiredFunctionName is not null)
                        {
                            ((config.ToolConfig.FunctionCallingConfig ??= new()).AllowedFunctionNames ??= []).Add(required.RequiredFunctionName);
                        }
                        break;
                }
            }

            // Set the response format if specified.
            if (options.ResponseFormat is ChatResponseFormatJson responseFormat)
            {
                config.ResponseMimeType = "application/json";
                if (responseFormat.Schema is { } schema)
                {
                    config.ResponseJsonSchema = schema;
                }
            }
        }

        // Transfer messages to request, handling system messages specially
        Dictionary<string, string>? callIdToFunctionNames = null;
        foreach (var message in messages)
        {
            if (message.Role == ChatRole.System)
            {
                string instruction = message.Text;
                if (!string.IsNullOrWhiteSpace(instruction))
                {
                    ((config.SystemInstruction ??= new()).Parts ??= []).Add(new() { Text = instruction });
                }

                continue;
            }

            Content content = new() { Role = message.Role == ChatRole.Assistant ? "model" : "user" };
            content.Parts ??= [];
            AddPartsForAIContents(ref callIdToFunctionNames, message.Contents, content.Parts);

            contents.Add(content);
        }

        // Make sure the request contains at least one content part (the request would always fail if empty).
        if (!contents.SelectMany(c => c.Parts ?? Enumerable.Empty<Part>()).Any())
        {
            contents.Add(new() { Role = "user", Parts = [new() { Text = "" }] });
        }

        return (model, contents, config);
    }

    /// <summary>Creates <see cref="Part"/>s for <paramref name="contents"/> and adds them to <paramref name="parts"/>.</summary>
    private static void AddPartsForAIContents(ref Dictionary<string, string>? callIdToFunctionNames, IList<AIContent> contents, List<Part> parts)
    {
        for (int i = 0; i < contents.Count; i++)
        {
            var content = contents[i];

            byte[]? thoughtSignature = null;
            if (content is not TextReasoningContent { ProtectedData: not null } &&
                i + 1 < contents.Count &&
                contents[i + 1] is TextReasoningContent nextReasoning &&
                string.IsNullOrWhiteSpace(nextReasoning.Text) &&
                nextReasoning.ProtectedData is { } protectedData)
            {
                i++;
                thoughtSignature = Convert.FromBase64String(protectedData);
            }

            // Before the main switch, do any necessary state tracking. We want to do this
            // even if the AIContent includes a Part as its RawRepresentation.
            if (content is AIFunctionCallContent fcc)
            {
                (callIdToFunctionNames ??= [])[fcc.CallId] = fcc.Name;
                callIdToFunctionNames[""] = fcc.Name; // track last function name in case calls don't have IDs
            }

            Part? part = null;
            switch (content)
            {
                case AIContent aic when aic.RawRepresentation is Part rawPart:
                    part = rawPart;
                    break;

                case AITextContent textContent:
                    part = new() { Text = textContent.Text };
                    break;

                case TextReasoningContent reasoningContent:
                    part = new()
                    {
                        Thought = true,
                        Text = !string.IsNullOrWhiteSpace(reasoningContent.Text) ? reasoningContent.Text : null,
                        ThoughtSignature = reasoningContent.ProtectedData is not null ? Convert.FromBase64String(reasoningContent.ProtectedData) : null,
                    };
                    break;

                case AIDataContent dataContent:
                    part = new()
                    {
                        InlineData = new()
                        {
                            MimeType = dataContent.MediaType,
                            Data = dataContent.Data.ToArray(),
                            DisplayName = dataContent.Name,
                        }
                    };
                    break;

                case AIUriContent uriContent:
                    part = new()
                    {
                        FileData = new()
                        {
                            FileUri = uriContent.Uri.AbsoluteUri,
                            MimeType = uriContent.MediaType,
                        }
                    };
                    break;

                case AIFunctionCallContent functionCallContent:
                    part = new()
                    {
                        FunctionCall = new()
                        {
                            Id = functionCallContent.CallId,
                            Name = functionCallContent.Name,
                            Args = functionCallContent.Arguments is null ? null : functionCallContent.Arguments as Dictionary<string, object> ?? new(functionCallContent.Arguments!),
                        },
                        ThoughtSignature = thoughtSignature ?? s_skipThoughtValidation,
                    };
                    break;

                case AIFunctionResultContent functionResultContent:
                    FunctionResponse funcResponse = new()
                    {
                        Id = functionResultContent.CallId,
                    };

                    if (callIdToFunctionNames?.TryGetValue(functionResultContent.CallId ?? "", out string? functionName) is true ||
                        callIdToFunctionNames?.TryGetValue("", out functionName) is true)
                    {
                        funcResponse.Name = functionName;
                    }

                    switch (functionResultContent.Result)
                    {
                        case null:
                            break;

                        case AIContent aic when ToFunctionResponsePart(aic) is { } singleContentBlob:
                            funcResponse.Parts = [singleContentBlob];
                            break;

                        case IEnumerable<AIContent> aiContents:
                            List<AIContent>? nonBlobContent = null;
                            foreach (var aiContent in aiContents)
                            {
                                if (ToFunctionResponsePart(aiContent) is { } contentBlob)
                                {
                                    (funcResponse.Parts ??= []).Add(contentBlob);
                                }
                                else
                                {
                                    (nonBlobContent ??= []).Add(aiContent);
                                }
                            }

                            if (nonBlobContent is not null)
                            {
                                funcResponse.Response = new() { ["result"] = nonBlobContent };
                            }
                            break;

                        case AITextContent textContent:
                            funcResponse.Response = new() { ["result"] = textContent.Text };
                            break;

                        default:
                            funcResponse.Response = new() { ["result"] = functionResultContent.Result };
                            break;
                    }

                    part = new()
                    {
                        FunctionResponse = funcResponse,
                    };

                    static FunctionResponsePart? ToFunctionResponsePart(AIContent content)
                    {
                        switch (content)
                        {
                            case AIContent when content.RawRepresentation is FunctionResponsePart functionResponsePart:
                                return functionResponsePart;

                            case AIDataContent dc when IsSupportedMediaType(dc.MediaType):
                                FunctionResponseBlob dataBlob = new()
                                {
                                    MimeType = dc.MediaType,
                                    Data = dc.Data.Span.ToArray(),
                                };

                                if (!string.IsNullOrWhiteSpace(dc.Name))
                                {
                                    dataBlob.DisplayName = dc.Name;
                                }

                                return new() { InlineData = dataBlob };

                            case AIUriContent uc when IsSupportedMediaType(uc.MediaType):
                                return new()
                                {
                                    FileData = new()
                                    {
                                        MimeType = uc.MediaType,
                                        FileUri = uc.Uri.AbsoluteUri,
                                    }
                                };

                            default:
                                return null;
                        }

                        // https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling#mm-fr
                        static bool IsSupportedMediaType(string mediaType) =>
                            // images
                            mediaType.Equals("image/png", StringComparison.OrdinalIgnoreCase) ||
                            mediaType.Equals("image/jpeg", StringComparison.OrdinalIgnoreCase) ||
                            mediaType.Equals("image/webp", StringComparison.OrdinalIgnoreCase) ||
                            // documents
                            mediaType.Equals("application/pdf", StringComparison.OrdinalIgnoreCase) ||
                            mediaType.Equals("text/plain", StringComparison.OrdinalIgnoreCase);
                    }
                    break;
            }

            if (part is not null)
            {
                part.ThoughtSignature ??= thoughtSignature;
                parts.Add(part);
            }

            thoughtSignature = null;
        }
    }

    /// <summary>Creates <see cref="AIContent"/>s for <paramref name="parts"/> and adds them to <paramref name="contents"/>.</summary>
    [SuppressMessage("Design", "MEAI001:Suppress for experimental types", Justification = "Using experimental MEAI types")]
    private static void AddAIContentsForParts(List<Part> parts, IList<AIContent> contents)
    {
        foreach (var part in parts)
        {
            AIContent content;

            if (!string.IsNullOrEmpty(part.Text))
            {
                content = part.Thought is true ?
                    new TextReasoningContent(part.Text) :
                    new AITextContent(part.Text);
            }
            else if (part.InlineData is { } inlineData)
            {
                content = new AIDataContent(inlineData.Data, inlineData.MimeType ?? "application/octet-stream")
                {
                    Name = inlineData.DisplayName,
                };
            }
            else if (part.FileData is { FileUri: not null } fileData)
            {
                content = new AIUriContent(new Uri(fileData.FileUri), fileData.MimeType ?? "application/octet-stream");
            }
            else if (part.FunctionCall is { Name: not null } functionCall)
            {
                content = new AIFunctionCallContent(functionCall.Id ?? "", functionCall.Name, functionCall.Args!);
            }
            else if (part.FunctionResponse is { } functionResponse)
            {
                content = new AIFunctionResultContent(
                    functionResponse.Id ?? "",
                    functionResponse.Response?.TryGetValue("output", out var output) is true ? output :
                    functionResponse.Response?.TryGetValue("error", out var error) is true ? error :
                    null);
            }
            else if (part.ExecutableCode is { Code: not null } executableCode)
            {
#pragma warning disable MEAI001 // CodeInterpreterToolCallContent is experimental
                content = new CodeInterpreterToolCallContent()
                {
                    Inputs =
                    [
                        new AIDataContent(Encoding.UTF8.GetBytes(executableCode.Code), executableCode.Language switch
                        {
                            Language.PYTHON => "text/x-python",
                            _ => "text/x-source-code",
                        })
                    ],
                };
#pragma warning restore MEAI001
            }
            else if (part.CodeExecutionResult is { Output: { } codeOutput } codeExecutionResult)
            {
#pragma warning disable MEAI001 // CodeInterpreterToolResultContent is experimental
                content = new CodeInterpreterToolResultContent()
                {
                    Outputs =
                    [
                        codeExecutionResult.Outcome is Outcome.OUTCOME_OK ?
                            new AITextContent(codeOutput) :
                            new ErrorContent(codeOutput) { ErrorCode = codeExecutionResult.Outcome.ToString() }
                    ],
                };
#pragma warning restore MEAI001
            }
            else
            {
                content = new AIContent();
            }

            content.RawRepresentation = part;
            contents.Add(content);

            if (part.ThoughtSignature is { } thoughtSignature)
            {
                contents.Add(new TextReasoningContent(null)
                {
                    ProtectedData = Convert.ToBase64String(thoughtSignature),
                });
            }
        }
    }

    private static ChatFinishReason? PopulateResponseContents(GenerateContentResponse generateResult, IList<AIContent> responseContents)
    {
        ChatFinishReason? finishReason = null;

        // Populate the response messages. There should only be at most one candidate, but if there are more, ignore all but the first.
        if (generateResult.Candidates is { Count: > 0 } &&
            generateResult.Candidates[0] is { Content: { } candidateContent } candidate)
        {
            // Grab the finish reason if one exists.
            finishReason = ConvertFinishReason(candidate.FinishReason);

            // Add all of the response content parts as AIContents.
            if (candidateContent.Parts is { } parts)
            {
                AddAIContentsForParts(parts, responseContents);
            }

            // Add any citation metadata.
            if (candidate.CitationMetadata is { Citations: { Count: > 0 } citations } &&
                responseContents.OfType<AITextContent>().FirstOrDefault() is AITextContent textContent)
            {
                foreach (var citation in citations)
                {
                    textContent.Annotations =
                    [
                        new CitationAnnotation()
                        {
                            Title = citation.Title,
                            Url = Uri.TryCreate(citation.Uri, UriKind.Absolute, out Uri? uri) ? uri : null,
                            AnnotatedRegions =
                            [
                                new TextSpanAnnotatedRegion()
                                {
                                    StartIndex = citation.StartIndex,
                                    EndIndex = citation.EndIndex,
                                }
                            ],
                        }
                    ];
                }
            }
        }

        // Populate error information if there is any.
        if (generateResult.PromptFeedback is { } promptFeedback)
        {
            responseContents.Add(new ErrorContent(promptFeedback.BlockReasonMessage));
        }

        return finishReason;
    }

    /// <summary>Creates an M.E.AI <see cref="ChatFinishReason"/> from a Google <see cref="FinishReason"/>.</summary>
    private static ChatFinishReason? ConvertFinishReason(FinishReason? finishReason)
    {
        return finishReason switch
        {
            null => null,

            FinishReason.MAX_TOKENS =>
                ChatFinishReason.Length,

            FinishReason.MALFORMED_FUNCTION_CALL or
            FinishReason.UNEXPECTED_TOOL_CALL =>
                ChatFinishReason.ToolCalls,

            FinishReason.FINISH_REASON_UNSPECIFIED or
            FinishReason.STOP =>
                ChatFinishReason.Stop,

            _ => ChatFinishReason.ContentFilter,
        };
    }

    /// <summary>Creates a <see cref="UsageDetails"/> populated from the supplied <paramref name="usageMetadata"/>.</summary>
    private static UsageDetails ExtractUsageDetails(GenerateContentResponseUsageMetadata usageMetadata)
    {
        UsageDetails details = new()
        {
            InputTokenCount = usageMetadata.PromptTokenCount,
            OutputTokenCount = usageMetadata.CandidatesTokenCount,
            TotalTokenCount = usageMetadata.TotalTokenCount,
        };

        AddIfPresent(nameof(usageMetadata.CachedContentTokenCount), usageMetadata.CachedContentTokenCount);
        AddIfPresent(nameof(usageMetadata.ThoughtsTokenCount), usageMetadata.ThoughtsTokenCount);
        AddIfPresent(nameof(usageMetadata.ToolUsePromptTokenCount), usageMetadata.ToolUsePromptTokenCount);

        return details;

        void AddIfPresent(string key, int? value)
        {
            if (value is int intValue)
            {
                (details.AdditionalCounts ??= [])[key] = intValue;
            }
        }
    }
}

#endif
