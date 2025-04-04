// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.ExceptionServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides factory methods for creating <see cref="KernelFunction"/> instances backed by a .NET method.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
internal sealed partial class KernelFunctionFromMethod : KernelFunction
{
    private static readonly Dictionary<Type, Func<string, object>> s_jsonStringParsers = new(12)
    {
        { typeof(bool), s => bool.Parse(s) },
        { typeof(int), s => int.Parse(s) },
        { typeof(uint), s => uint.Parse(s) },
        { typeof(long), s => long.Parse(s) },
        { typeof(ulong), s => ulong.Parse(s) },
        { typeof(float), s => float.Parse(s) },
        { typeof(double), s => double.Parse(s) },
        { typeof(decimal), s => decimal.Parse(s) },
        { typeof(short), s => short.Parse(s) },
        { typeof(ushort), s => ushort.Parse(s) },
        { typeof(byte), s => byte.Parse(s) },
        { typeof(sbyte), s => sbyte.Parse(s) }
    };

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction Create(
        MethodInfo method,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null)
    {
        return Create(
            method,
            target,
            new KernelFunctionFromMethodOptions
            {
                FunctionName = functionName,
                Description = description,
                Parameters = parameters,
                ReturnParameter = returnParameter,
                LoggerFactory = loggerFactory
            });
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunction Create(
        MethodInfo method,
        JsonSerializerOptions jsonSerializerOptions,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null)
    {
        return Create(
            method,
            jsonSerializerOptions,
            target,
            new KernelFunctionFromMethodOptions
            {
                FunctionName = functionName,
                Description = description,
                Parameters = parameters,
                ReturnParameter = returnParameter,
                LoggerFactory = loggerFactory
            });
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="options">Optional function creation options.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction Create(
        MethodInfo method,
        object? target = null,
        KernelFunctionFromMethodOptions? options = default)
    {
        Verify.NotNull(method);
        if (!method.IsStatic && target is null)
        {
            throw new ArgumentNullException(nameof(target), "Target must not be null for an instance method.");
        }

        MethodDetails methodDetails = GetMethodDetails(options?.FunctionName, method, target);
        var result = new KernelFunctionFromMethod(
            method,
            methodDetails.Function,
            methodDetails.Name,
            options?.Description ?? methodDetails.Description,
            options?.Parameters?.ToList() ?? methodDetails.Parameters,
            options?.ReturnParameter ?? methodDetails.ReturnParameter,
            options?.AdditionalMetadata);

        if (options?.LoggerFactory?.CreateLogger(method.DeclaringType ?? typeof(KernelFunctionFromPrompt)) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Created KernelFunction '{Name}' for '{MethodName}'", result.Name, method.Name);
        }

        return result;
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="options">Optional function creation options.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunction Create(
        MethodInfo method,
        JsonSerializerOptions jsonSerializerOptions,
        object? target = null,
        KernelFunctionFromMethodOptions? options = default)
    {
        Verify.NotNull(method);
        Verify.NotNull(jsonSerializerOptions);
        if (!method.IsStatic && target is null)
        {
            throw new ArgumentNullException(nameof(target), "Target must not be null for an instance method.");
        }

        MethodDetails methodDetails = GetMethodDetails(options?.FunctionName, method, jsonSerializerOptions, target);
        var result = new KernelFunctionFromMethod(
            method,
            methodDetails.Function,
            methodDetails.Name,
            options?.Description ?? methodDetails.Description,
            options?.Parameters?.ToList() ?? methodDetails.Parameters,
            options?.ReturnParameter ?? methodDetails.ReturnParameter,
            jsonSerializerOptions,
            options?.AdditionalMetadata);

        if (options?.LoggerFactory?.CreateLogger(method.DeclaringType ?? typeof(KernelFunctionFromPrompt)) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Created KernelFunction '{Name}' for '{MethodName}'", result.Name, method.Name);
        }

        return result;
    }

    /// <summary>
    /// Creates a <see cref="KernelFunctionMetadata"/> instance for a method, specified via an <see cref="MethodInfo"/> instance.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunctionMetadata CreateMetadata(
        MethodInfo method,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null)
        => CreateMetadata(
            method,
            new KernelFunctionFromMethodOptions
            {
                FunctionName = functionName,
                Description = description,
                Parameters = parameters,
                ReturnParameter = returnParameter,
                LoggerFactory = loggerFactory
            });

    /// <summary>
    /// Creates a <see cref="KernelFunctionMetadata"/> instance for a method, specified via an <see cref="MethodInfo"/> instance.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunctionMetadata CreateMetadata(
        MethodInfo method,
        JsonSerializerOptions jsonSerializerOptions,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null)
        => CreateMetadata(
            method,
            jsonSerializerOptions,
            new KernelFunctionFromMethodOptions
            {
                FunctionName = functionName,
                Description = description,
                Parameters = parameters,
                ReturnParameter = returnParameter,
                LoggerFactory = loggerFactory
            });

    /// <summary>
    /// Creates a <see cref="KernelFunctionMetadata"/> instance for a method, specified via an <see cref="MethodInfo"/> instance.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="options">Optional function creation options.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunctionMetadata CreateMetadata(
        MethodInfo method,
        KernelFunctionFromMethodOptions? options = default)
    {
        Verify.NotNull(method);

        MethodDetails methodDetails = GetMethodDetails(options?.FunctionName, method, null);
        var result = new KernelFunctionFromMethod(
            method,
            methodDetails.Function,
            methodDetails.Name,
            options?.Description ?? methodDetails.Description,
            options?.Parameters?.ToList() ?? methodDetails.Parameters,
            options?.ReturnParameter ?? methodDetails.ReturnParameter,
            options?.AdditionalMetadata);

        if (options?.LoggerFactory?.CreateLogger(method.DeclaringType ?? typeof(KernelFunctionFromPrompt)) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Created KernelFunctionMetadata '{Name}' for '{MethodName}'", result.Name, method.Name);
        }

        return result.Metadata;
    }

    /// <summary>
    /// Creates a <see cref="KernelFunctionMetadata"/> instance for a method, specified via an <see cref="MethodInfo"/> instance.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional function creation options.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunctionMetadata CreateMetadata(
        MethodInfo method,
        JsonSerializerOptions jsonSerializerOptions,
        KernelFunctionFromMethodOptions? options = default)
    {
        Verify.NotNull(method);

        MethodDetails methodDetails = GetMethodDetails(options?.FunctionName, method, jsonSerializerOptions, target: null);
        var result = new KernelFunctionFromMethod(
            method,
            methodDetails.Function,
            methodDetails.Name,
            options?.Description ?? methodDetails.Description,
            options?.Parameters?.ToList() ?? methodDetails.Parameters,
            options?.ReturnParameter ?? methodDetails.ReturnParameter,
            jsonSerializerOptions,
            options?.AdditionalMetadata);

        if (options?.LoggerFactory?.CreateLogger(method.DeclaringType ?? typeof(KernelFunctionFromPrompt)) is ILogger logger &&
            logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Created KernelFunctionMetadata '{Name}' for '{MethodName}'", result.Name, method.Name);
        }

        return result.Metadata;
    }

    /// <inheritdoc/>
    protected override ValueTask<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken)
    {
        return this._function(kernel, this, arguments, cancellationToken);
    }

    /// <inheritdoc/>
    protected override async IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(
        Kernel kernel,
        KernelArguments arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        FunctionResult functionResult = await this.InvokeCoreAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

        if (functionResult.Value is TResult result)
        {
            yield return result;
            yield break;
        }

        // If the function returns an IAsyncEnumerable<T>, we can stream the results directly.
        // This helps to enable composition, with a KernelFunctionFromMethod that returns an
        // Invoke{Prompt}StreamingAsync and returns its result enumerable directly.
        if (functionResult.Value is IAsyncEnumerable<TResult> asyncEnumerable)
        {
            await foreach (TResult item in asyncEnumerable.WithCancellation(cancellationToken).ConfigureAwait(false))
            {
                yield return item;
            }

            yield break;
        }

        // Supports the following provided T types for Method streaming
        if (typeof(TResult) == typeof(StreamingKernelContent) ||
            typeof(TResult) == typeof(StreamingMethodContent))
        {
            if (functionResult.Value is not null)
            {
                yield return (TResult)(object)new StreamingMethodContent(functionResult.Value, functionResult.Metadata);
            }
            yield break;
        }

        throw new NotSupportedException($"Streaming function {this.Name} does not support type {typeof(TResult)}");
    }

    /// <inheritdoc/>
    public override KernelFunction Clone(string pluginName)
    {
        Verify.NotNullOrWhiteSpace(pluginName, nameof(pluginName));

        if (base.JsonSerializerOptions is not null)
        {
            return new KernelFunctionFromMethod(
            this.UnderlyingMethod!,
            this._function,
            this.Name,
            pluginName,
            this.Description,
            this.Metadata.Parameters,
            this.Metadata.ReturnParameter,
            base.JsonSerializerOptions,
            this.Metadata.AdditionalProperties);
        }

        [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "Non AOT scenario.")]
        [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "Non AOT scenario.")]
        KernelFunctionFromMethod Clone()
        {
            return new KernelFunctionFromMethod(
            this.UnderlyingMethod!,
            this._function,
            this.Name,
            pluginName,
            this.Description,
            this.Metadata.Parameters,
            this.Metadata.ReturnParameter,
            this.Metadata.AdditionalProperties);
        }

        return Clone();
    }

    /// <summary>Delegate used to invoke the underlying delegate.</summary>
    private delegate ValueTask<FunctionResult> ImplementationFunc(
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments,
        CancellationToken cancellationToken);

    private static readonly object[] s_cancellationTokenNoneArray = [CancellationToken.None];
    private readonly ImplementationFunc _function;

    private record struct MethodDetails(string Name, string Description, ImplementationFunc Function, List<KernelParameterMetadata> Parameters, KernelReturnParameterMetadata ReturnParameter);

    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    private KernelFunctionFromMethod(
        MethodInfo method,
        ImplementationFunc implementationFunc,
        string functionName,
        string description,
        IReadOnlyList<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter,
        ReadOnlyDictionary<string, object?>? additionalMetadata = null) :
        this(method, implementationFunc, functionName, null, description, parameters, returnParameter, additionalMetadata)
    {
    }

    private KernelFunctionFromMethod(
        MethodInfo method,
        ImplementationFunc implementationFunc,
        string functionName,
        string description,
        IReadOnlyList<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter,
        JsonSerializerOptions jsonSerializerOptions,
        ReadOnlyDictionary<string, object?>? additionalMetadata = null) :
        this(method, implementationFunc, functionName, null, description, parameters, returnParameter, jsonSerializerOptions, additionalMetadata)
    {
    }

    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    private KernelFunctionFromMethod(
        MethodInfo method,
        ImplementationFunc implementationFunc,
        string functionName,
        string? pluginName,
        string description,
        IReadOnlyList<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter,
        ReadOnlyDictionary<string, object?>? additionalMetadata = null) :
        base(functionName, pluginName, description, parameters, returnParameter, additionalMetadata: additionalMetadata)
    {
        Verify.ValidFunctionName(functionName);

        this._function = implementationFunc;
        this.UnderlyingMethod = method;
    }

    private KernelFunctionFromMethod(
        MethodInfo method,
        ImplementationFunc implementationFunc,
        string functionName,
        string? pluginName,
        string description,
        IReadOnlyList<KernelParameterMetadata> parameters,
        KernelReturnParameterMetadata returnParameter,
        JsonSerializerOptions jsonSerializerOptions,
        ReadOnlyDictionary<string, object?>? additionalMetadata = null) :
        base(functionName, pluginName, description, parameters, jsonSerializerOptions, returnParameter, additionalMetadata: additionalMetadata)
    {
        Verify.ValidFunctionName(functionName);

        this._function = implementationFunc;
        this.UnderlyingMethod = method;
    }

    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT save.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    private static MethodDetails GetMethodDetails(string? functionName, MethodInfo method, JsonSerializerOptions jsonSerializerOptions, object? target)
    {
        Verify.NotNull(jsonSerializerOptions);
        return GetMethodDetails(functionName, method, target, jsonSerializerOptions);
    }

    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    private static MethodDetails GetMethodDetails(string? functionName, MethodInfo method, object? target, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        ThrowForInvalidSignatureIf(method.ContainsGenericParameters, method, "Open generic methods are not supported");

        if (functionName is null)
        {
            // Get the name to use for the function.  If the function has a KernelFunction attribute and it contains a name, we use that.
            // Otherwise, we use the name of the method, but strip off any "Async" suffix if it's {Value}Task-returning.
            // We don't apply any heuristics to the value supplied by KernelFunction's Name so that it can always be used
            // as a definitive override.
            functionName = method.GetCustomAttribute<KernelFunctionAttribute>(inherit: true)?.Name?.Trim();
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

        // Build up a list of KernelParameterMetadata for the parameters we expect to be populated
        // from arguments. Some arguments are populated specially, not from arguments, and thus
        // we don't want to advertize their metadata, e.g. CultureInfo, ILoggerFactory, etc.
        List<KernelParameterMetadata> argParameterViews = [];

        // Get marshaling funcs for parameters and build up the parameter metadata.
        var parameters = method.GetParameters();
        var parameterFuncs = new Func<KernelFunction, Kernel, KernelArguments, CancellationToken, object?>[parameters.Length];
        bool sawFirstParameter = false;
        for (int i = 0; i < parameters.Length; i++)
        {
            (parameterFuncs[i], KernelParameterMetadata? parameterView) = GetParameterMarshalerDelegate(method, parameters[i], ref sawFirstParameter, jsonSerializerOptions);
            if (parameterView is not null)
            {
                argParameterViews.Add(parameterView);
            }
        }

        // Check for param names conflict
        Verify.ParametersUniqueness(argParameterViews);

        // Get the return type and a marshaling func for the return value.
        (Type returnType, Func<Kernel, KernelFunction, object?, ValueTask<FunctionResult>> returnFunc) = GetReturnValueMarshalerDelegate(method);
        if (Nullable.GetUnderlyingType(returnType) is Type underlying)
        {
            // Unwrap the U from a Nullable<U> since everything is going through object, at which point Nullable<U> and a boxed U are indistinguishable.
            returnType = underlying;
        }

        // Create the func
        ValueTask<FunctionResult> Function(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            // Create the arguments.
            object?[] args = parameterFuncs.Length != 0 ? new object?[parameterFuncs.Length] : [];
            for (int i = 0; i < args.Length; i++)
            {
                args[i] = parameterFuncs[i](function, kernel, arguments, cancellationToken);
            }

            // Invoke the method.
            object? result = Invoke(method, target, args);

            // Extract and return the result.
            return returnFunc(kernel, function, result);
        }

        KernelReturnParameterMetadata returnParameterMetadata;

        if (jsonSerializerOptions is not null)
        {
            returnParameterMetadata = new KernelReturnParameterMetadata(jsonSerializerOptions)
            {
                ParameterType = returnType,
                Description = method.ReturnParameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description,
            };
        }
        else
        {
            returnParameterMetadata = new KernelReturnParameterMetadata()
            {
                ParameterType = returnType,
                Description = method.ReturnParameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description,
            };
        }

        // And return the details.
        return new MethodDetails
        {
            Function = Function,
            Name = functionName!,
            Description = method.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description ?? "",
            Parameters = argParameterViews,
            ReturnParameter = returnParameterMetadata
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
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    private static (Func<KernelFunction, Kernel, KernelArguments, CancellationToken, object?>, KernelParameterMetadata?) GetParameterMarshalerDelegate(
        MethodInfo method, ParameterInfo parameter, ref bool sawFirstParameter, JsonSerializerOptions? jsonSerializerOptions)
    {
        Type type = parameter.ParameterType;

        // Handle special types.
        // These are not reported as part of KernelParameterMetadata because they're not satisfied from arguments.

        if (type == typeof(KernelFunction))
        {
            return (static (KernelFunction func, Kernel _, KernelArguments _, CancellationToken _) => func, null);
        }

        if (type == typeof(Kernel))
        {
            return (static (KernelFunction _, Kernel kernel, KernelArguments _, CancellationToken _) => kernel, null);
        }

        if (type == typeof(KernelArguments))
        {
            return (static (KernelFunction _, Kernel _, KernelArguments arguments, CancellationToken _) => arguments, null);
        }

        if (type == typeof(ILoggerFactory))
        {
            return ((KernelFunction _, Kernel kernel, KernelArguments _, CancellationToken _) => kernel.LoggerFactory, null);
        }

        if (type == typeof(ILogger))
        {
            return ((KernelFunction _, Kernel kernel, KernelArguments _, CancellationToken _) => kernel.LoggerFactory.CreateLogger(method?.DeclaringType ?? typeof(KernelFunctionFromPrompt)) ?? NullLogger.Instance, null);
        }

        if (type == typeof(IAIServiceSelector))
        {
            return ((KernelFunction _, Kernel kernel, KernelArguments _, CancellationToken _) => kernel.ServiceSelector, null);
        }

        if (type == typeof(CultureInfo) || type == typeof(IFormatProvider))
        {
            return (static (KernelFunction _, Kernel kernel, KernelArguments _, CancellationToken _) => kernel.Culture, null);
        }

        if (type == typeof(CancellationToken))
        {
            return (static (KernelFunction _, Kernel _, KernelArguments _, CancellationToken cancellationToken) => cancellationToken, null);
        }

        // Handle the special FromKernelServicesAttribute, which indicates that the parameter should be sourced from the kernel's services.
        // As with the above, these are not reported as part of KernelParameterMetadata because they're not satisfied from arguments.
        if (parameter.GetCustomAttribute<FromKernelServicesAttribute>() is FromKernelServicesAttribute fromKernelAttr)
        {
            return ((KernelFunction _, Kernel kernel, KernelArguments _, CancellationToken _) =>
            {
                // Try to resolve the service from kernel.Services, using the attribute's key if one was provided.
                object? service = kernel.Services is IKeyedServiceProvider keyedServiceProvider ?
                    keyedServiceProvider.GetKeyedService(type, fromKernelAttr.ServiceKey) :
                    kernel.Services.GetService(type);
                if (service is not null)
                {
                    return service;
                }

                // The service wasn't available. If the parameter has a default value (typically null), use that.
                if (parameter.HasDefaultValue)
                {
                    return parameter.DefaultValue;
                }

                // Otherwise, fail.
                throw new KernelException($"Missing service for function parameter '{parameter.Name}'",
                    new ArgumentException("Missing service for function parameter", parameter.Name));
            }, null);
        }

        // Handle parameters to be satisfied from KernelArguments.

        string name = SanitizeMetadataName(parameter.Name ?? "");
        ThrowForInvalidSignatureIf(string.IsNullOrWhiteSpace(name), method, $"Parameter {parameter.Name}'s attribute defines an invalid name.");

        var converter = GetConverter(type);

        object? parameterFunc(KernelFunction _, Kernel kernel, KernelArguments arguments, CancellationToken __)
        {
            // 1. Use the value of the variable if it exists.
            if (arguments.TryGetValue(name, out object? value))
            {
                return Process(value);
            }

            // 2. Otherwise, use the default value if there is one, sourced either from an attribute or the parameter's default.
            if (parameter.HasDefaultValue)
            {
                return parameter.DefaultValue;
            }

            // 3. Otherwise, fail.
            throw new KernelException($"Missing argument for function parameter '{name}'",
                new ArgumentException("Missing argument for function parameter", name));

            object? Process(object? value)
            {
                if (type.IsAssignableFrom(value?.GetType()))
                {
                    return value;
                }

                if (converter is not null && value is not JsonElement or JsonDocument or JsonNode)
                {
                    try
                    {
                        return converter(value, kernel.Culture);
                    }
                    catch (Exception e) when (!e.IsCriticalException())
                    {
                        throw new ArgumentOutOfRangeException(name, value, e.Message);
                    }
                }

                if (value is JsonElement element && element.ValueKind == JsonValueKind.String
                    && s_jsonStringParsers.TryGetValue(type, out var jsonStringParser))
                {
                    return jsonStringParser(element.GetString()!);
                }

                if (value is not null && TryToDeserializeValue(value, type, jsonSerializerOptions, out var deserializedValue))
                {
                    return deserializedValue;
                }

                return value;
            }
        }

        sawFirstParameter = true;

        KernelParameterMetadata? parameterView;

        if (jsonSerializerOptions is not null)
        {
            parameterView = new KernelParameterMetadata(name, jsonSerializerOptions)
            {
                Description = parameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description,
                DefaultValue = parameter.HasDefaultValue ? parameter.DefaultValue?.ToString() : null,
                IsRequired = !parameter.IsOptional,
                ParameterType = type,
            };
        }
        else
        {
            parameterView = new KernelParameterMetadata(name)
            {
                Description = parameter.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description,
                DefaultValue = parameter.HasDefaultValue ? parameter.DefaultValue?.ToString() : null,
                IsRequired = !parameter.IsOptional,
                ParameterType = type,
            };
        }

        return (parameterFunc, parameterView);
    }

    /// <summary>
    /// Tries to deserialize the given value into an object of the specified target type.
    /// </summary>
    /// <param name="value">The value to be deserialized.</param>
    /// <param name="targetType">The type of the object to deserialize the value into.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for deserialization.</param>
    /// <param name="deserializedValue">The deserialized object if the method succeeds; otherwise, null.</param>
    /// <returns>true if the value is successfully deserialized; otherwise, false.</returns>
    [RequiresUnreferencedCode("Uses reflection to deserialize given value if no source generated metadata provided via JSOs, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize given value if no source generated metadata provided via JSOs, making it incompatible with AOT scenarios.")]
    private static bool TryToDeserializeValue(object value, Type targetType, JsonSerializerOptions? jsonSerializerOptions, out object? deserializedValue)
    {
        try
        {
            deserializedValue = value switch
            {
                JsonDocument document => document.Deserialize(targetType, jsonSerializerOptions),
                JsonNode node => node.Deserialize(targetType, jsonSerializerOptions),
                JsonElement element => element.Deserialize(targetType, jsonSerializerOptions),
                // The JSON can be represented by other data types from various libraries. For example, JObject, JToken, and JValue from the Newtonsoft.Json library.  
                // Since we don't take dependencies on these libraries and don't have access to the types here,
                // the only way to deserialize those types is to convert them to a string first by calling the 'ToString' method.
                // Attempting to use the 'JsonSerializer.Serialize' method, instead of calling the 'ToString' directly on those types, can lead to unpredictable outcomes.
                // For instance, the JObject for { "id": 28 } JSON is serialized into the string  "{ "Id": [] }", and the deserialization fails with the
                // following exception - "The JSON value could not be converted to System.Int32. Path: $.Id | LineNumber: 0 | BytePositionInLine: 7."
                _ => JsonSerializer.Deserialize(value.ToString()!, targetType, jsonSerializerOptions)
            };

            return true;
        }
        catch (NotSupportedException)
        {
            // There is no compatible JsonConverter for targetType or its serializable members.
        }
        catch (JsonException)
        {
            // The JSON is invalid.
        }

        deserializedValue = null;
        return false;
    }

    /// <summary>
    /// Gets a delegate for handling the result value of a method, converting it into the <see cref="Task{FunctionResult}"/> to return from the invocation.
    /// </summary>
    private static (Type ReturnType, Func<Kernel, KernelFunction, object?, ValueTask<FunctionResult>> Marshaler) GetReturnValueMarshalerDelegate(MethodInfo method)
    {
        // Handle each known return type for the method
        Type returnType = method.ReturnType;

        // No return value, either synchronous (void) or asynchronous (Task / ValueTask).

        if (returnType == typeof(void))
        {
            return (typeof(void), (static (_, function, _) =>
                new ValueTask<FunctionResult>(new FunctionResult(function))));
        }

        if (returnType == typeof(Task))
        {
            return (typeof(void), async static (_, function, result) =>
            {
                await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(function);
            }
            );
        }

        if (returnType == typeof(ValueTask))
        {
            return (typeof(void), async static (_, function, result) =>
            {
                await ((ValueTask)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(function);
            }
            );
        }

        // string (which is special as no marshaling is required), either synchronous (string) or asynchronous (Task<string> / ValueTask<string>)

        if (returnType == typeof(string))
        {
            return (typeof(string), static (kernel, function, result) =>
            {
                var resultString = (string?)result;
                return new ValueTask<FunctionResult>(new FunctionResult(function, resultString, kernel.Culture));
            }
            );
        }

        if (returnType == typeof(Task<string>))
        {
            return (typeof(string), async static (kernel, function, result) =>
            {
                var resultString = await ((Task<string>)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(function, resultString, kernel.Culture);
            }
            );
        }

        if (returnType == typeof(ValueTask<string>))
        {
            return (typeof(string), async static (kernel, function, result) =>
            {
                var resultString = await ((ValueTask<string>)ThrowIfNullResult(result)).ConfigureAwait(false);
                return new FunctionResult(function, resultString, kernel.Culture);
            }
            );
        }

        if (returnType == typeof(FunctionResult))
        {
            return (typeof(object), static (_, function, result) =>
            {
                var functionResult = (FunctionResult?)result;
                return new ValueTask<FunctionResult>(functionResult ?? new FunctionResult(function));
            }
            );
        }

        if (returnType == typeof(Task<FunctionResult>))
        {
            return (typeof(object), async static (_, _, result) =>
            {
                var functionResult = await ((Task<FunctionResult>)ThrowIfNullResult(result)).ConfigureAwait(false);
                return functionResult;
            }
            );
        }

        if (returnType == typeof(ValueTask<FunctionResult>))
        {
            return (typeof(object), async static (_, _, result) =>
            {
                var functionResult = await ((ValueTask<FunctionResult>)ThrowIfNullResult(result)).ConfigureAwait(false);
                return functionResult;
            }
            );
        }

        // Asynchronous return types
        if (returnType.IsGenericType)
        {
            // Task<T>
#if NET6_0_OR_GREATER
            if (returnType.GetGenericTypeDefinition() == typeof(Task<>) &&
                ((PropertyInfo)returnType.GetMemberWithSameMetadataDefinitionAs(s_taskGetResultPropertyInfo)) is PropertyInfo taskPropertyInfo &&
                taskPropertyInfo.GetGetMethod() is MethodInfo taskResultGetter)
#else
            if (returnType.GetGenericTypeDefinition() == typeof(Task<>) &&
                returnType.GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)?.GetGetMethod() is MethodInfo taskResultGetter)
#endif
            {
                return (taskResultGetter.ReturnType, async (kernel, function, result) =>
                {
                    await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);

                    var taskResult = Invoke(taskResultGetter, result, null);
                    return new FunctionResult(function, taskResult, kernel.Culture);
                }
                );
            }

            // ValueTask<T>
#if NET6_0_OR_GREATER
            if (returnType.GetGenericTypeDefinition() == typeof(ValueTask<>) &&
                   returnType.GetMemberWithSameMetadataDefinitionAs(s_valueTaskGetAsTaskMethodInfo) is MethodInfo valueTaskAsTask &&
                   valueTaskAsTask.ReturnType.GetMemberWithSameMetadataDefinitionAs(s_taskGetResultPropertyInfo) is PropertyInfo valueTaskPropertyInfo &&
                   valueTaskPropertyInfo.GetGetMethod() is MethodInfo asTaskResultGetter)
#else
            if (returnType.GetGenericTypeDefinition() == typeof(ValueTask<>) &&
                    returnType.GetMethod("AsTask", BindingFlags.Public | BindingFlags.Instance) is MethodInfo valueTaskAsTask &&
                    valueTaskAsTask.ReturnType.GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)?.GetGetMethod() is MethodInfo asTaskResultGetter)
#endif
            {
                return (asTaskResultGetter.ReturnType, async (kernel, function, result) =>
                {
                    Task task = (Task)Invoke(valueTaskAsTask, ThrowIfNullResult(result), null)!;
                    await task.ConfigureAwait(false);

                    var taskResult = Invoke(asTaskResultGetter, task, null);
                    return new FunctionResult(function, taskResult, kernel.Culture);
                }
                );
            }

            // IAsyncEnumerable<T>
            if (returnType.GetGenericTypeDefinition() == typeof(IAsyncEnumerable<>))
            {
#if NET6_0_OR_GREATER
                //typeof(IAsyncEnumerable<>).GetMethod("GetAsyncEnumerator")!;
                MethodInfo? getAsyncEnumeratorMethod = returnType.GetMemberWithSameMetadataDefinitionAs(s_asyncEnumerableGetAsyncEnumeratorMethodInfo) as MethodInfo;
#else
                Type elementType = returnType.GetGenericArguments()[0];
                MethodInfo? getAsyncEnumeratorMethod = typeof(IAsyncEnumerable<>)
                    .MakeGenericType(elementType)
                    .GetMethod("GetAsyncEnumerator");
#endif

                if (getAsyncEnumeratorMethod is not null)
                {
                    return (returnType, (kernel, function, result) =>
                    {
                        var asyncEnumerator = Invoke(getAsyncEnumeratorMethod, result, s_cancellationTokenNoneArray);

                        if (asyncEnumerator is not null)
                        {
                            return new ValueTask<FunctionResult>(new FunctionResult(function, asyncEnumerator, kernel.Culture));
                        }

                        return new ValueTask<FunctionResult>(new FunctionResult(function));
                    }
                    );
                }
            }
        }

        // For everything else, just use the result as-is.
        return (returnType, (kernel, function, result) =>
        {
            return new ValueTask<FunctionResult>(new FunctionResult(function, result, kernel.Culture));
        }
        );

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

    /// <summary>
    /// Gets a converter for type to ty conversion. For example, string to int, string to Guid, double to int, CustomType to string, etc.
    /// </summary>
    /// <param name="targetType">Specifies the target type into which a source type should be converted.</param>
    /// <returns>The converter function if the target type is supported; otherwise, null.</returns>
    /// <remarks>
    /// The conversion function uses whatever TypeConverter is registered for the target type.
    /// Conversion is first attempted using the current culture, and if that fails, it tries again
    /// with the invariant culture. If both fail, an exception is thrown.
    /// </remarks>
    private static Func<object?, CultureInfo, object?>? GetConverter(Type targetType) =>
        s_parsers.GetOrAdd(targetType, static targetType =>
        {
            // For nullables, parse as the inner type.  We then just need to be careful to treat null as null,
            // as the underlying parser might not be expecting null.
            bool wasNullable = !targetType.IsValueType;
            if (!wasNullable && targetType.IsGenericType && targetType.GetGenericTypeDefinition() == typeof(Nullable<>))
            {
                wasNullable = true;
                targetType = Nullable.GetUnderlyingType(targetType)!;
            }

            // Finally, look up and use a type converter. Again, special-case null if it was actually Nullable<T>.
            if (TypeConverterFactory.GetTypeConverter(targetType) is TypeConverter converter)
            {
                return (input, cultureInfo) =>
                {
                    // This if block returns null if the target ValueType is nullable, or if the target type is a ReferenceType, which is inherently nullable.
                    // This prevents null from being handled by converters below, which may fail when converting from nulls or to the target type from nulls.
                    if (input is null && wasNullable)
                    {
                        return null;
                    }

                    object? Convert(CultureInfo culture)
                    {
                        if (input?.GetType() is Type type && converter.CanConvertFrom(type))
                        {
                            // This line performs string to type conversion 
                            return converter.ConvertFrom(context: null, culture, input);
                        }

                        // This line performs implicit type conversion, e.g., int to long, byte to int, Guid to string, etc.
                        if (converter.CanConvertTo(targetType))
                        {
                            return converter.ConvertTo(context: null, culture, input, targetType);
                        }

                        // EnumConverter cannot convert integer, so we verify manually
                        if (targetType.IsEnum &&
                            (input is int ||
                             input is uint ||
                             input is long ||
                             input is ulong ||
                             input is short ||
                             input is ushort ||
                             input is byte ||
                             input is sbyte))
                        {
                            return Enum.ToObject(targetType, input);
                        }

                        throw new InvalidOperationException($"No converter found to convert from {targetType} to {input?.GetType()}.");
                    }

                    // First try to parse using the supplied culture (or current if none was supplied).
                    // If that fails, try with the invariant culture and allow any exception to propagate.
                    try
                    {
                        return Convert(cultureInfo);
                    }
                    catch (Exception e) when (!e.IsCriticalException() && cultureInfo != CultureInfo.InvariantCulture)
                    {
                        return Convert(CultureInfo.InvariantCulture);
                    }
                };
            }

            // Unsupported type.
            return null;
        });

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => string.IsNullOrWhiteSpace(this.Description) ? this.Name : $"{this.Name} ({this.Description})";

    /// <summary>
    /// Remove characters from method name that are valid in metadata but invalid for SK.
    /// </summary>
    internal static string SanitizeMetadataName(string methodName) =>
        InvalidNameCharsRegex().Replace(methodName, "_");

    /// <summary>Regex that flags any character other than ASCII digits or letters or the underscore.</summary>
#if NET
    [GeneratedRegex("[^0-9A-Za-z_]")]
    private static partial Regex InvalidNameCharsRegex();
#else
    private static Regex InvalidNameCharsRegex() => s_invalidNameCharsRegex;
    private static readonly Regex s_invalidNameCharsRegex = new("[^0-9A-Za-z_]", RegexOptions.Compiled);
#endif

    /// <summary>Parser functions for converting strings to parameter types.</summary>
    private static readonly ConcurrentDictionary<Type, Func<object?, CultureInfo, object?>?> s_parsers = new();
#if NET6_0_OR_GREATER
    private static readonly MethodInfo s_valueTaskGetAsTaskMethodInfo = typeof(ValueTask<>).GetMethod("AsTask", BindingFlags.Public | BindingFlags.Instance)!;
    private static readonly MemberInfo s_taskGetResultPropertyInfo = typeof(Task<>).GetProperty("Result", BindingFlags.Public | BindingFlags.Instance)!;
    private static readonly MethodInfo s_asyncEnumerableGetAsyncEnumeratorMethodInfo = typeof(IAsyncEnumerable<>).GetMethod("GetAsyncEnumerator")!;
#endif
}
