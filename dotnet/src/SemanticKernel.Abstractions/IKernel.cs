// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Interface for the semantic kernel.
/// </summary>
public interface IKernel
{
    /// <summary>
    /// The ILoggerFactory used to create a logger for logging.
    /// </summary>
    ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Gets a read-only collection of plugins registered in the kernel.
    /// </summary>
    ISKPluginCollection Plugins { get; }

    /// <summary>
    /// Reference to Http handler factory
    /// </summary>
    IDelegatingHandlerFactory HttpHandlerFactory { get; }

    /// <summary>
    /// Registers a custom function in the internal function collection.
    /// </summary>
    /// <param name="customFunction">The custom function to register.</param>
    /// <returns>A C# function wrapping the function execution logic.</returns>
    [EditorBrowsable(EditorBrowsableState.Never)]
    [Obsolete("This will be removed in a future release. Use RegisterPlugin instead.")]
    ISKFunction RegisterCustomFunction(ISKFunction customFunction);

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
    /// <param name="variables">Initializes the context with the provided variables</param>
    /// <param name="plugins">Provides a collection of plugins to be available in the new context. By default, it's the full collection from the kernel.</param>
    /// <param name="loggerFactory">Logged factory used within the context</param>
    /// <param name="culture">Optional culture info related to the context</param>
    /// <returns>SK context</returns>
    SKContext CreateNewContext(
        ContextVariables? variables = null,
        IReadOnlySKPluginCollection? plugins = null,
        ILoggerFactory? loggerFactory = null,
        CultureInfo? culture = null);

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
    /// Reference to the engine rendering prompt templates
    /// </summary>
    [Obsolete("PromptTemplateEngine has been replaced with PromptTemplateFactory and will be null. If you pass an PromptTemplateEngine instance when creating a Kernel it will be wrapped in an instance of IPromptTemplateFactory. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    IPromptTemplateEngine? PromptTemplateEngine { get; }

    /// <summary>
    /// Semantic memory instance
    /// </summary>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. See sample dotnet/samples/KernelSyntaxExamples/Example14_SemanticMemory.cs in the semantic-kernel repository.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    ISemanticTextMemory Memory { get; }

    /// <summary>
    /// Set the semantic memory to use
    /// </summary>
    /// <param name="memory">Semantic memory instance</param>
    /// <inheritdoc/>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. See sample dotnet/samples/KernelSyntaxExamples/Example14_SemanticMemory.cs in the semantic-kernel repository.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    void RegisterMemory(ISemanticTextMemory memory);

    #endregion
}
