// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Buffers;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization.Metadata;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

#pragma warning disable IDE0009 // Use explicit 'this.' qualifier
#pragma warning disable IDE1006 // Missing static prefix s_ suffix

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>Provides factory methods for creating commonly used implementations of <see cref="AIFunction"/>.</summary>
internal static partial class AIFunctionFactory
{
    /// <summary>Holds the default options instance used when creating function.</summary>
    private static readonly AIFunctionFactoryOptions _defaultOptions = new();

    /// <summary>Creates an <see cref="AIFunction"/> instance for a method, specified via a delegate.</summary>
    /// <param name="method">The method to be represented via the created <see cref="AIFunction"/>.</param>
    /// <param name="options">Metadata to use to override defaults inferred from <paramref name="method"/>.</param>
    /// <returns>The created <see cref="AIFunction"/> for invoking <paramref name="method"/>.</returns>
    /// <remarks>
    /// <para>
    /// Return values are serialized to <see cref="JsonElement"/> using <paramref name="options"/>'s
    /// <see cref="AIFunctionFactoryOptions.SerializerOptions"/>. Arguments that are not already of the expected type are
    /// marshaled to the expected type via JSON and using <paramref name="options"/>'s
    /// <see cref="AIFunctionFactoryOptions.SerializerOptions"/>. If the argument is a <see cref="JsonElement"/>,
    /// <see cref="JsonDocument"/>, or <see cref="JsonNode"/>, it is deserialized directly. If the argument is anything else unknown,
    /// it is round-tripped through JSON, serializing the object as JSON and then deserializing it to the expected type.
    /// </para>
    /// </remarks>
    public static AIFunction Create(Delegate method, AIFunctionFactoryOptions? options)
    {
        Verify.NotNull(method);

        return ReflectionAIFunction.Build(method.Method, method.Target, options ?? _defaultOptions);
    }

    /// <summary>Creates an <see cref="AIFunction"/> instance for a method, specified via a delegate.</summary>
    /// <param name="method">The method to be represented via the created <see cref="AIFunction"/>.</param>
    /// <param name="name">The name to use for the <see cref="AIFunction"/>.</param>
    /// <param name="description">The description to use for the <see cref="AIFunction"/>.</param>
    /// <param name="serializerOptions">The <see cref="JsonSerializerOptions"/> used to marshal function parameters and any return value.</param>
    /// <returns>The created <see cref="AIFunction"/> for invoking <paramref name="method"/>.</returns>
    /// <remarks>
    /// <para>
    /// Return values are serialized to <see cref="JsonElement"/> using <paramref name="serializerOptions"/>.
    /// Arguments that are not already of the expected type are marshaled to the expected type via JSON and using
    /// <paramref name="serializerOptions"/>. If the argument is a <see cref="JsonElement"/>, <see cref="JsonDocument"/>,
    /// or <see cref="JsonNode"/>, it is deserialized directly. If the argument is anything else unknown, it is
    /// round-tripped through JSON, serializing the object as JSON and then deserializing it to the expected type.
    /// </para>
    /// </remarks>
    public static AIFunction Create(Delegate method, string? name = null, string? description = null, JsonSerializerOptions? serializerOptions = null)
    {
        Verify.NotNull(method);

        AIFunctionFactoryOptions createOptions = serializerOptions is null && name is null && description is null
            ? _defaultOptions
            : new()
            {
                Name = name,
                Description = description,
                SerializerOptions = serializerOptions,
            };

        return ReflectionAIFunction.Build(method.Method, method.Target, createOptions);
    }

    /// <summary>
    /// Creates an <see cref="AIFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="AIFunction"/>.</param>
    /// <param name="target">
    /// The target object for the <paramref name="method"/> if it represents an instance method.
    /// This should be <see langword="null"/> if and only if <paramref name="method"/> is a static method.
    /// </param>
    /// <param name="options">Metadata to use to override defaults inferred from <paramref name="method"/>.</param>
    /// <returns>The created <see cref="AIFunction"/> for invoking <paramref name="method"/>.</returns>
    /// <remarks>
    /// <para>
    /// Return values are serialized to <see cref="JsonElement"/> using <paramref name="options"/>'s
    /// <see cref="AIFunctionFactoryOptions.SerializerOptions"/>. Arguments that are not already of the expected type are
    /// marshaled to the expected type via JSON and using <paramref name="options"/>'s
    /// <see cref="AIFunctionFactoryOptions.SerializerOptions"/>. If the argument is a <see cref="JsonElement"/>,
    /// <see cref="JsonDocument"/>, or <see cref="JsonNode"/>, it is deserialized directly. If the argument is anything else unknown,
    /// it is round-tripped through JSON, serializing the object as JSON and then deserializing it to the expected type.
    /// </para>
    /// </remarks>
    public static AIFunction Create(MethodInfo method, object? target, AIFunctionFactoryOptions? options)
    {
        Verify.NotNull(method);

        return ReflectionAIFunction.Build(method, target, options ?? _defaultOptions);
    }

    /// <summary>
    /// Creates an <see cref="AIFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="AIFunction"/>.</param>
    /// <param name="target">
    /// The target object for the <paramref name="method"/> if it represents an instance method.
    /// This should be <see langword="null"/> if and only if <paramref name="method"/> is a static method.
    /// </param>
    /// <param name="name">The name to use for the <see cref="AIFunction"/>.</param>
    /// <param name="description">The description to use for the <see cref="AIFunction"/>.</param>
    /// <param name="serializerOptions">The <see cref="JsonSerializerOptions"/> used to marshal function parameters and return value.</param>
    /// <returns>The created <see cref="AIFunction"/> for invoking <paramref name="method"/>.</returns>
    /// <remarks>
    /// <para>
    /// Return values are serialized to <see cref="JsonElement"/> using <paramref name="serializerOptions"/>.
    /// Arguments that are not already of the expected type are marshaled to the expected type via JSON and using
    /// <paramref name="serializerOptions"/>. If the argument is a <see cref="JsonElement"/>, <see cref="JsonDocument"/>,
    /// or <see cref="JsonNode"/>, it is deserialized directly. If the argument is anything else unknown, it is
    /// round-tripped through JSON, serializing the object as JSON and then deserializing it to the expected type.
    /// </para>
    /// </remarks>
    public static AIFunction Create(MethodInfo method, object? target, string? name = null, string? description = null, JsonSerializerOptions? serializerOptions = null)
    {
        Verify.NotNull(method);

        AIFunctionFactoryOptions createOptions = serializerOptions is null && name is null && description is null
            ? _defaultOptions
            : new()
            {
                Name = name,
                Description = description,
                SerializerOptions = serializerOptions,
            };

        return ReflectionAIFunction.Build(method, target, createOptions);
    }

    private sealed class ReflectionAIFunction : AIFunction
    {
        public static ReflectionAIFunction Build(MethodInfo method, object? target, AIFunctionFactoryOptions options)
        {
            Verify.NotNull(method);

            if (method.ContainsGenericParameters)
            {
                throw new ArgumentException("Open generic methods are not supported", nameof(method));
            }

            if (!method.IsStatic && target is null)
            {
                throw new ArgumentNullException(nameof(target), "Target must not be null for an instance method.");
            }

            ReflectionAIFunctionDescriptor functionDescriptor = ReflectionAIFunctionDescriptor.GetOrCreate(method, options);

            if (target is null && options.AdditionalProperties is null)
            {
                // We can use a cached value for static methods not specifying additional properties.
                return functionDescriptor.CachedDefaultInstance ??= new(functionDescriptor, target, options);
            }

            return new(functionDescriptor, target, options);
        }

        private ReflectionAIFunction(ReflectionAIFunctionDescriptor functionDescriptor, object? target, AIFunctionFactoryOptions options)
        {
            FunctionDescriptor = functionDescriptor;
            Target = target;
            AdditionalProperties = options.AdditionalProperties ?? EmptyReadOnlyDictionary<string, object?>.Instance;
        }

        public ReflectionAIFunctionDescriptor FunctionDescriptor { get; }
        public object? Target { get; }
        public override IReadOnlyDictionary<string, object?> AdditionalProperties { get; }
        public override string Name => FunctionDescriptor.Name;
        public override string Description => FunctionDescriptor.Description;
        public override MethodInfo UnderlyingMethod => FunctionDescriptor.Method;
        public override JsonElement JsonSchema => FunctionDescriptor.JsonSchema;
        public override JsonSerializerOptions JsonSerializerOptions => FunctionDescriptor.JsonSerializerOptions;
        protected override Task<object?> InvokeCoreAsync(
            IEnumerable<KeyValuePair<string, object?>>? arguments,
            CancellationToken cancellationToken)
        {
            var paramMarshallers = FunctionDescriptor.ParameterMarshallers;
            object?[] args = paramMarshallers.Length != 0 ? new object?[paramMarshallers.Length] : [];

            IReadOnlyDictionary<string, object?> argDict =
                arguments is null || args.Length == 0 ? EmptyReadOnlyDictionary<string, object?>.Instance :
                arguments as IReadOnlyDictionary<string, object?> ??
                arguments.
#if NET8_0_OR_GREATER
                    ToDictionary();
#else
                    ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
#endif
            for (int i = 0; i < args.Length; i++)
            {
                args[i] = paramMarshallers[i](argDict, cancellationToken);
            }

            return FunctionDescriptor.ReturnParameterMarshaller(ReflectionInvoke(FunctionDescriptor.Method, Target, args), cancellationToken);
        }
    }

    /// <summary>
    /// A descriptor for a .NET method-backed AIFunction that precomputes its marshalling delegates and JSON schema.
    /// </summary>
    private sealed class ReflectionAIFunctionDescriptor
    {
        private const int InnerCacheSoftLimit = 512;
        private static readonly ConditionalWeakTable<JsonSerializerOptions, ConcurrentDictionary<DescriptorKey, ReflectionAIFunctionDescriptor>> _descriptorCache = new();

        /// <summary>A boxed <see cref="CancellationToken.None"/>.</summary>
        private static readonly object? _boxedDefaultCancellationToken = default(CancellationToken);

        /// <summary>
        /// Gets or creates a descriptors using the specified method and options.
        /// </summary>
        public static ReflectionAIFunctionDescriptor GetOrCreate(MethodInfo method, AIFunctionFactoryOptions options)
        {
            JsonSerializerOptions serializerOptions = options.SerializerOptions ?? AIJsonUtilities.DefaultOptions;
            AIJsonSchemaCreateOptions schemaOptions = options.JsonSchemaCreateOptions ?? AIJsonSchemaCreateOptions.Default;
            serializerOptions.MakeReadOnly();
            ConcurrentDictionary<DescriptorKey, ReflectionAIFunctionDescriptor> innerCache = _descriptorCache.GetOrCreateValue(serializerOptions);

            DescriptorKey key = new(method, options.Name, options.Description, schemaOptions);
            if (innerCache.TryGetValue(key, out ReflectionAIFunctionDescriptor? descriptor))
            {
                return descriptor;
            }

            descriptor = new(key, serializerOptions);
            return innerCache.Count < InnerCacheSoftLimit
                ? innerCache.GetOrAdd(key, descriptor)
                : descriptor;
        }

        private ReflectionAIFunctionDescriptor(DescriptorKey key, JsonSerializerOptions serializerOptions)
        {
            // Get marshaling delegates for parameters.
            ParameterInfo[] parameters = key.Method.GetParameters();
            ParameterMarshallers = new Func<IReadOnlyDictionary<string, object?>, CancellationToken, object?>[parameters.Length];
            for (int i = 0; i < parameters.Length; i++)
            {
                ParameterMarshallers[i] = GetParameterMarshaller(serializerOptions, parameters[i]);
            }

            // Get a marshaling delegate for the return value.
            ReturnParameterMarshaller = GetReturnParameterMarshaller(key.Method, serializerOptions);

            Method = key.Method;
            Name = key.Name ?? GetFunctionName(key.Method);
            Description = key.Description ?? key.Method.GetCustomAttribute<DescriptionAttribute>(inherit: true)?.Description ?? string.Empty;
            JsonSerializerOptions = serializerOptions;
            JsonSchema = AIJsonUtilities.CreateFunctionJsonSchema(
                key.Method,
                Name,
                Description,
                serializerOptions,
                key.SchemaOptions);
        }

        public string Name { get; }
        public string Description { get; }
        public MethodInfo Method { get; }
        public JsonSerializerOptions JsonSerializerOptions { get; }
        public JsonElement JsonSchema { get; }
        public Func<IReadOnlyDictionary<string, object?>, CancellationToken, object?>[] ParameterMarshallers { get; }
        public Func<object?, CancellationToken, Task<object?>> ReturnParameterMarshaller { get; }
        public ReflectionAIFunction? CachedDefaultInstance { get; set; }

        private static string GetFunctionName(MethodInfo method)
        {
            // Get the function name to use.
            string name = SanitizeMemberName(method.Name);

            const string AsyncSuffix = "Async";
            if (IsAsyncMethod(method) &&
                name.EndsWith(AsyncSuffix, StringComparison.Ordinal) &&
                name.Length > AsyncSuffix.Length)
            {
                name = name.Substring(0, name.Length - AsyncSuffix.Length);
            }

            return name;

            static bool IsAsyncMethod(MethodInfo method)
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
        }

        /// <summary>
        /// Gets a delegate for handling the marshaling of a parameter.
        /// </summary>
        private static Func<IReadOnlyDictionary<string, object?>, CancellationToken, object?> GetParameterMarshaller(
            JsonSerializerOptions serializerOptions,
            ParameterInfo parameter)
        {
            if (string.IsNullOrWhiteSpace(parameter.Name))
            {
                throw new ArgumentException("Parameter is missing a name.", nameof(parameter));
            }

            // Resolve the contract used to marshal the value from JSON -- can throw if not supported or not found.
            Type parameterType = parameter.ParameterType;
            JsonTypeInfo typeInfo = serializerOptions.GetTypeInfo(parameterType);

            // For CancellationToken parameters, we always bind to the token passed directly to InvokeAsync.
            if (parameterType == typeof(CancellationToken))
            {
                return static (_, cancellationToken) =>
                    cancellationToken == default ? _boxedDefaultCancellationToken : // optimize common case of a default CT to avoid boxing
                    cancellationToken;
            }

            // For all other parameters, create a marshaller that tries to extract the value from the arguments dictionary.
            return (arguments, _) =>
            {
                // If the parameter has an argument specified in the dictionary, return that argument.
                if (arguments.TryGetValue(parameter.Name, out object? value))
                {
                    return value switch
                    {
                        null => null, // Return as-is if null -- if the parameter is a struct this will be handled by MethodInfo.Invoke
                        _ when parameterType.IsInstanceOfType(value) => value, // Do nothing if value is assignable to parameter type
                        JsonElement element => JsonSerializer.Deserialize(element, typeInfo),
                        JsonDocument doc => JsonSerializer.Deserialize(doc, typeInfo),
                        JsonNode node => JsonSerializer.Deserialize(node, typeInfo),
                        _ => MarshallViaJsonRoundtrip(value),
                    };

                    object? MarshallViaJsonRoundtrip(object value)
                    {
#pragma warning disable CA1031 // Do not catch general exception types
                        try
                        {
                            string json = JsonSerializer.Serialize(value, serializerOptions.GetTypeInfo(value.GetType()));
                            return JsonSerializer.Deserialize(json, typeInfo);
                        }
                        catch
                        {
                            // Eat any exceptions and fall back to the original value to force a cast exception later on.
                            return value;
                        }
#pragma warning restore CA1031
                    }
                }

                // There was no argument for the parameter in the dictionary.
                // Does it have a default value?
                if (parameter.HasDefaultValue)
                {
                    return parameter.DefaultValue;
                }

                // Leave it empty.
                return null;
            };
        }

        /// <summary>
        /// Gets a delegate for handling the result value of a method, converting it into the <see cref="Task{FunctionResult}"/> to return from the invocation.
        /// </summary>
        private static Func<object?, CancellationToken, Task<object?>> GetReturnParameterMarshaller(MethodInfo method, JsonSerializerOptions serializerOptions)
        {
            Type returnType = method.ReturnType;
            JsonTypeInfo returnTypeInfo;

            // Void
            if (returnType == typeof(void))
            {
                return static (_, _) => Task.FromResult<object?>(null);
            }

            // Task
            if (returnType == typeof(Task))
            {
                return async static (result, _) =>
                {
                    await ((Task)ThrowIfNullResult(result)).ConfigureAwait(false);
                    return null;
                };
            }

            // ValueTask
            if (returnType == typeof(ValueTask))
            {
                return async static (result, _) =>
                {
                    await ((ValueTask)ThrowIfNullResult(result)).ConfigureAwait(false);
                    return null;
                };
            }

            if (returnType.IsGenericType)
            {
                // Task<T>
                if (returnType.GetGenericTypeDefinition() == typeof(Task<>))
                {
                    MethodInfo taskResultGetter = GetMethodFromGenericMethodDefinition(returnType, _taskGetResult);
                    returnTypeInfo = serializerOptions.GetTypeInfo(taskResultGetter.ReturnType);
                    return async (taskObj, cancellationToken) =>
                    {
                        await ((Task)ThrowIfNullResult(taskObj)).ConfigureAwait(false);
                        object? result = ReflectionInvoke(taskResultGetter, taskObj, null);
                        return await SerializeResultAsync(result, returnTypeInfo, cancellationToken).ConfigureAwait(false);
                    };
                }

                // ValueTask<T>
                if (returnType.GetGenericTypeDefinition() == typeof(ValueTask<>))
                {
                    MethodInfo valueTaskAsTask = GetMethodFromGenericMethodDefinition(returnType, _valueTaskAsTask);
                    MethodInfo asTaskResultGetter = GetMethodFromGenericMethodDefinition(valueTaskAsTask.ReturnType, _taskGetResult);
                    returnTypeInfo = serializerOptions.GetTypeInfo(asTaskResultGetter.ReturnType);
                    return async (taskObj, cancellationToken) =>
                    {
                        var task = (Task)ReflectionInvoke(valueTaskAsTask, ThrowIfNullResult(taskObj), null)!;
                        await task.ConfigureAwait(false);
                        object? result = ReflectionInvoke(asTaskResultGetter, task, null);
                        return await SerializeResultAsync(result, returnTypeInfo, cancellationToken).ConfigureAwait(false);
                    };
                }
            }

            // For everything else, just serialize the result as-is.
            returnTypeInfo = serializerOptions.GetTypeInfo(returnType);
            return (result, cancellationToken) => SerializeResultAsync(result, returnTypeInfo, cancellationToken);

            static async Task<object?> SerializeResultAsync(object? result, JsonTypeInfo returnTypeInfo, CancellationToken cancellationToken)
            {
                if (returnTypeInfo.Kind is JsonTypeInfoKind.None)
                {
                    // Special-case trivial contracts to avoid the more expensive general-purpose serialization path.
                    return JsonSerializer.SerializeToElement(result, returnTypeInfo);
                }

                // Serialize asynchronously to support potential IAsyncEnumerable responses.
                using PooledMemoryStream stream = new();
#if NET9_0_OR_GREATER
                await JsonSerializer.SerializeAsync(stream, result, returnTypeInfo, cancellationToken).ConfigureAwait(false);
                Utf8JsonReader reader = new(stream.GetBuffer());
                return JsonElement.ParseValue(ref reader);
#else
                await JsonSerializer.SerializeAsync(stream, result, returnTypeInfo, cancellationToken).ConfigureAwait(false);
                stream.Position = 0;
                var serializerOptions = _defaultOptions.SerializerOptions ?? AIJsonUtilities.DefaultOptions;
                return await JsonSerializer.DeserializeAsync(stream, serializerOptions.GetTypeInfo(typeof(JsonElement)), cancellationToken).ConfigureAwait(false);
#endif
            }

            // Throws an exception if a result is found to be null unexpectedly
            static object ThrowIfNullResult(object? result) => result ?? throw new InvalidOperationException("Function returned null unexpectedly.");
        }

        private static readonly MethodInfo _taskGetResult = typeof(Task<>).GetProperty(nameof(Task<int>.Result), BindingFlags.Instance | BindingFlags.Public)!.GetMethod!;
        private static readonly MethodInfo _valueTaskAsTask = typeof(ValueTask<>).GetMethod(nameof(ValueTask<int>.AsTask), BindingFlags.Instance | BindingFlags.Public)!;

        private static MethodInfo GetMethodFromGenericMethodDefinition(Type specializedType, MethodInfo genericMethodDefinition)
        {
            Debug.Assert(specializedType.IsGenericType && specializedType.GetGenericTypeDefinition() == genericMethodDefinition.DeclaringType, "generic member definition doesn't match type.");
#if NET
            return (MethodInfo)specializedType.GetMemberWithSameMetadataDefinitionAs(genericMethodDefinition);
#else
#pragma warning disable S3011 // Reflection should not be used to increase accessibility of classes, methods, or fields
            const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance;
#pragma warning restore S3011 // Reflection should not be used to increase accessibility of classes, methods, or fields
            return specializedType.GetMethods(All).First(m => m.MetadataToken == genericMethodDefinition.MetadataToken);
#endif
        }

        private record struct DescriptorKey(MethodInfo Method, string? Name, string? Description, AIJsonSchemaCreateOptions SchemaOptions);
    }

    /// <summary>
    /// Removes characters from a .NET member name that shouldn't be used in an AI function name.
    /// </summary>
    /// <param name="memberName">The .NET member name that should be sanitized.</param>
    /// <returns>
    /// Replaces non-alphanumeric characters in the identifier with the underscore character.
    /// Primarily intended to remove characters produced by compiler-generated method name mangling.
    /// </returns>
    internal static string SanitizeMemberName(string memberName)
    {
        Verify.NotNull(memberName);
        return InvalidNameCharsRegex().Replace(memberName, "_");
    }

    /// <summary>Regex that flags any character other than ASCII digits or letters or the underscore.</summary>
#if NET
    [GeneratedRegex("[^0-9A-Za-z_]")]
    private static partial Regex InvalidNameCharsRegex();
#else
    private static Regex InvalidNameCharsRegex() => _invalidNameCharsRegex;
    private static readonly Regex _invalidNameCharsRegex = new("[^0-9A-Za-z_]", RegexOptions.Compiled);
#endif

    /// <summary>Invokes the MethodInfo with the specified target object and arguments.</summary>
    private static object? ReflectionInvoke(MethodInfo method, object? target, object?[]? arguments)
    {
#if NET
        return method.Invoke(target, BindingFlags.DoNotWrapExceptions, binder: null, arguments, culture: null);
#else
        try
        {
            return method.Invoke(target, BindingFlags.Default, binder: null, arguments, culture: null);
        }
        catch (TargetInvocationException e) when (e.InnerException is not null)
        {
            // If we're targeting .NET Framework, such that BindingFlags.DoNotWrapExceptions
            // is ignored, the original exception will be wrapped in a TargetInvocationException.
            // Unwrap it and throw that original exception, maintaining its stack information.
            System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(e.InnerException).Throw();
            throw;
        }
#endif
    }

    /// <summary>
    /// Implements a simple write-only memory stream that uses pooled buffers.
    /// </summary>
    private sealed class PooledMemoryStream : Stream
    {
        private const int DefaultBufferSize = 4096;
        private byte[] _buffer;
        private int _position;

        public PooledMemoryStream(int initialCapacity = DefaultBufferSize)
        {
            _buffer = ArrayPool<byte>.Shared.Rent(initialCapacity);
            _position = 0;
        }

        public ReadOnlySpan<byte> GetBuffer() => _buffer.AsSpan(0, _position);
        public override bool CanWrite => true;
        public override bool CanRead => false;
        public override bool CanSeek => false;
        public override long Length => _position;
        public override long Position
        {
            get => _position;
            set => throw new NotSupportedException();
        }

        public override void Write(byte[] buffer, int offset, int count)
        {
            EnsureNotDisposed();
            EnsureCapacity(_position + count);

            Buffer.BlockCopy(buffer, offset, _buffer, _position, count);
            _position += count;
        }

        public override void Flush()
        {
        }

        public override int Read(byte[] buffer, int offset, int count) => throw new NotSupportedException();
        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException();

        protected override void Dispose(bool disposing)
        {
            if (_buffer is not null)
            {
                ArrayPool<byte>.Shared.Return(_buffer);
                _buffer = null!;
            }

            base.Dispose(disposing);
        }

        private void EnsureCapacity(int requiredCapacity)
        {
            if (requiredCapacity <= _buffer.Length)
            {
                return;
            }

            int newCapacity = Math.Max(requiredCapacity, _buffer.Length * 2);
            byte[] newBuffer = ArrayPool<byte>.Shared.Rent(newCapacity);
            Buffer.BlockCopy(_buffer, 0, newBuffer, 0, _position);

            ArrayPool<byte>.Shared.Return(_buffer);
            _buffer = newBuffer;
        }

        private void EnsureNotDisposed()
        {
            if (_buffer is null)
            {
                Throw();
                static void Throw() => throw new ObjectDisposedException(nameof(PooledMemoryStream));
            }
        }
    }
}
