// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Interface for the semantic kernel.
/// </summary>
public interface IKernel
{
    /// <summary>
    /// App logger
    /// </summary>
    ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Semantic memory instance
    /// </summary>
    ISemanticTextMemory Memory { get; }

    /// <summary>
    /// Reference to the engine rendering prompt templates
    /// </summary>
    IPromptTemplateEngine PromptTemplateEngine { get; }

    /// <summary>
    /// Reference to the read-only function collection containing all the imported functions
    /// </summary>
    IReadOnlyFunctionCollection Functions { get; }

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use Kernel.Functions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    IReadOnlyFunctionCollection Skills { get; }
#pragma warning restore CS1591

    /// <summary>
    /// Reference to Http handler factory
    /// </summary>
    IDelegatingHandlerFactory HttpHandlerFactory { get; }

    /// <summary>
    /// Build and register a function in the internal function collection, in a global generic plugin.
    /// </summary>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    ISKFunction RegisterSemanticFunction(
        string functionName,
        SemanticFunctionConfig functionConfig);

    /// <summary>
    /// Build and register a function in the internal function collection.
    /// </summary>
    /// <param name="pluginName">Name of the plugin containing the function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    ISKFunction RegisterSemanticFunction(
        string pluginName,
        string functionName,
        SemanticFunctionConfig functionConfig);

    /// <summary>
    /// Registers a custom function in the internal function collection.
    /// </summary>
    /// <param name="customFunction">The custom function to register.</param>
    /// <returns>A C# function wrapping the function execution logic.</returns>
    ISKFunction RegisterCustomFunction(ISKFunction customFunction);

    /// <summary>
    /// Import a set of functions as a plugin from the given object instance. Only the functions that have the `SKFunction` attribute will be included in the plugin.
    /// Once these functions are imported, the prompt templates can use functions to import content at runtime.
    /// </summary>
    /// <param name="functionsInstance">Instance of a class containing functions</param>
    /// <param name="pluginName">Name of the plugin for function collection and prompt templates. If the value is empty functions are registered in the global namespace.</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by function name.</returns>
    IDictionary<string, ISKFunction> ImportFunctions(object functionsInstance, string? pluginName = null);

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use Kernel.ImportFunctions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    IDictionary<string, ISKFunction> ImportSkill(object functionsInstance, string? pluginName = null);
#pragma warning restore CS1591

    /// <summary>
    /// Set the semantic memory to use
    /// </summary>
    /// <param name="memory">Semantic memory instance</param>
    void RegisterMemory(ISemanticTextMemory memory);

    /// <summary>
    /// Run a single synchronous or asynchronous <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="skFunction">A Semantic Kernel function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function</returns>
    Task<KernelResult> RunAsync(
        ISKFunction skFunction,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="input">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        string input,
        params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="variables">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        ContextVariables variables,
        params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="input">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        string input,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<KernelResult> RunAsync(
        ContextVariables variables,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline);

    /// <summary>
    /// Create a new instance of a context, linked to the kernel internal state.
    /// </summary>
    /// <returns>SK context</returns>
    SKContext CreateNewContext();

    /// <summary>
    /// Get one of the configured services. Currently limited to AI services.
    /// </summary>
    /// <param name="name">Optional name. If the name is not provided, returns the default T available</param>
    /// <typeparam name="T">Service type</typeparam>
    /// <returns>Instance of T</returns>
    T GetService<T>(string? name = null) where T : IAIService;

    /// <summary>
    /// Used for registering a function invoking event handler.
    /// Triggers before each function invocation.
    /// </summary>
    event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <summary>
    /// Used for registering a function invoked event handler.
    /// Triggers after each function invocation.
    /// </summary>
    event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    #region Obsolete

    /// <summary>
    /// Access registered functions by plugin name and function name. Not case sensitive.
    /// The function might be native or semantic, it's up to the caller handling it.
    /// </summary>
    /// <param name="pluginName">Plugin name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>Delegate to execute the function</returns>
    [Obsolete("Func shorthand no longer no longer supported. Use Kernel.Plugins collection instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    ISKFunction Func(string pluginName, string functionName);

    #endregion
}
