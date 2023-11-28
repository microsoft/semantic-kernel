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
using System.Runtime.CompilerServices;
using System.Runtime.ExceptionServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Text;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides factory methods for creating <see cref="KernelFunction"/> instances backed by a .NET method.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed class KernelFunctionFromMethod : KernelFunction
{
    /// <summary>
    /// Creates an <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunction Create(
        MethodInfo method,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(method);
        if (!method.IsStatic && target is null)
        {
            throw new ArgumentNullException(nameof(target), "Target must not be null for an instance method.");
        }

        ILogger logger = loggerFactory?.CreateLogger(method.DeclaringType ?? typeof(KernelFunctionFromPrompt)) ?? NullLogger.Instance;

        MethodDetails methodDetails = GetMethodDetails(functionName, method, target, logger);
        var result = new KernelFunctionFromMethod(
            methodDetails.Function,
            methodDetails.Name,
            description ?? methodDetails.Description,
            parameters?.ToList() ?? methodDetails.Parameters,
            returnParameter ?? methodDetails.ReturnParameter,
            logger);

        if (logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Created ISKFunction '{Name}' for '{MethodName}'", result.Name, method.Name);
        }

        return result;
    }

    /// <inheritdoc/>
    protected override async Task<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        ContextVariables variables,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        return await this._function(null, executionSettings, kernel, variables, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    protected override async IAsyncEnumerable<T> InvokeCoreStreamingAsync<T>(
        Kernel kernel,
        ContextVariables variables,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var functionResult = await this.InvokeCoreAsync(kernel, variables, executionSettings, cancellationToken).ConfigureAwait(false);
        if (functionResult.Value is T)
        {
            yield return (T)functionResult.Value;
            yield break;
        }

        // Supports the following provided T types for Method streaming
        if (typeof(T) == typeof(StreamingContent) ||
            typeof(T) == typeof(StreamingMethodContent))
        {
            if (functionResult.Value is not null)
            {
                yield return (T)(object)new StreamingMethodContent(functionResult.Value);
            }
            yield break;
        }

        throw new NotSupportedException($"Streaming function {this.Name} does not support type {typeof(T)}");

        // We don't invoke the hook here as the InvokeCoreAsync will do that for us
    }

    /// <summary>
    /// JSON serialized string representation of the function.
    /// </summary>
    public override string ToString() => JsonSerializer.Serialize(this, JsonOptionsCache.WriteIndented);

    #region private

    /// <summary>Delegate used to invoke the underlying delegate.</summary>
    private delegate ValueTask<FunctionResult> ImplementationFunc(
        ITextCompletion? textCompletion,
        PromptExecutionSettings? executionSettings,
        Kernel kernel,
        ContextVariables variables,
        CancellationToken cancellationToken);

    private static readonly object[] s_cancellationTokenNoneArray = new object[] { CancellationToken.None };
    private readonly ImplementationFunc _function;
    private readonly ILogger _logger;

    private record struct MethodDetails(string Name, string Description, ImplementationFunc Function, List<KernelParameterMetadata> Parameters, KernelReturnParameterMetadata ReturnParameter);

    private KernelFunctionFromMethod(
        ImplementationFunc implementationFunc,
        string functionName,
        string description,
        IReadOnlyList<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter,
        ILogger logger) : base(functionName, description, parameters, returnParameter)
    {
        Verify.ValidFunctionName(functionName);

        this._logger = logger;

        this._function = implementationFunc;
    }

    private static MethodDetails GetMethodDetails(string? functionName, MethodInfo method, object? target, ILogger logger)
    {
        ThrowForInvalidSignatureIf(method.IsGenericMethodDefinition, method, "Generic methods are not supported");

        if (functionName is null)
        {
            // Get the name to use for the function.  If the function has an SKName attribute, we use that.
            // Otherwise, we use the name of the method, but strip off any "Async" suffix if it's {Value}Task-returning.
            // We don't apply any heuristics to the value supplied by SKName so that it can always be used
            // as a definitive override.
            functionName = method.GetCustomAttribute<KernelNameAttribute>(inherit: true)?.Name?.Trim();
            if (string.IsNullOrEmpty(functionName))
            {
                functionName = SanitizeMetadataName(method.Name!);

                if (IsAsyncMethod(method) &&
                    functionName.EndsWith("Async", StringComparison.Ordinal) &&
                    functionName.Length > "Async".Length)
                {
                    functionName = functionName.Substring(0, functionName.Length - "Async".Length);
                }
            }
        }

        Verify.ValidFunctionName(functionName);

        List<KernelParameterMetadata> stringParameterViews = new();
        var parameters = method.GetParameters();

        // Get marshaling funcs for parameters and build up the parameter metadata.
        var parameterFuncs = new Func<Kernel, ContextVariables, CancellationToken, object?>[parameters.Length];
        bool sawFirstParameter = false, hasKernelParam = false, hasContextVariablesParam = false, hasCancellationTokenParam = false, hasLoggerParam = false, hasMemoryParam = false, hasCultureParam = false;
        for (int i = 0; i < parameters.Length; i++)
        {
            (parameterFuncs[i], KernelParameterMetadata? parameterView) = GetParameterMarshalerDelegate(
                method, parameters[i],
                ref sawFirstParameter, ref hasKernelParam, ref hasContextVariablesParam, ref hasCancellationTokenParam, ref hasLoggerParam, ref hasMemoryParam, ref hasCultureParam);
            if (parameterView is not null)
            {
                stringParameterViews.Add(parameterView);
            }
        }

        // Check for param names conflict
        Verify.ParametersUniqueness(stringParameterViews);

        // Get marshaling func for the return value.
        Func<string, object?, ContextVariables, Kernel, ValueTask<FunctionResult>> returnFunc = GetReturnValueMarshalerDelegate(method);

        // Create the func
        ValueTask<FunctionResult> Function(ITextCompletion? text, PromptExecutionSettings? executionSettings, Kernel kernel, ContextVariables variables, CancellationToken cancellationToken)
        {
            // Create the arguments.
            object?[] args = parameterFuncs.Length != 0 ? new object?[parameterFuncs.Length] : Array.Empty<object?>();
            for (int i = 0; i < args.Length; i++)
            {
                args[i] = parameterFuncs[i](kernel, variables, cancellationToken);
            }

            // Invoke the method.
            object? result = Invoke(method, target, args);

            // Extract and return the result.
            return returnFunc(functionName!, result, variables, kernel);
        }

        // And return the details.
        return new MethodDetails
        {
            Function = Function,
            Name = functionName!,
            Description = method.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description ?? "",
            Parameters = stringParameterViews,
            ReturnParameter = new KernelReturnParameterMetadata()
            {
                Description = method.ReturnParameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description,
                ParameterType = method.ReturnType,
            }
        };
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
            if (t == typeof(Task<>) || t == typeof(ValueTask<>) || t == typeof(IAsyncEnumerable<>))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Gets a delegate for handling the marshaling of a parameter.
    /// </summary>
    private static (Func<Kernel, ContextVariables, CancellationToken, object?>, KernelParameterMetadata?) GetParameterMarshalerDelegate(
        MethodInfo method, ParameterInfo parameter,
        ref bool sawFirstParameter, ref bool hasKernelParam, ref bool hasContextVariablesParam, ref bool hasCancellationTokenParam, ref bool hasLoggerParam, ref bool hasMemoryParam, ref bool hasCultureParam)
    {
        Type type = parameter.ParameterType;

        // Handle special types based on ContextVariables data. These can each show up at most once in the method signature,
        // with the Kernel or/and the ContextVariables itself or the primary data from it mapped directly into the method's parameter.
        // They do not get parameter metadata as they're not supplied from context variables.

        if (type == typeof(Kernel))
        {
            TrackUniqueParameterType(ref hasKernelParam, method, $"At most one {nameof(Kernel)} parameter is permitted.");
            return (static (Kernel kernel, ContextVariables variables, CancellationToken _) => kernel, null);
        }

        if (type == typeof(ContextVariables))
        {
            TrackUniqueParameterType(ref hasContextVariablesParam, method, $"At most one {nameof(ContextVariables)} parameter is permitted.");
            return (static (Kernel kernel, ContextVariables variables, CancellationToken _) => variables, null);
        }

        if (type == typeof(ILogger) || type == typeof(ILoggerFactory))
        {
            TrackUniqueParameterType(ref hasLoggerParam, method, $"At most one {nameof(ILogger)}/{nameof(ILoggerFactory)} parameter is permitted.");
            return type == typeof(ILogger) ?
                ((Kernel kernel, ContextVariables context, CancellationToken _) => kernel.LoggerFactory.CreateLogger(method?.DeclaringType ?? typeof(KernelFunctionFromPrompt)), null) :
                ((Kernel kernel, ContextVariables context, CancellationToken _) => kernel.LoggerFactory, null);
        }

        if (type == typeof(CultureInfo) || type == typeof(IFormatProvider))
        {
            TrackUniqueParameterType(ref hasCultureParam, method, $"At most one {nameof(CultureInfo)}/{nameof(IFormatProvider)} parameter is permitted.");
            return (static (Kernel kernel, ContextVariables context, CancellationToken _) => kernel.Culture, null);
        }

        if (type == typeof(CancellationToken))
        {
            TrackUniqueParameterType(ref hasCancellationTokenParam, method, $"At most one {nameof(CancellationToken)} parameter is permitted.");
            return (static (Kernel kernel, ContextVariables _, CancellationToken cancellationToken) => cancellationToken, null);
        }

        // Handle context variables. These are supplied from the SKContext's Variables dictionary.

        if (!type.IsByRef && GetParser(type) is Func<string, CultureInfo, object> parser)
        {
            // Use either the parameter's name or an override from an applied SKName attribute.
            KernelNameAttribute? nameAttr = parameter.GetCustomAttribute<KernelNameAttribute>(inherit: true);
            string name = nameAttr?.Name?.Trim() ?? SanitizeMetadataName(parameter.Name ?? "");
            bool nameIsInput = name.Equals("input", StringComparison.OrdinalIgnoreCase);
            ThrowForInvalidSignatureIf(name.Length == 0, method, $"Parameter {parameter.Name}'s context attribute defines an invalid name.");
            ThrowForInvalidSignatureIf(sawFirstParameter && nameIsInput, method, "Only the first parameter may be named 'input'");

            // Use either the parameter's optional default value as contained in parameter metadata (e.g. `string s = "hello"`)
            // or an override from an applied SKParameter attribute. Note that a default value may be null.
            DefaultValueAttribute? defaultValueAttribute = parameter.GetCustomAttribute<DefaultValueAttribute>(inherit: true);
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
            object? parameterFunc(Kernel kernel, ContextVariables variables, CancellationToken _)
            {
                // 1. Use the value of the variable if it exists.
                if (variables.TryGetValue(name, out string? value))
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
                    return Process(variables.Input);
                }

                // 4. Otherwise, fail.
                throw new KernelException($"Missing value for parameter '{name}'",
                    new ArgumentException("Missing value function parameter", name));

                object? Process(string value)
                {
                    if (type == typeof(string))
                    {
                        return value;
                    }

                    try
                    {
                        return parser(value, kernel.Culture);
                    }
                    catch (Exception e) when (!e.IsCriticalException())
                    {
                        throw new ArgumentOutOfRangeException(name, value, e.Message);
                    }
                }
            }

            sawFirstParameter = true;

            var parameterView = new KernelParameterMetadata(name)
            {
                Description = parameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description,
                DefaultValue = defaultValue?.ToString(),
                IsRequired = !parameter.IsOptional,
                ParameterType = type
            };

            return (parameterFunc, parameterView);
        }

        // Fail for unknown parameter types.
        throw GetExceptionForInvalidSignature(method, $"Unknown parameter type {parameter.ParameterType}");
    }

    /// <summary>
    /// Gets a delegate for handling the result value of a method, converting it into the <see cref="Task{SKContext}"/> to return from the invocation.
    /// </summary>
    private static Func<string, object?, ContextVariables, Kernel, ValueTask<FunctionResult>> GetReturnValueMarshalerDelegate(MethodInfo method)
    {
        // Handle each known return type for the method
        Type returnType = method.ReturnType;

        // No return value, either synchronous (void) or asynchronous (Task / ValueTask).

        if (returnType == typeof(void))
        {
            return static (functionName, result, variables, _) =>
                new ValueTask<FunctionResult>(new FunctionResult(functionName, variables));
        }

        if (returnType == typeof(Task))
        {
            return async static (functionName, result, variables, _) =>
            {
                await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(functionName, variables);
            };
        }

        if (returnType == typeof(ValueTask))
        {
            return async static (functionName, result, variables, _) =>
            {
                await ((ValueTask)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(functionName, variables);
            };
        }

        // string (which is special as no marshaling is required), either synchronous (string) or asynchronous (Task<string> / ValueTask<string>)

        if (returnType == typeof(string))
        {
            return static (functionName, result, variables, _) =>
            {
                var resultString = (string?)result;
                variables.Update(resultString);
                return new ValueTask<FunctionResult>(new FunctionResult(functionName, variables, resultString));
            };
        }

        if (returnType == typeof(Task<string>))
        {
            return async static (functionName, result, variables, _) =>
            {
                var resultString = await ((Task<string>)ThrowIfNullResult(result)).ConfigureAwait(false);
                variables.Update(resultString);
                return new FunctionResult(functionName, variables, resultString);
            };
        }

        if (returnType == typeof(ValueTask<string>))
        {
            return async static (functionName, result, variables, _) =>
            {
                var resultString = await ((ValueTask<string>)ThrowIfNullResult(result)).ConfigureAwait(false);
                variables.Update(resultString);
                return new FunctionResult(functionName, variables, resultString);
            };
        }

        // All other synchronous return types T.

        if (!returnType.IsGenericType || returnType.GetGenericTypeDefinition() == typeof(Nullable<>))
        {
            if (GetFormatter(returnType) is not Func<object?, CultureInfo, string> formatter)
            {
                throw GetExceptionForInvalidSignature(method, $"Unknown return type {returnType}");
            }

            return (functionName, result, variables, kernel) =>
            {
                variables.Update(formatter(result, kernel.Culture));
                return new ValueTask<FunctionResult>(new FunctionResult(functionName, variables, result));
            };
        }

        // All other asynchronous return types

        // Task<T>
        if (returnType.GetGenericTypeDefinition() is Type genericTask &&
            genericTask == typeof(Task<>) &&
            returnType.GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)?.GetGetMethod() is MethodInfo taskResultGetter &&
            GetFormatter(taskResultGetter.ReturnType) is Func<object?, CultureInfo, string> taskResultFormatter)
        {
            return async (functionName, result, variables, kernel) =>
            {
                await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);

                var taskResult = Invoke(taskResultGetter, result, Array.Empty<object>());

                variables.Update(taskResultFormatter(taskResult, kernel.Culture));
                return new FunctionResult(functionName, variables, taskResult);
            };
        }

        // ValueTask<T>
        if (returnType.GetGenericTypeDefinition() is Type genericValueTask &&
            genericValueTask == typeof(ValueTask<>) &&
            returnType.GetMethod("AsTask", BindingFlags.Public | BindingFlags.Instance) is MethodInfo valueTaskAsTask &&
            valueTaskAsTask.ReturnType.GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)?.GetGetMethod() is MethodInfo asTaskResultGetter &&
            GetFormatter(asTaskResultGetter.ReturnType) is Func<object?, CultureInfo, string> asTaskResultFormatter)
        {
            return async (functionName, result, variables, kernel) =>
            {
                Task task = (Task)Invoke(valueTaskAsTask, ThrowIfNullResult(result), Array.Empty<object>())!;
                await task.ConfigureAwait(false);

                var taskResult = Invoke(asTaskResultGetter, task, Array.Empty<object>());

                variables.Update(asTaskResultFormatter(taskResult, kernel.Culture));
                return new FunctionResult(functionName, variables, taskResult);
            };
        }

        // IAsyncEnumerable<T>
        if (returnType.GetGenericTypeDefinition() is Type genericAsyncEnumerable && genericAsyncEnumerable == typeof(IAsyncEnumerable<>))
        {
            Type elementType = returnType.GetGenericArguments()[0];

            MethodInfo? getAsyncEnumeratorMethod = typeof(IAsyncEnumerable<>)
                .MakeGenericType(elementType)
                .GetMethod("GetAsyncEnumerator");

            if (getAsyncEnumeratorMethod is not null)
            {
                return (functionName, result, variables, _) =>
                {
                    var asyncEnumerator = Invoke(getAsyncEnumeratorMethod, result, s_cancellationTokenNoneArray);

                    if (asyncEnumerator is not null)
                    {
                        return new ValueTask<FunctionResult>(new FunctionResult(functionName, variables, asyncEnumerator));
                    }

                    return new ValueTask<FunctionResult>(new FunctionResult(functionName, variables));
                };
            }
        }

        // Unrecognized return type.
        throw GetExceptionForInvalidSignature(method, $"Unknown return type {returnType}");

        // Throws an exception if a result is found to be null unexpectedly
        static object ThrowIfNullResult(object? result) =>
            result ??
            throw new KernelException("Function returned null unexpectedly.");
    }

    /// <summary>Invokes the MethodInfo with the specified target object and arguments.</summary>
    private static object? Invoke(MethodInfo method, object? target, object?[]? arguments)
    {
        object? result = null;
        try
        {
            const BindingFlags BindingFlagsDoNotWrapExceptions = (BindingFlags)0x02000000; // BindingFlags.DoNotWrapExceptions on .NET Core 2.1+, ignored before then
            result = method.Invoke(target, BindingFlagsDoNotWrapExceptions, binder: null, arguments, culture: null);
        }
        catch (TargetInvocationException e) when (e.InnerException is not null)
        {
            // If we're targeting .NET Framework, such that BindingFlags.DoNotWrapExceptions
            // is ignored, the original exception will be wrapped in a TargetInvocationException.
            // Unwrap it and throw that original exception, maintaining its stack information.
            ExceptionDispatchInfo.Capture(e.InnerException).Throw();
        }

        return result;
    }

    /// <summary>Gets an exception that can be thrown indicating an invalid signature.</summary>
    [DoesNotReturn]
    private static Exception GetExceptionForInvalidSignature(MethodInfo method, string reason) =>
        throw new KernelException($"Function '{method.Name}' is not supported by the kernel. {reason}");

    /// <summary>Throws an exception indicating an invalid KernelFunctionFactory signature if the specified condition is not met.</summary>
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
                targetType = Nullable.GetUnderlyingType(targetType)!;
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
                targetType = Nullable.GetUnderlyingType(targetType)!;
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
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>
    /// Remove characters from method name that are valid in metadata but invalid for SK.
    /// </summary>
    private static string SanitizeMetadataName(string methodName) =>
        s_invalidNameCharsRegex.Replace(methodName, "_");

    /// <summary>Regex that flags any character other than ASCII digits or letters or the underscore.</summary>
    private static readonly Regex s_invalidNameCharsRegex = new("[^0-9A-Za-z_]");

    /// <summary>Parser functions for converting strings to parameter types.</summary>
    private static readonly ConcurrentDictionary<Type, Func<string, CultureInfo, object?>?> s_parsers = new();

    /// <summary>Formatter functions for converting parameter types to strings.</summary>
    private static readonly ConcurrentDictionary<Type, Func<object?, CultureInfo, string?>?> s_formatters = new();

    #endregion
}
