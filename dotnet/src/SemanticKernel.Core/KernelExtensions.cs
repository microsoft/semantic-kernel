// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for interacting with <see cref="Kernel"/> and related types.</summary>
public static class KernelExtensions
{
    #region CreateFunctionFromMethod
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateFunctionFromMethod(
        this Kernel kernel,
        Delegate method,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(method);

        return KernelFunctionFactory.CreateFromMethod(method.Method, method.Target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    public static KernelFunction CreateFunctionFromMethod(
        this Kernel kernel,
        Delegate method,
        JsonSerializerOptions jsonSerializerOptions,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(method);

        return KernelFunctionFactory.CreateFromMethod(method.Method, jsonSerializerOptions, method.Target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateFunctionFromMethod(
        this Kernel kernel,
        MethodInfo method,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(method);

        return KernelFunctionFactory.CreateFromMethod(method, target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    public static KernelFunction CreateFunctionFromMethod(
        this Kernel kernel,
        MethodInfo method,
        JsonSerializerOptions jsonSerializerOptions,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(method);

        return KernelFunctionFactory.CreateFromMethod(method, jsonSerializerOptions, target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }

    #endregion

    #region CreateFunctionFromPrompt

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="executionSettings">Default execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to a randomly generated name.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        PromptExecutionSettings? executionSettings = null,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(promptTemplate);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            executionSettings,
            functionName,
            description,
            templateFormat,
            promptTemplateFactory,
            kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="executionSettings">Default execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to a randomly generated name.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        JsonSerializerOptions jsonSerializerOptions,
        PromptExecutionSettings? executionSettings = null,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(promptTemplate);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            jsonSerializerOptions,
            executionSettings,
            functionName,
            description,
            templateFormat,
            promptTemplateFactory,
            kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="executionSettings">List of execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to a randomly generated name.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        IEnumerable<PromptExecutionSettings>? executionSettings,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(promptTemplate);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            executionSettings,
            functionName,
            description,
            templateFormat,
            promptTemplateFactory,
            kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="executionSettings">List of execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to a randomly generated name.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        JsonSerializerOptions jsonSerializerOptions,
        IEnumerable<PromptExecutionSettings>? executionSettings,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(promptTemplate);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            jsonSerializerOptions,
            executionSettings,
            functionName,
            description,
            templateFormat,
            promptTemplateFactory,
            kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template configuration.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptConfig">Configuration information describing the prompt.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptConfig"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        PromptTemplateConfig promptConfig,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(promptConfig);

        return KernelFunctionFactory.CreateFromPrompt(promptConfig, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template configuration.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptConfig">Configuration information describing the prompt.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptConfig"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        PromptTemplateConfig promptConfig,
        JsonSerializerOptions jsonSerializerOptions,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(promptConfig);

        return KernelFunctionFactory.CreateFromPrompt(promptConfig, jsonSerializerOptions, promptTemplateFactory, kernel.LoggerFactory);
    }
    #endregion

    #region CreatePluginFromType
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreatePluginFromType<T>(this Kernel kernel, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromType<T>(pluginName, kernel.Services);
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    public static KernelPlugin CreatePluginFromType<[DynamicallyAccessedMembers(
        DynamicallyAccessedMemberTypes.PublicConstructors |
        DynamicallyAccessedMemberTypes.PublicMethods |
        DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this Kernel kernel, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromType<T>(jsonSerializerOptions, pluginName, kernel.Services);
    }
    #endregion

    #region CreatePluginFromObject
    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreatePluginFromObject(this Kernel kernel, object target, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromObject(target, pluginName, kernel.LoggerFactory);
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    public static KernelPlugin CreatePluginFromObject<[DynamicallyAccessedMembersAttribute(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this Kernel kernel, T target, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromObject<T>(target, jsonSerializerOptions, pluginName, kernel.LoggerFactory);
    }
    #endregion

    #region CreatePluginFromFunctions
    /// <summary>Creates a plugin that contains the specified functions.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin CreatePluginFromFunctions(this Kernel kernel, string pluginName, IEnumerable<KernelFunction>? functions) =>
        CreatePluginFromFunctions(kernel, pluginName, description: null, functions);

    /// <summary>Creates a plugin that contains the specified functions.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin CreatePluginFromFunctions(this Kernel kernel, string pluginName, string? description = null, IEnumerable<KernelFunction>? functions = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, functions);
    }
    #endregion

    #region ImportPlugin/AddFromType
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin ImportPluginFromType<T>(this Kernel kernel, string? pluginName = null)
    {
        KernelPlugin plugin = CreatePluginFromType<T>(kernel, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    public static KernelPlugin ImportPluginFromType<[DynamicallyAccessedMembers(
        DynamicallyAccessedMemberTypes.PublicConstructors |
        DynamicallyAccessedMemberTypes.PublicMethods |
        DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this Kernel kernel, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null)
    {
        KernelPlugin plugin = CreatePluginFromType<T>(kernel, jsonSerializerOptions, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and adds it into the plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="serviceProvider">Service provider from which to resolve dependencies, such as <see cref="ILoggerFactory"/>.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin AddFromType<T>(this ICollection<KernelPlugin> plugins, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        Verify.NotNull(plugins);

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<T>(pluginName, serviceProvider);
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and adds it into the plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="serviceProvider">Service provider from which to resolve dependencies, such as <see cref="ILoggerFactory"/>.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <typeparamref name="T"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    public static KernelPlugin AddFromType<[DynamicallyAccessedMembers(
        DynamicallyAccessedMemberTypes.PublicConstructors |
        DynamicallyAccessedMemberTypes.PublicMethods |
        DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this ICollection<KernelPlugin> plugins, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        Verify.NotNull(plugins);

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<T>(jsonSerializerOptions, pluginName, serviceProvider);
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and adds it into the plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IKernelBuilderPlugins AddFromType<T>(this IKernelBuilderPlugins plugins, string? pluginName = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton<KernelPlugin>(serviceProvider => KernelPluginFactory.CreateFromType<T>(pluginName, serviceProvider));

        return plugins;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and adds it into the plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    public static IKernelBuilderPlugins AddFromType<[DynamicallyAccessedMembers(
        DynamicallyAccessedMemberTypes.PublicConstructors |
        DynamicallyAccessedMemberTypes.PublicMethods |
        DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this IKernelBuilderPlugins plugins, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton<KernelPlugin>(serviceProvider => KernelPluginFactory.CreateFromType<T>(jsonSerializerOptions, pluginName, serviceProvider));

        return plugins;
    }

    /// <summary>Adds the <paramref name="plugin"/> to the <paramref name="plugins"/>.</summary>
    /// <param name="plugins">The plugin collection to which the plugin should be added.</param>
    /// <param name="plugin">The plugin to add.</param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    public static IKernelBuilderPlugins Add(this IKernelBuilderPlugins plugins, KernelPlugin plugin)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(plugin);

        plugins.Services.AddSingleton(plugin);

        return plugins;
    }
    #endregion

    #region ImportPlugin/AddFromObject
    /// <summary>Creates a plugin that wraps the specified target object and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin ImportPluginFromObject(this Kernel kernel, object target, string? pluginName = null)
    {
        KernelPlugin plugin = CreatePluginFromObject(kernel, target, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    public static KernelPlugin ImportPluginFromObject<[DynamicallyAccessedMembersAttribute(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this Kernel kernel, T target, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null)
    {
        KernelPlugin plugin = CreatePluginFromObject<T>(kernel, target, jsonSerializerOptions, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="serviceProvider">Service provider from which to resolve dependencies, such as <see cref="ILoggerFactory"/>.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin AddFromObject(this ICollection<KernelPlugin> plugins, object target, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        Verify.NotNull(plugins);

        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(target, pluginName, serviceProvider?.GetService<ILoggerFactory>());
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="serviceProvider">Service provider from which to resolve dependencies, such as <see cref="ILoggerFactory"/>.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="target"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [Experimental("SKEXP0120")]
    public static KernelPlugin AddFromObject<[DynamicallyAccessedMembersAttribute(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this ICollection<KernelPlugin> plugins, T target, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        Verify.NotNull(plugins);

        KernelPlugin plugin = KernelPluginFactory.CreateFromObject<T>(target, jsonSerializerOptions, pluginName, serviceProvider?.GetService<ILoggerFactory>());
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IKernelBuilderPlugins AddFromObject(this IKernelBuilderPlugins plugins, object target, string? pluginName = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton(serviceProvider => KernelPluginFactory.CreateFromObject(target, pluginName, serviceProvider?.GetService<ILoggerFactory>()));

        return plugins;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    /// <remarks>
    /// Methods that have the <see cref="KernelFunctionAttribute"/> attribute will be included in the plugin.
    /// See <see cref="KernelFunctionAttribute"/> attribute for details.
    /// </remarks>
    [Experimental("SKEXP0120")]
    public static IKernelBuilderPlugins AddFromObject<[DynamicallyAccessedMembersAttribute(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] T>(this IKernelBuilderPlugins plugins, T target, JsonSerializerOptions jsonSerializerOptions, string? pluginName = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton(serviceProvider => KernelPluginFactory.CreateFromObject<T>(target, jsonSerializerOptions, pluginName, serviceProvider?.GetService<ILoggerFactory>()));

        return plugins;
    }
    #endregion

    #region ImportPlugin/AddFromFunctions
    /// <summary>Creates a plugin that contains the specified functions and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin ImportPluginFromFunctions(this Kernel kernel, string pluginName, IEnumerable<KernelFunction>? functions) =>
        ImportPluginFromFunctions(kernel, pluginName, description: null, functions);

    /// <summary>Creates a plugin that contains the specified functions and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin ImportPluginFromFunctions(this Kernel kernel, string pluginName, string? description = null, IEnumerable<KernelFunction>? functions = null)
    {
        KernelPlugin plugin = CreatePluginFromFunctions(kernel, pluginName, description, functions);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that contains the specified functions and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin AddFromFunctions(this ICollection<KernelPlugin> plugins, string pluginName, IEnumerable<KernelFunction>? functions) =>
        AddFromFunctions(plugins, pluginName, description: null, functions);

    /// <summary>Creates a plugin that contains the specified functions and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing the functions provided in <paramref name="functions"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin AddFromFunctions(this ICollection<KernelPlugin> plugins, string pluginName, string? description = null, IEnumerable<KernelFunction>? functions = null)
    {
        Verify.NotNull(plugins);

        var plugin = new DefaultKernelPlugin(pluginName, description, functions);
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static IKernelBuilderPlugins AddFromFunctions(this IKernelBuilderPlugins plugins, string pluginName, IEnumerable<KernelFunction>? functions) =>
        AddFromFunctions(plugins, pluginName, description: null, functions);

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static IKernelBuilderPlugins AddFromFunctions(this IKernelBuilderPlugins plugins, string pluginName, string? description = null, IEnumerable<KernelFunction>? functions = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton(KernelPluginFactory.CreateFromFunctions(pluginName, description, functions));

        return plugins;
    }
    #endregion

    #region CreatePluginFromDirectory
    /// <summary>Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>.</summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreatePluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);

        return CreatePluginFromPromptDirectory(pluginDirectory, pluginName, promptTemplateFactory, kernel.Services);
    }

    /// <summary>Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>.</summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT save.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    [Experimental("SKEXP0120")]
    public static KernelPlugin CreatePluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        JsonSerializerOptions jsonSerializerOptions,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(jsonSerializerOptions);

        return CreatePluginFromPromptDirectory(pluginDirectory, pluginName, promptTemplateFactory, kernel.Services, jsonSerializerOptions);
    }

    /// <summary>Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>.</summary>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [ExcludeFromCodeCoverage]
    private static KernelPlugin CreatePluginFromPromptDirectory(
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        IServiceProvider? services = null,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        const string ConfigFile = "config.json";
        const string PromptFile = "skprompt.txt";

        Verify.DirectoryExists(pluginDirectory);
        pluginName ??= new DirectoryInfo(pluginDirectory).Name;

        ILoggerFactory loggerFactory = services?.GetService<ILoggerFactory>() ?? NullLoggerFactory.Instance;

        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);

        var functions = new List<KernelFunction>();
        ILogger logger = loggerFactory.CreateLogger(typeof(Kernel)) ?? NullLogger.Instance;

        foreach (string functionDirectory in Directory.EnumerateDirectories(pluginDirectory))
        {
            var functionName = Path.GetFileName(functionDirectory);

            // Continue only if prompt template exists
            var promptPath = Path.Combine(functionDirectory, PromptFile);
            if (!File.Exists(promptPath))
            {
                continue;
            }

            // Load prompt configuration. Note: the configuration is optional.
            var configPath = Path.Combine(functionDirectory, ConfigFile);

            PromptTemplateConfig promptConfig;

            if (File.Exists(configPath))
            {
                promptConfig = jsonSerializerOptions != null ?
                    PromptTemplateConfig.FromJson(File.ReadAllText(configPath), jsonSerializerOptions) :
                    PromptTemplateConfig.FromJson(File.ReadAllText(configPath));
            }
            else
            {
                promptConfig = new PromptTemplateConfig();
            }

            promptConfig.Name = functionName;

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Config {0}: {1}", functionName, JsonSerializer.Serialize(promptConfig, JsonOptionsCache.WriteIndented));
            }

            // Load prompt template
            promptConfig.Template = File.ReadAllText(promptPath);
            IPromptTemplate promptTemplateInstance = factory.Create(promptConfig);

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Registering function {0}.{1} loaded from {2}", pluginName, functionName, functionDirectory);
            }

            functions.Add(KernelFunctionFactory.CreateFromPrompt(promptTemplateInstance, promptConfig, loggerFactory));
        }

        return KernelPluginFactory.CreateFromFunctions(pluginName, null, functions);
    }
    #endregion

    #region ImportPlugin/AddFromPromptDirectory
    /// <summary>
    /// Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>
    /// and imports it into the <paramref name="kernel"/>'s plugin collection.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin ImportPluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        KernelPlugin plugin = CreatePluginFromPromptDirectory(kernel, pluginDirectory, pluginName, promptTemplateFactory);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>
    /// and imports it into the <paramref name="kernel"/>'s plugin collection.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [Experimental("SKEXP0120")]
    public static KernelPlugin ImportPluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        JsonSerializerOptions jsonSerializerOptions,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        KernelPlugin plugin = CreatePluginFromPromptDirectory(kernel, pluginDirectory, jsonSerializerOptions, pluginName, promptTemplateFactory);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>
    /// Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>
    /// and adds it into the plugin collection.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IKernelBuilderPlugins AddFromPromptDirectory(
        this IKernelBuilderPlugins plugins,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton<KernelPlugin>(services =>
            CreatePluginFromPromptDirectory(pluginDirectory, pluginName, promptTemplateFactory, services));

        return plugins;
    }

    /// <summary>
    /// Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>
    /// and adds it into the plugin collection.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The same instance as <paramref name="plugins"/>.</returns>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT save.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    [Experimental("SKEXP0120")]
    public static IKernelBuilderPlugins AddFromPromptDirectory(
        this IKernelBuilderPlugins plugins,
        string pluginDirectory,
        JsonSerializerOptions jsonSerializerOptions,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(jsonSerializerOptions);

        plugins.Services.AddSingleton<KernelPlugin>(services =>
            CreatePluginFromPromptDirectory(pluginDirectory, pluginName, promptTemplateFactory, services, jsonSerializerOptions));

        return plugins;
    }
    #endregion

    #region InvokePromptAsync
    /// <summary>
    /// Invokes a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The result of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunction">The function failed to invoke successfully.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static Task<FunctionResult> InvokePromptAsync(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return kernel.InvokeAsync(function, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The result of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunction">The function failed to invoke successfully.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Experimental("SKEXP0120")]
    public static Task<FunctionResult> InvokePromptAsync(
        this Kernel kernel,
        JsonSerializerOptions jsonSerializerOptions,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            jsonSerializerOptions,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return kernel.InvokeAsync(function, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template and returns the results of type <typeparamref name="T"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The <typeparamref name="T"/> of the function result value.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunction">The function failed to invoke successfully.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static Task<T?> InvokePromptAsync<T>(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return kernel.InvokeAsync<T>(function, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template and returns the results of type <typeparamref name="T"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The <typeparamref name="T"/> of the function result value.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunction">The function failed to invoke successfully.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    [Experimental("SKEXP0120")]
    public static Task<T?> InvokePromptAsync<T>(
        this Kernel kernel,
        JsonSerializerOptions jsonSerializerOptions,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            jsonSerializerOptions,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return kernel.InvokeAsync<T>(function, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template and returns the results of type <typeparamref name="T"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The <typeparamref name="T"/> of the function result value.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunction">The function failed to invoke successfully.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    [EditorBrowsable(EditorBrowsableState.Never)]
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static Task<T?> InvokePromptAsync<T>(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments,
        string? templateFormat,
        IPromptTemplateFactory? promptTemplateFactory)
    {
        return InvokePromptAsync<T>(
            kernel,
            promptTemplate,
            arguments,
            templateFormat,
            promptTemplateFactory,
            CancellationToken.None);
    }
    #endregion

    #region InvokePromptStreamingAsync
    /// <summary>
    /// Invokes a prompt specified via a prompt template and streams its results.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IAsyncEnumerable<StreamingKernelContent> InvokePromptStreamingAsync(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptStreamingAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return function.InvokeStreamingAsync<StreamingKernelContent>(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template and streams its results.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    [Experimental("SKEXP0120")]
    public static IAsyncEnumerable<StreamingKernelContent> InvokePromptStreamingAsync(
        this Kernel kernel,
        JsonSerializerOptions jsonSerializerOptions,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            jsonSerializerOptions,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptStreamingAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return function.InvokeStreamingAsync<StreamingKernelContent>(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template and streams its results of type <typeparamref name="T"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IAsyncEnumerable<T> InvokePromptStreamingAsync<T>(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptStreamingAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return function.InvokeStreamingAsync<T>(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invokes a prompt specified via a prompt template and streams its results of type <typeparamref name="T"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT save.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT save.")]
    [Experimental("SKEXP0120")]
    public static IAsyncEnumerable<T> InvokePromptStreamingAsync<T>(
        this Kernel kernel,
        JsonSerializerOptions jsonSerializerOptions,
        string promptTemplate,
        KernelArguments? arguments = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFromPrompt.Create(
            promptTemplate,
            jsonSerializerOptions,
            functionName: KernelFunctionFromPrompt.CreateRandomFunctionName(nameof(InvokePromptStreamingAsync)),
            templateFormat: templateFormat,
            promptTemplateFactory: promptTemplateFactory,
            loggerFactory: kernel.LoggerFactory);

        return function.InvokeStreamingAsync<T>(kernel, arguments, cancellationToken);
    }
    #endregion

    #region Build for IKernelBuilder
    /// <summary>Constructs a new instance of <see cref="Kernel"/> using all of the settings configured on the builder.</summary>
    /// <returns>The new <see cref="Kernel"/> instance.</returns>
    /// <remarks>
    /// Every call to <see cref="Build"/> produces a new <see cref="Kernel"/> instance. The resulting <see cref="Kernel"/>
    /// instances will not share the same plugins collection or services provider (unless there are no services).
    /// </remarks>
    public static Kernel Build(this IKernelBuilder builder)
    {
        Verify.NotNull(builder);

        if (builder is KernelBuilder kb && !kb.AllowBuild)
        {
            throw new InvalidOperationException(
                "Build is not permitted on instances returned from AddKernel. " +
                "Resolve the Kernel from the service provider.");
        }

        IServiceProvider serviceProvider = EmptyServiceProvider.Instance;
        if (builder.Services is { Count: > 0 } services)
        {
            // This is a workaround for Microsoft.Extensions.DependencyInjection's GetKeyedServices not currently supporting
            // enumerating all services for a given type regardless of key.
            // https://github.com/dotnet/runtime/issues/91466
            // We need this support to, for example, allow IServiceSelector to pick from multiple named instances of an AI
            // service based on their characteristics. Until that is addressed, we work around it by injecting as a service all
            // of the keys used for a given type, such that Kernel can then query for this dictionary and enumerate it. This means
            // that such functionality will work when KernelBuilder is used to build the kernel but not when the IServiceProvider
            // is created via other means, such as if Kernel is directly created by DI. However, it allows us to create the APIs
            // the way we want them for the longer term and then subsequently fix the implementation when M.E.DI is fixed.
            Dictionary<Type, HashSet<object?>> typeToKeyMappings = [];
            foreach (ServiceDescriptor serviceDescriptor in services)
            {
                if (!typeToKeyMappings.TryGetValue(serviceDescriptor.ServiceType, out HashSet<object?>? keys))
                {
                    typeToKeyMappings[serviceDescriptor.ServiceType] = keys = [];
                }

                keys.Add(serviceDescriptor.ServiceKey);
            }
            services.AddKeyedSingleton(Kernel.KernelServiceTypeToKeyMappings, typeToKeyMappings);

            serviceProvider = services.BuildServiceProvider();
        }

        return new Kernel(serviceProvider);
    }
    #endregion
}
