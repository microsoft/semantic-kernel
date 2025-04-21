// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Internal;

/// <summary>
/// Invokes handler methods asynchronously using reflection.
/// The target methods must return either a ValueTask or a ValueTask{T}.
/// This class wraps the reflection call and provides a unified asynchronous invocation interface.
/// </summary>
internal sealed class HandlerInvoker
{
    /// <summary>
    /// Scans the provided agent for implemented handler interfaces (IHandle&lt;&gt; and IHandle&lt;,&gt;) via reflection,
    /// creates a corresponding <see cref="HandlerInvoker"/> for each handler method, and returns a dictionary that maps
    /// the message type (first generic argument of the interface) to its invoker.
    /// </summary>
    /// <param name="agent">The agent instance whose handler interfaces will be reflected.</param>
    /// <returns>A dictionary mapping message types to their corresponding <see cref="HandlerInvoker"/> instances.</returns>
    public static Dictionary<Type, HandlerInvoker> ReflectAgentHandlers(BaseAgent agent)
    {
        Type realType = agent.GetType();

        IEnumerable<Type> candidateInterfaces =
            realType.GetInterfaces()
                .Where(i => i.IsGenericType &&
                    (i.GetGenericTypeDefinition() == typeof(IHandle<>) ||
                    (i.GetGenericTypeDefinition() == typeof(IHandle<,>))));

        Dictionary<Type, HandlerInvoker> invokers = new();
        foreach (Type interface_ in candidateInterfaces)
        {
            MethodInfo handleAsync =
                interface_.GetMethod(nameof(IHandle<object>.HandleAsync), BindingFlags.Instance | BindingFlags.Public) ??
                throw new InvalidOperationException($"No handler method found for interface {interface_.FullName}");

            HandlerInvoker invoker = new(handleAsync, agent);
            invokers.Add(interface_.GetGenericArguments()[0], invoker);
        }

        return invokers;
    }

    /// <summary>
    /// Represents the asynchronous invocation function.
    /// </summary>
    private Func<object?, MessageContext, ValueTask<object?>> Invocation { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlerInvoker"/> class with the specified method information and target object.
    /// </summary>
    /// <param name="methodInfo">The MethodInfo representing the handler method to be invoked.</param>
    /// <param name="target">The target instance of the agent.</param>
    /// <exception cref="InvalidOperationException">Thrown if the target is missing for a non-static method or if the method's return type is not supported.</exception>
    private HandlerInvoker(MethodInfo methodInfo, BaseAgent target)
    {
        object? invocation(object? message, MessageContext messageContext) => methodInfo.Invoke(target, [message, messageContext]);

        Func<object?, MessageContext, ValueTask<object?>> getResultAsync;
        // Check if the method returns a non-generic ValueTask
        if (methodInfo.ReturnType.IsAssignableFrom(typeof(ValueTask)))
        {
            getResultAsync = async (message, messageContext) =>
            {
                // Await the ValueTask and return null as there is no result value.
                await ((ValueTask)invocation(message, messageContext)!).ConfigureAwait(false);
                return null;
            };
        }
        // Check if the method returns a generic ValueTask<T>
        else if (methodInfo.ReturnType.IsGenericType && methodInfo.ReturnType.GetGenericTypeDefinition() == typeof(ValueTask<>))
        {
            // Obtain the generic type argument for ValueTask<T>
            MethodInfo typeEraseAwait = typeof(HandlerInvoker)
                    .GetMethod(nameof(TypeEraseAwaitAsync), BindingFlags.NonPublic | BindingFlags.Static)!
                    .MakeGenericMethod(methodInfo.ReturnType.GetGenericArguments()[0]);

            getResultAsync = async (message, messageContext) =>
            {
                // Execute the invocation and then type-erase the ValueTask<T> to ValueTask<object?>
                object valueTask = invocation(message, messageContext)!;
                object? typelessValueTask = typeEraseAwait.Invoke(null, [valueTask]);

                Debug.Assert(typelessValueTask is ValueTask<object?>, "Expected ValueTask<object?> after type erasure.");

                return await ((ValueTask<object?>)typelessValueTask).ConfigureAwait(false);
            };
        }
        else
        {
            throw new InvalidOperationException($"Method {methodInfo.Name} must return a ValueTask or ValueTask<T>");
        }

        this.Invocation = getResultAsync;
    }

    /// <summary>
    /// Invokes the handler method asynchronously with the provided message and context.
    /// </summary>
    /// <param name="obj">The message to be passed as the first argument to the handler.</param>
    /// <param name="messageContext">The contextual information associated with the message.</param>
    /// <returns>A ValueTask representing the asynchronous operation, which yields the handler's result.</returns>
    public async ValueTask<object?> InvokeAsync(object? obj, MessageContext messageContext)
    {
        try
        {
            return await this.Invocation.Invoke(obj, messageContext).ConfigureAwait(false);
        }
        catch (TargetInvocationException ex)
        {
            // Unwrap the exception to get the original exception thrown by the handler method.
            Exception? innerException = ex.InnerException;
            if (innerException != null)
            {
                throw innerException;
            }
            throw;
        }
    }

    /// <summary>
    /// Awaits a generic ValueTask and returns its result as an object.
    /// This method is used to convert a ValueTask{T} to ValueTask{object?}.
    /// </summary>
    /// <typeparam name="T">The type of the result contained in the ValueTask.</typeparam>
    /// <param name="vt">The ValueTask to be awaited.</param>
    /// <returns>A ValueTask containing the result as an object.</returns>
    private static async ValueTask<object?> TypeEraseAwaitAsync<T>(ValueTask<T> vt)
    {
        return await vt.ConfigureAwait(false);
    }
}
