// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class SKFunction : ISKFunction, IDisposable
{
    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string SkillName { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public bool IsSemantic { get; }

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings => this._aiRequestSettings;

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IList<ParameterView> Parameters { get; }

    /// <summary>
    /// Create a native function instance, wrapping a native object method
    /// </summary>
    /// <param name="methodSignature">Signature of the method to invoke</param>
    /// <param name="methodContainerInstance">Object containing the method to invoke</param>
    /// <param name="skillName">SK skill name</param>
    /// <param name="log">Application logger</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction? FromNativeMethod(
        MethodInfo methodSignature,
        object? methodContainerInstance = null,
        string skillName = "",
        ILogger? log = null)
    {
        if (!methodSignature.IsStatic && methodContainerInstance is null)
        {
            throw new ArgumentNullException(nameof(methodContainerInstance), "Argument cannot be null for non-static methods");
        }

        if (string.IsNullOrWhiteSpace(skillName))
        {
            skillName = SkillCollection.GlobalSkill;
        }

        MethodDetails methodDetails = GetMethodDetails(methodSignature, methodContainerInstance, true, log);

        // If the given method is not a valid SK function
        if (!methodDetails.HasSkFunctionAttribute)
        {
            return null;
        }

        return new SKFunction(
            delegateFunction: methodDetails.Function,
            parameters: methodDetails.Parameters,
            skillName: skillName,
            functionName: methodDetails.Name,
            description: methodDetails.Description,
            isSemantic: false,
            log: log);
    }

    /// <summary>
    /// Create a native function instance, wrapping a delegate function
    /// </summary>
    /// <param name="nativeFunction">Function to invoke</param>
    /// <param name="skillName">SK skill name</param>
    /// <param name="functionName">SK function name</param>
    /// <param name="description">SK function description</param>
    /// <param name="parameters">SK function parameters</param>
    /// <param name="log">Application logger</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromNativeFunction(
        Delegate nativeFunction,
        string skillName,
        string functionName,
        string description,
        IEnumerable<ParameterView>? parameters = null,
        ILogger? log = null)
    {
        MethodDetails methodDetails = GetMethodDetails(nativeFunction.Method, nativeFunction.Target, false, log);

        return new SKFunction(
            delegateFunction: methodDetails.Function,
            parameters: parameters is not null ? parameters.ToList() : (IList<ParameterView>)Array.Empty<ParameterView>(),
            description: description,
            skillName: skillName,
            functionName: functionName,
            isSemantic: false,
            log: log);
    }

    /// <summary>
    /// Create a native function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="skillName">Name of the skill to which the function to create belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="functionConfig">Semantic function configuration.</param>
    /// <param name="log">Optional logger for the function.</param>
    /// <returns>SK function instance.</returns>
    public static ISKFunction FromSemanticConfig(
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig,
        ILogger? log = null)
    {
        Verify.NotNull(functionConfig);

        async Task<SKContext> LocalFunc(
            ITextCompletion? client,
            CompleteRequestSettings? requestSettings,
            SKContext context)
        {
            Verify.NotNull(client);
            Verify.NotNull(requestSettings);

            try
            {
                string prompt = await functionConfig.PromptTemplate.RenderAsync(context).ConfigureAwait(false);

                string completion = await client.CompleteAsync(prompt, requestSettings, context.CancellationToken).ConfigureAwait(false);
                context.Variables.Update(completion);
            }
            catch (AIException ex)
            {
                const string Message = "Something went wrong while rendering the semantic function" +
                                       " or while executing the text completion. Function: {0}.{1}. Error: {2}. Details: {3}";
                log?.LogError(ex, Message, skillName, functionName, ex.Message, ex.Detail);
                context.Fail(ex.Message, ex);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                const string Message = "Something went wrong while rendering the semantic function" +
                                       " or while executing the text completion. Function: {0}.{1}. Error: {2}";
                log?.LogError(ex, Message, skillName, functionName, ex.Message);
                context.Fail(ex.Message, ex);
            }

            return context;
        }

        return new SKFunction(
            delegateFunction: LocalFunc,
            parameters: functionConfig.PromptTemplate.GetParameters(),
            description: functionConfig.PromptTemplateConfig.Description,
            skillName: skillName,
            functionName: functionName,
            isSemantic: true,
            log: log);
    }

    /// <inheritdoc/>
    public FunctionView Describe()
    {
        return new FunctionView
        {
            IsSemantic = this.IsSemantic,
            Name = this.Name,
            SkillName = this.SkillName,
            Description = this.Description,
            Parameters = this.Parameters,
        };
    }

    /// <inheritdoc/>
    public Task<SKContext> InvokeAsync(SKContext context, CompleteRequestSettings? settings = null)
    {
        // If the function is invoked manually, the user might have left out the skill collection
        context.Skills ??= this._skillCollection;

        return this.IsSemantic ?
            InvokeSemanticAsync(context, settings) :
            this._function(null, settings, context);

        async Task<SKContext> InvokeSemanticAsync(SKContext context, CompleteRequestSettings? settings)
        {
            var resultContext = await this._function(this._aiService?.Value, settings ?? this._aiRequestSettings, context).ConfigureAwait(false);
            context.Variables.Update(resultContext.Variables);
            return context;
        }
    }

    /// <inheritdoc/>
    public Task<SKContext> InvokeAsync(
        string? input = null,
        CompleteRequestSettings? settings = null,
        ISemanticTextMemory? memory = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        SKContext context = new(
            new ContextVariables(input),
            memory: memory,
            skills: this._skillCollection,
            logger: logger,
            cancellationToken: cancellationToken);

        return this.InvokeAsync(context, settings);
    }

    /// <inheritdoc/>
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
    {
        this._skillCollection = skills;
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        Verify.NotNull(serviceFactory);
        this.VerifyIsSemantic();
        this._aiService = new Lazy<ITextCompletion>(serviceFactory);
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
    {
        Verify.NotNull(settings);
        this.VerifyIsSemantic();
        this._aiRequestSettings = settings;
        return this;
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
        if (this._aiService is { IsValueCreated: true } aiService)
        {
            (aiService.Value as IDisposable)?.Dispose();
        }
    }

    /// <summary>
    /// JSON serialized string representation of the function.
    /// </summary>
    public override string ToString()
        => this.ToString(false);

    /// <summary>
    /// JSON serialized string representation of the function.
    /// </summary>
    public string ToString(bool writeIndented)
        => JsonSerializer.Serialize(this, options: writeIndented ? s_toStringIndentedSerialization : s_toStringStandardSerialization);

    #region private

    private static readonly JsonSerializerOptions s_toStringStandardSerialization = new();
    private static readonly JsonSerializerOptions s_toStringIndentedSerialization = new() { WriteIndented = true };
    private readonly Func<ITextCompletion?, CompleteRequestSettings?, SKContext, Task<SKContext>> _function;
    private readonly ILogger _log;
    private IReadOnlySkillCollection? _skillCollection;
    private Lazy<ITextCompletion>? _aiService = null;
    private CompleteRequestSettings _aiRequestSettings = new();

    private struct MethodDetails
    {
        public bool HasSkFunctionAttribute { get; set; }
        public Func<ITextCompletion?, CompleteRequestSettings?, SKContext, Task<SKContext>> Function { get; set; }
        public List<ParameterView> Parameters { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
    }

    internal SKFunction(
        Func<ITextCompletion?, CompleteRequestSettings?, SKContext, Task<SKContext>> delegateFunction,
        IList<ParameterView> parameters,
        string skillName,
        string functionName,
        string description,
        bool isSemantic = false,
        ILogger? log = null)
    {
        Verify.NotNull(delegateFunction);
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);
        Verify.ParametersUniqueness(parameters);

        this._log = log ?? NullLogger.Instance;

        this._function = delegateFunction;
        this.Parameters = parameters;

        this.IsSemantic = isSemantic;
        this.Name = functionName;
        this.SkillName = skillName;
        this.Description = description;
    }

    /// <summary>
    /// Throw an exception if the function is not semantic, use this method when some logic makes sense only for semantic functions.
    /// </summary>
    /// <exception cref="KernelException"></exception>
    private void VerifyIsSemantic()
    {
        if (this.IsSemantic) { return; }

        this._log.LogError("The function is not semantic");
        throw new KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a semantic function");
    }

    private static MethodDetails GetMethodDetails(
        MethodInfo methodSignature,
        object? methodContainerInstance,
        bool skAttributesRequired = true,
        ILogger? log = null)
    {
        Verify.NotNull(methodSignature);

        var result = new MethodDetails
        {
            Name = methodSignature.Name,
            Parameters = new List<ParameterView>(),
        };

        // SKFunction attribute
        SKFunctionAttribute? skFunctionAttribute = methodSignature
            .GetCustomAttributes(typeof(SKFunctionAttribute), true)
            .Cast<SKFunctionAttribute>()
            .FirstOrDefault();

        result.HasSkFunctionAttribute = skFunctionAttribute != null;

        if (!result.HasSkFunctionAttribute || skFunctionAttribute == null)
        {
            log?.LogTrace("Method '{0}' doesn't have '{1}' attribute", result.Name, nameof(SKFunctionAttribute));
            if (skAttributesRequired) { return result; }
        }
        else
        {
            result.HasSkFunctionAttribute = true;
        }

        (result.Function, bool hasStringParam) = GetDelegateInfo(methodContainerInstance, methodSignature);

        // SKFunctionName attribute
        SKFunctionNameAttribute? skFunctionNameAttribute = methodSignature
            .GetCustomAttributes(typeof(SKFunctionNameAttribute), true)
            .Cast<SKFunctionNameAttribute>()
            .FirstOrDefault();

        if (skFunctionNameAttribute != null)
        {
            result.Name = skFunctionNameAttribute.Name;
        }

        // SKFunctionInput attribute
        SKFunctionInputAttribute? skMainParam = methodSignature
            .GetCustomAttributes(typeof(SKFunctionInputAttribute), true)
            .Cast<SKFunctionInputAttribute>()
            .FirstOrDefault();

        // SKFunctionContextParameter attribute
        IList<SKFunctionContextParameterAttribute> skContextParams = methodSignature
            .GetCustomAttributes(typeof(SKFunctionContextParameterAttribute), true)
            .Cast<SKFunctionContextParameterAttribute>().ToList();

        // Handle main string param description, if available/valid
        // Note: Using [SKFunctionInput] is optional
        if (hasStringParam)
        {
            result.Parameters.Add(skMainParam != null
                ? skMainParam.ToParameterView() // Use the developer description
                : new ParameterView { Name = "input", Description = "Input string", DefaultValue = "" }); // Use a default description
        }
        else if (skMainParam != null)
        {
            // The developer used [SKFunctionInput] on a function that doesn't support a string input
            var message = $"The method '{result.Name}' doesn't have a string parameter, do not use '{nameof(SKFunctionInputAttribute)}' attribute.";
            throw new KernelException(KernelException.ErrorCodes.InvalidFunctionDescription, message);
        }

        // Handle named arg passed via the SKContext object
        // Note: "input" is added first to the list, before context params
        // Note: Using [SKFunctionContextParameter] is optional
        result.Parameters.AddRange(skContextParams.Select(x => x.ToParameterView()));

        // Check for param names conflict
        // Note: the name "input" is reserved for the main parameter
        Verify.ParametersUniqueness(result.Parameters);

        result.Description = skFunctionAttribute?.Description ?? "";

        log?.LogTrace("Method '{0}' found", result.Name);

        return result;
    }

    // Inspect a method and returns the corresponding delegate and related info
    private static (Func<ITextCompletion?, CompleteRequestSettings?, SKContext, Task<SKContext>> function, bool hasStringParam) GetDelegateInfo(object? instance, MethodInfo method)
    {
        // Get marshaling funcs for parameters
        var parameters = method.GetParameters();
        if (parameters.Length > 2)
        {
            ThrowForInvalidSignature();
        }

        var parameterFuncs = new Func<SKContext, object>[parameters.Length];
        bool hasStringParam = false;
        bool hasContextParam = false;
        for (int i = 0; i < parameters.Length; i++)
        {
            if (!hasStringParam && parameters[i].ParameterType == typeof(string))
            {
                hasStringParam = true;
                parameterFuncs[i] = static (SKContext ctx) => ctx.Variables.Input;
            }
            else if (!hasContextParam && parameters[i].ParameterType == typeof(SKContext))
            {
                hasContextParam = true;
                parameterFuncs[i] = static (SKContext ctx) => ctx;
            }
            else
            {
                ThrowForInvalidSignature();
            }
        }

        // Get marshaling func for the return value
        Func<object?, SKContext, Task<SKContext>> returnFunc;
        if (method.ReturnType == typeof(void))
        {
            returnFunc = static (result, context) => Task.FromResult(context);
        }
        else if (method.ReturnType == typeof(string))
        {
            returnFunc = static (result, context) =>
            {
                context.Variables.Update((string?)result);
                return Task.FromResult(context);
            };
        }
        else if (method.ReturnType == typeof(SKContext))
        {
            returnFunc = static (result, _) => Task.FromResult((SKContext)ThrowIfNullResult(result));
        }
        else if (method.ReturnType == typeof(Task))
        {
            returnFunc = async static (result, context) =>
            {
                await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);
                return context;
            };
        }
        else if (method.ReturnType == typeof(Task<string>))
        {
            returnFunc = async static (result, context) =>
            {
                context.Variables.Update(await ((Task<string>)ThrowIfNullResult(result)).ConfigureAwait(false));
                return context;
            };
        }
        else if (method.ReturnType == typeof(Task<SKContext>))
        {
            returnFunc = static (result, _) => (Task<SKContext>)ThrowIfNullResult(result);
        }
        else
        {
            ThrowForInvalidSignature();
        }

        // Create the func
        Func<ITextCompletion?, CompleteRequestSettings?, SKContext, Task<SKContext>> function = (_, _, context) =>
        {
            // Create the arguments.
            object[] args = parameterFuncs.Length != 0 ? new object[parameterFuncs.Length] : Array.Empty<object>();
            for (int i = 0; i < args.Length; i++)
            {
                args[i] = parameterFuncs[i](context);
            }

            // Invoke the method.
            object? result = method.Invoke(instance, args);

            // Extract and return the result.
            return returnFunc(result, context);
        };

        // Return the func and whether it has a string param
        return (function, hasStringParam);

        void ThrowForInvalidSignature() =>
            throw new KernelException(
                KernelException.ErrorCodes.FunctionTypeNotSupported,
                $"Function '{method.Name}' has an invalid signature not supported by the kernel.");

        static object ThrowIfNullResult(object? result) =>
            result ??
            throw new KernelException(
                KernelException.ErrorCodes.FunctionInvokeError,
                "Function returned null unexpectedly.");
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"{this.Name} ({this.Description})";

    #endregion
}
