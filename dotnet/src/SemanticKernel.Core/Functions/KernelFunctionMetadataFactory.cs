// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides factory methods for creating collections of <see cref="KernelFunctionMetadata"/>, such as
/// those backed by a prompt to be submitted to an LLM or those backed by a .NET method.
/// </summary>
public static class KernelFunctionMetadataFactory
{
    /// <summary>
    /// Creates a <see cref="KernelFunctionMetadata"/> enumeration for a method, specified via an <see cref="MethodInfo"/> instance.
    /// </summary>
    /// <param name="instanceType">Specifies the type of the object to extract <see cref="KernelFunctionMetadata"/> for.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="instanceType"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IEnumerable<KernelFunctionMetadata> CreateFromType(Type instanceType, ILoggerFactory? loggerFactory = null)
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
                functionMetadata.Add(KernelFunctionFromMethod.CreateMetadata(method, loggerFactory: loggerFactory));
            }
        }
        if (functionMetadata.Count == 0)
        {
            throw new ArgumentException($"The {instanceType} instance doesn't implement any [KernelFunction]-attributed methods.");
        }

        return functionMetadata;
    }

    /// <summary>
    /// Creates a <see cref="KernelFunctionMetadata"/> enumeration for a method, specified via an <see cref="MethodInfo"/> instance.
    /// </summary>
    /// <param name="instanceType">Specifies the type of the object to extract <see cref="KernelFunctionMetadata"/> for.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>A <see cref="KernelPlugin"/> containing <see cref="KernelFunction"/>s for all relevant members of <paramref name="instanceType"/>.</returns>
    /// <remarks>
    /// Methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static IEnumerable<KernelFunctionMetadata> CreateFromType([DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicMethods | DynamicallyAccessedMemberTypes.NonPublicMethods)] Type instanceType, JsonSerializerOptions jsonSerializerOptions, ILoggerFactory? loggerFactory = null)
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
                functionMetadata.Add(KernelFunctionFromMethod.CreateMetadata(method, jsonSerializerOptions, loggerFactory: loggerFactory));
            }
        }
        if (functionMetadata.Count == 0)
        {
            throw new ArgumentException($"The {instanceType} instance doesn't implement any [KernelFunction]-attributed methods.");
        }

        return functionMetadata;
    }
}
