﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides factory methods for creating commonly-used implementations of <see cref="KernelFunction"/>, such as
/// those backed by a prompt to be submitted to an LLM or those backed by a .NET method.
/// </summary>
public static class KernelFunctionFactory
{
    #region FromMethod
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    public static KernelFunction CreateFromMethod(
        Delegate method,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null) =>
        CreateFromMethod(method.Method, method.Target, functionName, description, parameters, returnParameter, loggerFactory);

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="options">Optional function creation options.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    public static KernelFunction CreateFromMethod(
        Delegate method,
        KernelFunctionFromMethodOptions? options) =>
        CreateFromMethod(method.Method, method.Target, options);

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">The description to use for the function. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to ones derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    public static KernelFunction CreateFromMethod(
        MethodInfo method,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null,
        ILoggerFactory? loggerFactory = null) =>
        KernelFunctionFromMethod.Create(method, target, functionName, description, parameters, returnParameter, loggerFactory);

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="options">Optional function creation options.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking <paramref name="method"/>.</returns>
    public static KernelFunction CreateFromMethod(
        MethodInfo method,
        object? target,
        KernelFunctionFromMethodOptions? options) =>
        KernelFunctionFromMethod.Create(method, target, options);
    #endregion

    #region FromPrompt

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="executionSettings">Default execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to a randomly generated name.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFromPrompt(
        string promptTemplate,
        PromptExecutionSettings? executionSettings = null,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null) =>
        KernelFunctionFromPrompt.Create(
            promptTemplate,
            CreateSettingsDictionary(executionSettings is null ? null : [executionSettings]),
            functionName,
            description,
            templateFormat,
            promptTemplateFactory,
            loggerFactory);

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="executionSettings">Default execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">The name to use for the function. If null, it will default to a randomly generated name.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">The template format of <paramref name="promptTemplate"/>. This must be provided if <paramref name="promptTemplateFactory"/> is not null.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptTemplate"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFromPrompt(
        string promptTemplate,
        IEnumerable<PromptExecutionSettings>? executionSettings,
        string? functionName = null,
        string? description = null,
        string? templateFormat = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null) =>
        KernelFunctionFromPrompt.Create(promptTemplate, CreateSettingsDictionary(executionSettings), functionName, description, templateFormat, promptTemplateFactory, loggerFactory);

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template configuration.
    /// </summary>
    /// <param name="promptConfig">Configuration information describing the prompt.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the <paramref name="promptConfig"/> into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFromPrompt(
        PromptTemplateConfig promptConfig,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null) => KernelFunctionFromPrompt.Create(promptConfig, promptTemplateFactory, loggerFactory);

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template and prompt template configuration.
    /// </summary>
    /// <param name="promptTemplate">Prompt template for the function.</param>
    /// <param name="promptConfig">Configuration information describing the prompt.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/> for invoking the prompt.</returns>
    public static KernelFunction CreateFromPrompt(
        IPromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig,
        ILoggerFactory? loggerFactory = null) => KernelFunctionFromPrompt.Create(promptTemplate, promptConfig, loggerFactory);
    #endregion

    #region Metadata
    /// <summary>
    /// Returns a list of <see cref="KernelFunctionMetadata"/> instances for the specified type.
    /// </summary>
    /// <param name="instanceType">Specifies the type of the object to extract <see cref="KernelFunctionMetadata"/> for.</param>
    public static List<KernelFunctionMetadata> GetMetadataForType(Type instanceType)
    {
        Verify.NotNull(instanceType);

        MethodInfo[] methods = instanceType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static);

        // Filter out non-KernelFunctions and fail if two functions have the same name (with or without the same casing).
        var functionMetadata = new List<KernelFunctionMetadata>();
        KernelFunctionFromMethodOptions options = new();
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<KernelFunctionAttribute>() is not null)
            {
                functionMetadata.Add(KernelFunctionFromMethod.Create(method, null, options).Metadata);
            }
        }
        if (functionMetadata.Count == 0)
        {
            throw new ArgumentException($"The {instanceType} instance doesn't implement any [KernelFunction]-attributed methods.");
        }

        return functionMetadata;
    }

    #endregion

    /// <summary>
    /// Wraps the specified settings into a dictionary with the default service ID as the key.
    /// </summary>
    [return: NotNullIfNotNull(nameof(settings))]
    private static Dictionary<string, PromptExecutionSettings>? CreateSettingsDictionary(IEnumerable<PromptExecutionSettings>? settings) =>
        settings?.ToDictionary(s => s.ServiceId ?? PromptExecutionSettings.DefaultServiceId, s => s);
}
