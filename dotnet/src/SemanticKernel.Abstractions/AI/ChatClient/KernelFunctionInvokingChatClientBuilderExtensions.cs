// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>Provides extensions for configuring <see cref="KernelFunctionInvokingChatClient"/> instances.</summary>
[Experimental("SKEXP0001")]
public static class KernelFunctionInvokingChatClientBuilderExtensions
{
    /// <summary>
    /// Enables automatic function call invocation on the chat pipeline.
    /// </summary>
    /// <remarks>This works by adding an instance of <see cref="KernelFunctionInvokingChatClient"/> with default options.</remarks>
    /// <param name="builder">The <see cref="ChatClientBuilder"/> being used to build the chat pipeline.</param>
    /// <param name="loggerFactory">An optional <see cref="ILoggerFactory"/> to use to create a logger for logging function invocations.</param>
    /// <returns>The supplied <paramref name="builder"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="builder"/> is <see langword="null"/>.</exception>
    public static ChatClientBuilder UseKernelFunctionInvocation(
        this ChatClientBuilder builder,
        ILoggerFactory? loggerFactory = null)
    {
        _ = Throw.IfNull(builder);

        return builder.Use((innerClient, services) =>
        {
            loggerFactory ??= services.GetService<ILoggerFactory>();

            return new KernelFunctionInvokingChatClient(innerClient, loggerFactory, services);
        });
    }
}
