// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Diagnostics;
using Extensions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Orchestration;
using SemanticFunctions;
using SemanticKernel.AI.ChatCompletion;
using SemanticKernel.AI.TextCompletion;
using SkillDefinition;

#pragma warning disable format
/// <summary>
/// A semantic function that calls other functions
/// </summary>
public sealed class SKFunctionCall : ISKFunction, IDisposable
{

    /// <summary>
    /// The maximum number of callable functions to include in a FunctionCall request
    /// </summary>
    public const int MaxCallableFunctions = 64;

    /// <inheritdoc />
    public string Name { get; }

    /// <inheritdoc />
    public string SkillName { get; }

    /// <inheritdoc />
    public string Description { get; }

    /// <inheritdoc />
    public bool IsSemantic => true;

    /// <inheritdoc />
    public CompleteRequestSettings RequestSettings { get; private set; } = new();

    /// <summary>
    ///  The callable functions for this SKFunctionCall instance
    /// </summary>
    public List<FunctionDefinition> CallableFunctions { get; }

    /// <summary>
    ///  Whether to call execute the function call automatically
    /// </summary>
    public bool CallFunctionsAutomatically { get; }


    /// <summary>
    /// Initializes a new instance of <see cref="SKFunctionCall"/>.
    /// </summary>
    /// <param name="skillName"></param>
    /// <param name="functionName"></param>
    /// <param name="functionConfig"></param>
    /// <param name="loggerFactory"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static ISKFunction FromConfig(
        string skillName,
        string functionName,
        SKFunctionCallConfig functionConfig,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(functionConfig);

        var func = new SKFunctionCall(
            functionConfig.PromptTemplate,
            skillName,
            functionName,
            functionConfig.PromptTemplateConfig.Description,
            functionConfig.TargetFunction,
            functionConfig.CallableFunctions,
            functionConfig.CallFunctionsAutomatically,
            loggerFactory
        );

        return func;
    }


    /// <inheritdoc />
    public FunctionView Describe()
    {
        return new FunctionView
        {
            IsSemantic = IsSemantic,
            Name = Name,
            SkillName = SkillName,
            Description = Description,
            Parameters = CallableFunctions.Select(f => new ParameterView(f.Name, f.Description)).ToList()
        };
    }


    /// <inheritdoc />
    public async Task<SKContext> InvokeAsync(SKContext context, CompleteRequestSettings? settings = null, CancellationToken cancellationToken = default)
    {
        if (_skillCollection is null)
        {
            SetDefaultSkillCollection(context.Skills);
        }

        var requestSettings = GetRequestSettings(settings ?? RequestSettings);

        // trim any skills from the 
        IReadOnlyList<IChatResult> results = await RunPromptAsync(_aiService?.Value, requestSettings, context, cancellationToken).ConfigureAwait(false);
        context.ModelResults = results.Select(c => c.ModelResult).ToArray();

        if (CallFunctionsAutomatically)
        {
            return await ExecuteFunctionCallAsync(results.ToList(), context, cancellationToken).ConfigureAwait(false);
        }

        var content = await GetCompletionsResultContentAsync(results.ToList(), cancellationToken).ConfigureAwait(false);
        context.Variables.Update(content);
        return context;
    }


    /// <inheritdoc />
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
    {
        _skillCollection = skills;
        CallableFunctions.Clear();

        if (_targetFunctionDefinition != FunctionDefinition.Auto)
        {
            CallableFunctions.Add(_targetFunctionDefinition);
        }

        List<FunctionDefinition> functionDefinitions = skills.GetFunctionDefinitions(new[] { SkillName }).Take(MaxCallableFunctions - 1).ToList();
        CallableFunctions.AddRange(functionDefinitions);

        return this;
    }


    /// <inheritdoc />
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        Verify.NotNull(serviceFactory);
        var textService = serviceFactory();

        // Mainly check if the service returned by the factory could be cast as IChatCompletion
        if (textService is not IChatCompletion chatService)
        {
            throw new SKException("The service factory must return an IOpenAIChatCompletion");
        }
        _aiService = new Lazy<IChatCompletion>(() => chatService);
        return this;

    }


    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
    {
        Verify.NotNull(settings);
        RequestSettings = settings;
        return this;
    }


    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
        if (_aiService is { IsValueCreated: true } aiService)
        {
            (aiService.Value as IDisposable)?.Dispose();
        }
    }


    internal SKFunctionCall(
        IPromptTemplate template,
        string skillName,
        string functionName,
        string description,
        FunctionDefinition? targetFunctionDefinition = null,
        List<FunctionDefinition>? callableFunctions = null,
        bool callFunctionsAutomatically = true,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(template);
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);

        _logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(SKFunctionCall)) : NullLogger.Instance;

        _promptTemplate = template;

        Name = functionName;
        SkillName = skillName;
        Description = description;
        _targetFunctionDefinition = targetFunctionDefinition ?? FunctionExtensions.Default;
        CallFunctionsAutomatically = callFunctionsAutomatically;
        CallableFunctions = callableFunctions ?? new List<FunctionDefinition>();

        if (_targetFunctionDefinition != FunctionDefinition.Auto)
        {
            CallableFunctions.Add(_targetFunctionDefinition);
        }
    }


    #region private

    private readonly ILogger _logger;
    private IReadOnlySkillCollection? _skillCollection;
    private Lazy<IChatCompletion>? _aiService;
    private readonly FunctionDefinition _targetFunctionDefinition;
    private ISKFunction? _functionToCall;
    private readonly IPromptTemplate _promptTemplate;


    private FunctionCallRequestSettings GetRequestSettings(CompleteRequestSettings settings)
    {
        // Remove duplicates, if any, due to the inaccessibility of ReadOnlySkillCollection
        // Can't changes what skills are available to the context because you can't remove skills from the context
        List<FunctionDefinition> distinctCallableFunctions = CallableFunctions
            .GroupBy(func => func.Name)
            .Select(group => group.First())
            .ToList();

        var requestSettings = new FunctionCallRequestSettings()
        {
            Temperature = settings.Temperature,
            TopP = settings.TopP,
            PresencePenalty = settings.PresencePenalty,
            FrequencyPenalty = settings.FrequencyPenalty,
            StopSequences = settings.StopSequences,
            MaxTokens = settings.MaxTokens,
            FunctionCall = _targetFunctionDefinition,
            CallableFunctions = distinctCallableFunctions
        };

        return requestSettings;
    }


    private static async Task<FunctionCallResult?> GetFunctionCallResponseAsync(IReadOnlyList<IChatResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        //check if the first completion is a function call
        var message = await completions[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        return message?.ToFunctionCallResult();
    }


    private static async Task<string> GetCompletionsResultContentAsync(IReadOnlyList<IChatResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        var message = await completions[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        return message.Content;
    }


    private async Task<IReadOnlyList<IChatResult>> RunPromptAsync(
        IChatCompletion? client,
        FunctionCallRequestSettings? requestSettings,
        SKContext context,
        CancellationToken cancellationToken)
    {
        Verify.NotNull(client);
        Verify.NotNull(requestSettings);

        try
        {
            var renderedPrompt = await _promptTemplate.RenderAsync(context, cancellationToken).ConfigureAwait(false);

            if (client is null)
            {
                throw new SKException(" Must be an OpenAI model");
            }

            IReadOnlyList<IChatResult>? completionResults = await client.GetChatCompletionsAsync(
                    client.CreateNewChat(renderedPrompt),
                    requestSettings, cancellationToken)
                .ConfigureAwait(false);

            if (completionResults is null)
            {
                throw new SKException("The completion results are null");
            }
            return completionResults;
        }
        catch (HttpOperationException ex)
        {
            const string MESSAGE = "Something went wrong while rendering the semantic function" +
                                   " or while executing the text completion. Function: {SkillName}.{FunctionName} - {Message}. {ResponseContent}";
            _logger.LogError(ex, MESSAGE, SkillName, Name, ex.Message, ex.ResponseContent);
            throw;
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            const string MESSAGE = "Something went wrong while rendering the semantic function" +
                                   " or while executing the text completion. Function: {SkillName}.{FunctionName} - {Message}";
            _logger.LogError(ex, MESSAGE, SkillName, Name, ex.Message);
            throw;
        }

    }


    private async Task<SKContext> ExecuteFunctionCallAsync(IReadOnlyList<IChatResult> results, SKContext context, CancellationToken cancellationToken)
    {
        var functionCallResult = await GetFunctionCallResponseAsync(results, cancellationToken).ConfigureAwait(false);

        if (functionCallResult is null)
        {
            throw new SKException("The function call result is null");
        }

        if (!_skillCollection!.TryGetFunction(functionCallResult, out _functionToCall))
        {
            throw new SKException($"The function {functionCallResult.Function} is not available");
        }
        // Update the result with the completion
        context.Variables.Update(functionCallResult.FunctionParameters());

        if (_functionToCall != null)
        {
            context = await _functionToCall.InvokeAsync(context, cancellationToken: cancellationToken).ConfigureAwait(false);
        }

        return context;
    }

    #endregion


}
