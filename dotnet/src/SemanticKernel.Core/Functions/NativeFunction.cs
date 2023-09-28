// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

#pragma warning disable format

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class NativeFunction : ISKFunction, IDisposable
{
    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string PluginName { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public AIRequestSettings? RequestSettings { get; }

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IReadOnlyList<ParameterView> Parameters { get; }

    /// <summary>
    /// Create a native function instance, wrapping a native object method
    /// </summary>
    /// <param name="method">Signature of the method to invoke</param>
    /// <param name="target">Object containing the method to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromNativeMethod(
        MethodInfo method,
        object? target = null,
        string? pluginName = null,
        ILoggerFactory? loggerFactory = null)
    {
        if (!method.IsStatic && target is null)
        {
            throw new ArgumentNullException(nameof(target), "Argument cannot be null for non-static methods");
        }

        if (string.IsNullOrWhiteSpace(pluginName))
        {
            pluginName = FunctionCollection.GlobalFunctionsPluginName;
        }

        ILogger logger = loggerFactory?.CreateLogger(method.DeclaringType ?? typeof(SKFunction)) ?? NullLogger.Instance;

        MethodDetails methodDetails = GetMethodDetails(method, target, pluginName!, logger);

        return new NativeFunction(
            delegateFunction: methodDetails.Function,
            parameters: methodDetails.Parameters,
            pluginName: pluginName!,
            functionName: methodDetails.Name,
            description: methodDetails.Description,
            logger: logger);
    }

    /// <summary>
    /// Create a native function instance, wrapping a delegate function
    /// </summary>
    /// <param name="nativeFunction">Function to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="functionName">SK function name</param>
    /// <param name="description">SK function description</param>
    /// <param name="parameters">SK function parameters</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromNativeFunction(
        Delegate nativeFunction,
        string? pluginName = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<ParameterView>? parameters = null,
        ILoggerFactory? loggerFactory = null)
    {
        ILogger logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(ISKFunction)) : NullLogger.Instance;

        if (string.IsNullOrWhiteSpace(pluginName))
        {
            pluginName = FunctionCollection.GlobalFunctionsPluginName;
        }

        MethodDetails methodDetails = GetMethodDetails(nativeFunction.Method, nativeFunction.Target, pluginName!, logger);

        functionName ??= methodDetails.Name;
        parameters ??= methodDetails.Parameters;
        description ??= methodDetails.Description;

        return new NativeFunction(
            delegateFunction: methodDetails.Function,
            parameters: parameters.ToList(),
            description: description,
            pluginName: pluginName!,
            functionName: functionName,
            logger: logger);
    }

    /// <inheritdoc/>
    public FunctionView Describe()
        => this._view.Value;

    /// <inheritdoc/>
    public async Task<FunctionResult> InvokeAsync(
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            return await this._function(null, requestSettings, context, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            this._logger.LogError(e, "Native function {Plugin}.{Name} execution failed with error {Error}", this.PluginName, this.Name, e.Message);
            throw;
        }
    }

    /// <inheritdoc/>
    public ISKFunction SetDefaultFunctionCollection(IReadOnlyFunctionCollection functions)
    {
        // No-op for native functions; do not throw, as both Plan and PromptFunctions use this,
        // and we don't have a way to distinguish between a native function and a Plan.
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        this.ThrowNotSemantic();
        return this;
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(AIRequestSettings? requestSettings)
    {
        this.ThrowNotSemantic();
        return this;
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
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
    private readonly NativeFunctionDelegate _function;
    private readonly ILogger _logger;

    private struct MethodDetails
    {
        public NativeFunctionDelegate Function { get; set; }
        public List<ParameterView> Parameters { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
    }

    private static async Task<string> GetCompletionsResultContentAsync(IReadOnlyList<ITextResult> completions, CancellationToken cancellationToken = default)
    {
        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        return await completions[0].GetCompletionAsync(cancellationToken).ConfigureAwait(false);
    }

    internal NativeFunction(
        NativeFunctionDelegate delegateFunction,
        IReadOnlyList<ParameterView> parameters,
        string pluginName,
        string functionName,
        string description,
        ILogger logger)
    {
        Verify.NotNull(delegateFunction);
        Verify.ValidPluginName(pluginName);
        Verify.ValidFunctionName(functionName);

        this._logger = logger;

        this._function = delegateFunction;
        this.Parameters = parameters.ToArray();
        Verify.ParametersUniqueness(this.Parameters);

        this.Name = functionName;
        this.PluginName = pluginName;
        this.Description = description;

        this._view = new(() => new (functionName, pluginName, description) { Parameters = this.Parameters });
    }

    /// <summary>
    /// Throw an exception if the function is not semantic, use this method when some logic makes sense only for semantic functions.
    /// </summary>
    /// <exception cref="SKException"></exception>
    [DoesNotReturn]
    private void ThrowNotSemantic()
    {
        this._logger.LogError("The function is not semantic");
        throw new SKException("Invalid operation, the method requires a semantic function");
    }

    private static MethodDetails GetMethodDetails(
        MethodInfo method,
        object? target,
        string pluginName,
        ILogger? logger = null)
    {
        Verify.NotNull(method);

        // Get the name to use for the function.  If the function has an SKName attribute, we use that.
        // Otherwise, we use the name of the method, but strip off any "Async" suffix if it's {Value}Task-returning.
        // We don't apply any heuristics to the value supplied by SKName so that it can always be used
        // as a definitive override.
        string? functionName = method.GetCustomAttribute<SKNameAttribute>(inherit: true)?.Name?.Trim();
        if (string.IsNullOrEmpty(functionName))
        {
            functionName = SanitizeMetadataName(method.Name!);
            Verify.ValidFunctionName(functionName);

            if (IsAsyncMethod(method) &&
                functionName.EndsWith("Async", StringComparison.Ordinal) &&
                functionName.Length > "Async".Length)
            {
                functionName = functionName.Substring(0, functionName.Length - "Async".Length);
            }
        }

        SKFunctionAttribute? functionAttribute = method.GetCustomAttribute<SKFunctionAttribute>(inherit: true);

        string? description = method.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description;

        var result = new MethodDetails
        {
            Name = functionName!,
            Description = description ?? string.Empty,
        };

        (result.Function, result.Parameters) = GetDelegateInfo(functionName!, pluginName, target, method);

        logger?.LogTrace("Method '{0}' found", result.Name);

        return result;
    }

    /// <summary>Gets whether a method has a known async return type.</summary>
    private static bool IsAsyncMethod(MethodInfo method)
    {
        Type t = method.ReturnType;

        if (t == typeof(Task) || t == typeof(ValueTask))
        {
            return true;
        }

        if (t.IsGenericType)
        {
            t = t.GetGenericTypeDefinition();
            if (t == typeof(Task<>) || t == typeof(ValueTask<>))
            {
                return true;
            }
        }

        return false;
    }

    // Inspect a method and returns the corresponding delegate and related info
    private static (NativeFunctionDelegate function, List<ParameterView>) GetDelegateInfo(
        string functionName,
        string pluginName,
        object? instance,
        MethodInfo method)
    {
        ThrowForInvalidSignatureIf(method.IsGenericMethodDefinition, method, "Generic methods are not supported");

        var stringParameterViews = new List<ParameterView>();
        var parameters = method.GetParameters();

        // Get marshaling funcs for parameters and build up the parameter views.
        var parameterFuncs = new Func<SKContext, CancellationToken, object?>[parameters.Length];
        bool sawFirstParameter = false, hasSKContextParam = false, hasCancellationTokenParam = false, hasLoggerParam = false, hasMemoryParam = false, hasCultureParam = false;
        for (int i = 0; i < parameters.Length; i++)
        {
            (parameterFuncs[i], ParameterView? parameterView) = GetParameterMarshalerDelegate(
                method, parameters[i],
                ref sawFirstParameter, ref hasSKContextParam, ref hasCancellationTokenParam, ref hasLoggerParam, ref hasMemoryParam, ref hasCultureParam);
            if (parameterView is not null)
            {
                stringParameterViews.Add(parameterView);
            }
        }

        // Get marshaling func for the return value.
        Func<string, string, object?, SKContext, Task<FunctionResult>> returnFunc = GetReturnValueMarshalerDelegate(method);

        // Create the func
        Task<FunctionResult> Function(ITextCompletion? text, AIRequestSettings? requestSettings, SKContext context, CancellationToken cancellationToken)
        {
            // Create the arguments.
            object?[] args = parameterFuncs.Length != 0 ? new object?[parameterFuncs.Length] : Array.Empty<object?>();
            for (int i = 0; i < args.Length; i++)
            {
                args[i] = parameterFuncs[i](context, cancellationToken);
            }

            // Invoke the method.
            object? result = method.Invoke(instance, args);

            // Extract and return the result.
            return returnFunc(functionName, pluginName, result, context);
        }

        // Check for param names conflict
        Verify.ParametersUniqueness(stringParameterViews);

        // Return the function and its parameter views.
        return (Function, stringParameterViews);
    }

    /// <summary>
    /// Gets a delegate for handling the marshaling of a parameter.
    /// </summary>
    private static (Func<SKContext, CancellationToken, object?>, ParameterView?) GetParameterMarshalerDelegate(
        MethodInfo method, ParameterInfo parameter,
        ref bool sawFirstParameter, ref bool hasSKContextParam, ref bool hasCancellationTokenParam, ref bool hasLoggerParam, ref bool hasMemoryParam, ref bool hasCultureParam)
    {
        Type type = parameter.ParameterType;

        // Handle special types based on SKContext data. These can each show up at most once in the method signature,
        // with the SKContext itself or the primary data from it mapped directly into the method's parameter.
        // They do not get parameter views as they're not supplied from context variables.

        if (type == typeof(SKContext))
        {
            TrackUniqueParameterType(ref hasSKContextParam, method, $"At most one {nameof(SKContext)} parameter is permitted.");
            return (static (SKContext context, CancellationToken _) => context, null);
        }

        if (type == typeof(ILogger) || type == typeof(ILoggerFactory))
        {
            TrackUniqueParameterType(ref hasLoggerParam, method, $"At most one {nameof(ILogger)}/{nameof(ILoggerFactory)} parameter is permitted.");
            return type == typeof(ILogger) ?
                ((SKContext context, CancellationToken _) => context.LoggerFactory.CreateLogger(method?.DeclaringType ?? typeof(SKFunction)), null) :
                ((SKContext context, CancellationToken _) => context.LoggerFactory, null);
        }

        if (type == typeof(CultureInfo) || type == typeof(IFormatProvider))
        {
            TrackUniqueParameterType(ref hasCultureParam, method, $"At most one {nameof(CultureInfo)}/{nameof(IFormatProvider)} parameter is permitted.");
            return (static (SKContext context, CancellationToken _) => context.Culture, null);
        }

        if (type == typeof(CancellationToken))
        {
            TrackUniqueParameterType(ref hasCancellationTokenParam, method, $"At most one {nameof(CancellationToken)} parameter is permitted.");
            return (static (SKContext _, CancellationToken cancellationToken) => cancellationToken, null);
        }

        // Handle context variables. These are supplied from the SKContext's Variables dictionary.

        if (!type.IsByRef && GetParser(type) is Func<string, CultureInfo, object> parser)
        {
            // Use either the parameter's name or an override from an applied SKName attribute.
            SKNameAttribute? nameAttr = parameter.GetCustomAttribute<SKNameAttribute>(inherit: true);
            string name = nameAttr?.Name?.Trim() ?? SanitizeMetadataName(parameter.Name);
            bool nameIsInput = name.Equals("input", StringComparison.OrdinalIgnoreCase);
            ThrowForInvalidSignatureIf(name.Length == 0, method, $"Parameter {parameter.Name}'s context attribute defines an invalid name.");
            ThrowForInvalidSignatureIf(sawFirstParameter && nameIsInput, method, "Only the first parameter may be named 'input'");

            // Use either the parameter's optional default value as contained in parameter metadata (e.g. `string s = "hello"`)
            // or an override from an applied SKParameter attribute. Note that a default value may be null.
            DefaultValueAttribute defaultValueAttribute = parameter.GetCustomAttribute<DefaultValueAttribute>(inherit: true);
            bool hasDefaultValue = defaultValueAttribute is not null;
            object? defaultValue = defaultValueAttribute?.Value;
            if (!hasDefaultValue && parameter.HasDefaultValue)
            {
                hasDefaultValue = true;
                defaultValue = parameter.DefaultValue;
            }

            if (hasDefaultValue)
            {
                // If we got a default value, make sure it's of the right type. This currently supports
                // null values if the target type is a reference type or a Nullable<T>, strings,
                // anything that can be parsed from a string via a registered TypeConverter,
                // and a value that's already the same type as the parameter.
                if (defaultValue is string defaultStringValue && defaultValue.GetType() != typeof(string))
                {
                    // Invariant culture is used here as this value comes from the C# source
                    // and it should be deterministic across cultures.
                    defaultValue = parser(defaultStringValue, CultureInfo.InvariantCulture);
                }
                else
                {
                    ThrowForInvalidSignatureIf(
                        defaultValue is null && type.IsValueType && Nullable.GetUnderlyingType(type) is null,
                        method,
                        $"Type {type} is a non-nullable value type but a null default value was specified.");
                    ThrowForInvalidSignatureIf(
                        defaultValue is not null && !type.IsAssignableFrom(defaultValue.GetType()),
                        method,
                        $"Default value {defaultValue} for parameter {name} is not assignable to type {type}.");
                }
            }

            bool fallBackToInput = !sawFirstParameter && !nameIsInput;
            object? parameterFunc(SKContext context, CancellationToken _)
            {
                // 1. Use the value of the variable if it exists.
                if (context.Variables.TryGetValue(name, out string? value))
                {
                    return Process(value);
                }

                // 2. Otherwise, use the default value if there is one, sourced either from an attribute or the parameter's default.
                if (hasDefaultValue)
                {
                    return defaultValue;
                }

                // 3. Otherwise, use "input" if this is the first (or only) parameter.
                if (fallBackToInput)
                {
                    return Process(context.Variables.Input);
                }

                // 4. Otherwise, fail.
                throw new SKException($"Missing value for parameter '{name}'",
                    new ArgumentException("Missing value function parameter", name));

                object ? Process(string value)
                {
                    if (type == typeof(string))
                    {
                        return value;
                    }

                    try
                    {
                        return parser(value, context.Culture);
                    }
                    catch (Exception e) when (!e.IsCriticalException())
                    {
                        throw new ArgumentOutOfRangeException(name, value, e.Message);
                    }
                }
            }

            sawFirstParameter = true;

            var parameterView = new ParameterView(
                name,
                parameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description ?? string.Empty,
                defaultValue?.ToString() ?? string.Empty);

            return (parameterFunc, parameterView);
        }

        // Fail for unknown parameter types.
        throw GetExceptionForInvalidSignature(method, $"Unknown parameter type {parameter.ParameterType}");
    }

    /// <summary>
    /// Gets a delegate for handling the result value of a method, converting it into the <see cref="Task{SKContext}"/> to return from the invocation.
    /// </summary>
    private static Func<string, string, object?, SKContext, Task<FunctionResult>> GetReturnValueMarshalerDelegate(MethodInfo method)
    {
        // Handle each known return type for the method
        Type returnType = method.ReturnType;

        // No return value, either synchronous (void) or asynchronous (Task / ValueTask).

        if (returnType == typeof(void))
        {
            return static (functionName, pluginName, result, context) =>
                Task.FromResult(new FunctionResult(functionName, pluginName, context));
        }

        if (returnType == typeof(Task))
        {
            return async static (functionName, pluginName, result, context) =>
            {
                await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(functionName, pluginName, context);
            };
        }

        if (returnType == typeof(ValueTask))
        {
            return async static (functionName, pluginName, result, context) =>
            {
                await ((ValueTask)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(functionName, pluginName, context);
            };
        }

        // SKContext, either synchronous (SKContext) or asynchronous (Task<SKContext> / ValueTask<SKContext>).

        if (returnType == typeof(SKContext))
        {
            return static (functionName, pluginName, result, _) =>
            {
                var context = (SKContext)ThrowIfNullResult(result);
                return Task.FromResult(new FunctionResult(functionName, pluginName, context, context.Result));
            };
        }

        if (returnType == typeof(Task<SKContext>))
        {
            return static async (functionName, pluginName, result, _) =>
            {
                var context = await ((Task<SKContext>)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(functionName, pluginName, context, context.Result);
            };
        }

        if (returnType == typeof(ValueTask<SKContext>))
        {
            return static async (functionName, pluginName, result, _) =>
            {
                var context = await ((ValueTask<SKContext>)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(functionName, pluginName, context, context);
            };
        }

        // string (which is special as no marshaling is required), either synchronous (string) or asynchronous (Task<string> / ValueTask<string>)

        if (returnType == typeof(string))
        {
            return static (functionName, pluginName, result, context) =>
            {
                var resultString = (string?)result;
                context.Variables.Update(resultString);
                return Task.FromResult(new FunctionResult(functionName, pluginName, context, resultString));
            };
        }

        if (returnType == typeof(Task<string>))
        {
            return async static (functionName, pluginName, result, context) =>
            {
                var resultString = await ((Task<string>)ThrowIfNullResult(result)).ConfigureAwait(false);
                context.Variables.Update(resultString);
                return new FunctionResult(functionName, pluginName, context, resultString);
            };
        }

        if (returnType == typeof(ValueTask<string>))
        {
            return async static (functionName, pluginName, result, context) =>
            {
                var resultString = await ((ValueTask<string>)ThrowIfNullResult(result)).ConfigureAwait(false);
                context.Variables.Update(resultString);
                return new FunctionResult(functionName, pluginName, context, resultString);
            };
        }

        // All other synchronous return types T.

        if (!returnType.IsGenericType || returnType.GetGenericTypeDefinition() == typeof(Nullable<>))
        {
            if (GetFormatter(returnType) is not Func<object?, CultureInfo, string> formatter)
            {
                throw GetExceptionForInvalidSignature(method, $"Unknown return type {returnType}");
            }

            return (functionName, pluginName, result, context) =>
            {
                context.Variables.Update(formatter(result, context.Culture));
                return Task.FromResult(new FunctionResult(functionName, pluginName, context, result));
            };
        }

        // All other asynchronous return types

        // Task<T>
        if (returnType.GetGenericTypeDefinition() is Type genericTask &&
            genericTask == typeof(Task<>) &&
            returnType.GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)?.GetGetMethod() is MethodInfo taskResultGetter &&
            GetFormatter(taskResultGetter.ReturnType) is Func<object?, CultureInfo, string> taskResultFormatter)
        {
            return async (functionName, pluginName, result, context) =>
            {
                await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);

                var taskResult = taskResultGetter.Invoke(result!, Array.Empty<object>());

                context.Variables.Update(taskResultFormatter(taskResult, context.Culture));
                return new FunctionResult(functionName, pluginName, context, taskResult);
            };
        }

        // ValueTask<T>
        if (returnType.GetGenericTypeDefinition() is Type genericValueTask &&
            genericValueTask == typeof(ValueTask<>) &&
            returnType.GetMethod("AsTask", BindingFlags.Public | BindingFlags.Instance) is MethodInfo valueTaskAsTask &&
            valueTaskAsTask.ReturnType.GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)?.GetGetMethod() is MethodInfo asTaskResultGetter &&
            GetFormatter(asTaskResultGetter.ReturnType) is Func<object?, CultureInfo, string> asTaskResultFormatter)
        {
            return async (functionName, pluginName, result, context) =>
            {
                Task task = (Task)valueTaskAsTask.Invoke(ThrowIfNullResult(result), Array.Empty<object>());
                await task.ConfigureAwait(false);

                var taskResult = asTaskResultGetter.Invoke(task!, Array.Empty<object>());

                context.Variables.Update(asTaskResultFormatter(taskResult, context.Culture));
                return new FunctionResult(functionName, pluginName, context, taskResult);
            };
        }

        // IAsyncEnumerable<T>
        if (returnType.GetGenericTypeDefinition() is Type genericAsyncEnumerable && genericAsyncEnumerable == typeof(IAsyncEnumerable<>))
        {
            Type elementType = returnType.GetGenericArguments()[0];

            MethodInfo getAsyncEnumeratorMethod = typeof(IAsyncEnumerable<>)
                .MakeGenericType(elementType)
                .GetMethod("GetAsyncEnumerator");

            if (getAsyncEnumeratorMethod is not null)
            {
                return (functionName, pluginName, result, context) =>
                {
                    var asyncEnumerator = getAsyncEnumeratorMethod.Invoke(result, new object[] { default(CancellationToken) });

                    if (asyncEnumerator is not null)
                    {
                        return Task.FromResult(new FunctionResult(functionName, pluginName, context, asyncEnumerator));
                    }

                    return Task.FromResult(new FunctionResult(functionName, pluginName, context));
                };
            }
        }

        // Unrecognized return type.
        throw GetExceptionForInvalidSignature(method, $"Unknown return type {returnType}");

        // Throws an exception if a result is found to be null unexpectedly
        static object ThrowIfNullResult(object? result) =>
            result ??
            throw new SKException("Function returned null unexpectedly.");
    }

    /// <summary>Gets an exception that can be thrown indicating an invalid signature.</summary>
    [DoesNotReturn]
    private static Exception GetExceptionForInvalidSignature(MethodInfo method, string reason) =>
        throw new SKException($"Function '{method.Name}' is not supported by the kernel. {reason}");

    /// <summary>Throws an exception indicating an invalid SKFunction signature if the specified condition is not met.</summary>
    private static void ThrowForInvalidSignatureIf([DoesNotReturnIf(true)] bool condition, MethodInfo method, string reason)
    {
        if (condition)
        {
            throw GetExceptionForInvalidSignature(method, reason);
        }
    }

    /// <summary>Tracks whether a particular kind of parameter has been seen, throwing an exception if it has, and marking it as seen if it hasn't</summary>
    private static void TrackUniqueParameterType(ref bool hasParameterType, MethodInfo method, string failureMessage)
    {
        ThrowForInvalidSignatureIf(hasParameterType, method, failureMessage);
        hasParameterType = true;
    }

    /// <summary>
    /// Gets a TypeConverter-based parser for parsing a string as the target type.
    /// </summary>
    /// <param name="targetType">Specifies the target type into which a string should be parsed.</param>
    /// <returns>The parsing function if the target type is supported; otherwise, null.</returns>
    /// <remarks>
    /// The parsing function uses whatever TypeConverter is registered for the target type.
    /// Parsing is first attempted using the current culture, and if that fails, it tries again
    /// with the invariant culture. If both fail, an exception is thrown.
    /// </remarks>
    private static Func<string, CultureInfo, object?>? GetParser(Type targetType) =>
        s_parsers.GetOrAdd(targetType, static targetType =>
        {
            // Strings just parse to themselves.
            if (targetType == typeof(string))
            {
                return (input, cultureInfo) => input;
            }

            // For nullables, parse as the inner type.  We then just need to be careful to treat null as null,
            // as the underlying parser might not be expecting null.
            bool wasNullable = false;
            if (targetType.IsGenericType && targetType.GetGenericTypeDefinition() == typeof(Nullable<>))
            {
                wasNullable = true;
                targetType = Nullable.GetUnderlyingType(targetType);
            }

            // For enums, delegate to Enum.Parse, special-casing null if it was actually Nullable<EnumType>.
            if (targetType.IsEnum)
            {
                return (input, cultureInfo) =>
                {
                    if (wasNullable && input is null)
                    {
                        return null!;
                    }

                    return Enum.Parse(targetType, input, ignoreCase: true);
                };
            }

            // Finally, look up and use a type converter.  Again, special-case null if it was actually Nullable<T>.
            if (GetTypeConverter(targetType) is TypeConverter converter && converter.CanConvertFrom(typeof(string)))
            {
                return (input, cultureInfo) =>
                {
                    if (wasNullable && input is null)
                    {
                        return null!;
                    }

                    // First try to parse using the supplied culture (or current if none was supplied).
                    // If that fails, try with the invariant culture and allow any exception to propagate.
                    try
                    {
                        return converter.ConvertFromString(context: null, cultureInfo, input);
                    }
                    catch (Exception e) when (!e.IsCriticalException() && cultureInfo != CultureInfo.InvariantCulture)
                    {
                        return converter.ConvertFromInvariantString(input);
                    }
                };
            }

            // Unsupported type.
            return null;
        });

    /// <summary>
    /// Gets a TypeConverter-based formatter for formatting an object as a string.
    /// </summary>
    /// <remarks>
    /// Formatting is performed in the invariant culture whenever possible.
    /// </remarks>
    private static Func<object?, CultureInfo, string?>? GetFormatter(Type targetType) =>
        s_formatters.GetOrAdd(targetType, static targetType =>
        {
            // For nullables, render as the underlying type.
            bool wasNullable = false;
            if (targetType.IsGenericType && targetType.GetGenericTypeDefinition() == typeof(Nullable<>))
            {
                wasNullable = true;
                targetType = Nullable.GetUnderlyingType(targetType);
            }

            // For enums, just ToString() and allow the object override to do the right thing.
            if (targetType.IsEnum)
            {
                return (input, cultureInfo) => input?.ToString()!;
            }

            // Strings just render as themselves.
            if (targetType == typeof(string))
            {
                return (input, cultureInfo) => (string)input!;
            }

            // Finally, look up and use a type converter.
            if (GetTypeConverter(targetType) is TypeConverter converter && converter.CanConvertTo(typeof(string)))
            {
                return (input, cultureInfo) =>
                {
                    if (wasNullable && input is null)
                    {
                        return null!;
                    }

                    return converter.ConvertToString(context: null, cultureInfo, input);
                };
            }

            return null;
        });

    private static TypeConverter? GetTypeConverter(Type targetType)
    {
        // In an ideal world, this would use TypeDescriptor.GetConverter. However, that is not friendly to
        // any form of ahead-of-time compilation, as it could end up requiring functionality that was trimmed.
        // Instead, we just use a hard-coded set of converters for the types we know about and then also support
        // types that are explicitly attributed with TypeConverterAttribute.

        if (targetType == typeof(byte)) { return new ByteConverter(); }
        if (targetType == typeof(sbyte)) { return new SByteConverter(); }
        if (targetType == typeof(bool)) { return new BooleanConverter(); }
        if (targetType == typeof(ushort)) { return new UInt16Converter(); }
        if (targetType == typeof(short)) { return new Int16Converter(); }
        if (targetType == typeof(char)) { return new CharConverter(); }
        if (targetType == typeof(uint)) { return new UInt32Converter(); }
        if (targetType == typeof(int)) { return new Int32Converter(); }
        if (targetType == typeof(ulong)) { return new UInt64Converter(); }
        if (targetType == typeof(long)) { return new Int64Converter(); }
        if (targetType == typeof(float)) { return new SingleConverter(); }
        if (targetType == typeof(double)) { return new DoubleConverter(); }
        if (targetType == typeof(decimal)) { return new DecimalConverter(); }
        if (targetType == typeof(TimeSpan)) { return new TimeSpanConverter(); }
        if (targetType == typeof(DateTime)) { return new DateTimeConverter(); }
        if (targetType == typeof(DateTimeOffset)) { return new DateTimeOffsetConverter(); }
        if (targetType == typeof(Uri)) { return new UriTypeConverter(); }
        if (targetType == typeof(Guid)) { return new GuidConverter(); }

        if (targetType.GetCustomAttribute<TypeConverterAttribute>() is TypeConverterAttribute tca &&
            Type.GetType(tca.ConverterTypeName, throwOnError: false) is Type converterType &&
            Activator.CreateInstance(converterType) is TypeConverter converter)
        {
            return converter;
        }

        return null;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"{this.Name} ({this.Description})";

    /// <summary>
    /// Remove characters from method name that are valid in metadata but invalid for SK.
    /// </summary>
    private static string SanitizeMetadataName(string methodName) =>
        s_invalidNameCharsRegex.Replace(methodName, "_");

    /// <summary>Regex that flags any character other than ASCII digits or letters or the underscore.</summary>
    private static readonly Regex s_invalidNameCharsRegex = new("[^0-9A-Za-z_]");

    /// <summary>Parser functions for converting strings to parameter types.</summary>
    private static readonly ConcurrentDictionary<Type, Func<string, CultureInfo, object>?> s_parsers = new();

    /// <summary>Formatter functions for converting parameter types to strings.</summary>
    private static readonly ConcurrentDictionary<Type, Func<object?, CultureInfo, string>?> s_formatters = new();

    private readonly Lazy<FunctionView> _view;

    #endregion

    #region Obsolete

    /// <inheritdoc/>
    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.PluginName instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string SkillName => this.PluginName;

    /// <inheritdoc/>
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool IsSemantic => true;

    /// <inheritdoc/>
    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.SetDefaultFunctionCollection instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction SetDefaultSkillCollection(IReadOnlyFunctionCollection skills) => this.SetDefaultFunctionCollection(skills);

    #endregion
}
