// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using AgentHooks;

namespace Microsoft.SemanticKernel.AgentHooks;

/// <summary>
/// Semantic Kernel filter that emits AGENT-HOOKS-0.1 interception points
/// (https://github.com/responsibleai/agent-hooks) and honours interceptor
/// verdicts.
/// </summary>
/// <remarks>
/// Mapping: <see cref="IFunctionInvocationFilter"/> brackets each kernel
/// function invocation as <c>pre_tool_call</c>/<c>post_tool_call</c>;
/// <see cref="IPromptRenderFilter"/> emits <c>pre_model_call</c> over the
/// rendered prompt before it is submitted; <see cref="IAutoFunctionInvocationFilter"/>
/// emits <c>post_model_call</c> once per model response that carries function
/// calls. <c>agent_startup</c> is emitted lazily on the first interception for
/// a kernel. The <c>input</c>, <c>output</c>, and <c>agent_shutdown</c> points
/// have no kernel-level seam and are not emitted by this adapter.
/// A block verdict surfaces as <see cref="AgentHooksInterceptionBlockedException"/>;
/// filter exceptions propagate, so enforcement fails closed. A
/// <c>post_tool_call</c> transform substitutes a JSON-typed function result,
/// which may differ from the original CLR result type.
/// </remarks>
public sealed class AgentHooksFilter :
    IFunctionInvocationFilter, IPromptRenderFilter, IAutoFunctionInvocationFilter
{
    private readonly AgentHooksOptions _options;
    private readonly IInterceptor[] _interceptors;
    private readonly ConditionalWeakTable<Kernel, KernelSession> _sessions = [];

    /// <summary>Creates the filter with the adapter options and the DI-resolved interceptors.</summary>
    public AgentHooksFilter(AgentHooksOptions options, IEnumerable<IInterceptor> interceptors)
    {
        this._options = options;
        this._interceptors = interceptors.ToArray();
    }

    /// <summary>Per-kernel emitter state: one agent-hooks session per <see cref="Kernel"/>.</summary>
    private sealed class KernelSession
    {
        public required InterceptionEmitter Emitter { get; init; }
        public required AgentContextBuilder Builder { get; init; }
        public bool StartupEmitted;
        public bool StartupBlocked;
        public readonly object StartupLock = new();
    }

    private KernelSession GetSession(Kernel kernel) =>
        this._sessions.GetValue(kernel, k =>
        {
            var emitter = new InterceptionEmitter(
                this._options.Mode, this._options.ApprovalResolver, this._options.InterceptorTimeout);
            emitter.SetComposition(this._options.Composition);
            if (this._options.RecordSink is not null)
            {
                emitter.SetRecordSink(this._options.RecordSink);
            }
            foreach (var interceptor in this._interceptors)
            {
                emitter.Register(interceptor, interceptor.GetType().Name);
            }
            var sessionId = this._options.SessionIdProvider?.Invoke(k) ?? Guid.NewGuid().ToString("N");
            return new KernelSession
            {
                Emitter = emitter,
                Builder = new AgentContextBuilder(this._options.AgentId, "semantic-kernel", sessionId),
            };
        });

    private async ValueTask<KernelSession> EnsureStartupAsync(Kernel kernel)
    {
        var session = this.GetSession(kernel);
        bool emitStartup = false;
        lock (session.StartupLock)
        {
            if (!session.StartupEmitted)
            {
                session.StartupEmitted = true;
                emitStartup = true;
            }
        }
        if (emitStartup)
        {
            var tools = kernel.Plugins
                .SelectMany(p => p.Select(f => $"{p.Name}.{f.Name}"))
                .ToArray();
            try
            {
                await this.EmitAsync(session, session.Builder.AgentStartup(tools)).ConfigureAwait(false);
            }
            catch (AgentHooksInterceptionBlockedException)
            {
                session.StartupBlocked = true;
                throw;
            }
        }

        // §6.1a: a blocked agent_startup means the session processes nothing.
        if (session.StartupBlocked)
        {
            throw new AgentHooksInterceptionBlockedException();
        }

        return session;
    }

    private async ValueTask<EmitOutcome> EmitAsync(KernelSession session, AgentContext ctx)
    {
        try
        {
            return await session.Emitter.EmitAsync(ctx).ConfigureAwait(false);
        }
        catch (InterceptionBlockedException ex)
        {
            throw new AgentHooksInterceptionBlockedException(ex.Result);
        }
    }

    /// <inheritdoc/>
    public async Task OnFunctionInvocationAsync(
        FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        var session = await this.EnsureStartupAsync(context.Kernel).ConfigureAwait(false);
        var callId = Guid.NewGuid().ToString("N");
        var name = context.Function.PluginName is { } plugin
            ? $"{plugin}.{context.Function.Name}"
            : context.Function.Name;

        var args = ToJsonObject(context.Arguments);
        var pre = await this.EmitAsync(session, session.Builder.PreToolCall(callId, name, args))
            .ConfigureAwait(false);

        // A transform verdict rewrote tool_call.args (§5.2): write the
        // effective target back into the kernel arguments before invocation.
        if (pre.Target is JsonObject effective && !JsonNode.DeepEquals(effective, args))
        {
            foreach (var (key, value) in effective)
            {
                context.Arguments[key] = value?.DeepClone();
            }
        }

        try
        {
            await next(context).ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is not AgentHooksInterceptionBlockedException)
        {
            // The invocation completed with an error: the contract still
            // brackets it with post_tool_call (tool_result.is_error = true).
            var errorArgs = pre.Target as JsonObject ?? args;
            var error = (JsonNode)(ex.GetType().Name);
            await this.EmitAsync(
                    session,
                    session.Builder.PostToolCall(callId, name, errorArgs, error, isError: true))
                .ConfigureAwait(false);
            throw;
        }

        var resultValue = SerializeResult(context.Result);
        var effectiveArgs = pre.Target as JsonObject ?? args;
        var post = await this.EmitAsync(
                session,
                session.Builder.PostToolCall(callId, name, effectiveArgs, resultValue, isError: false))
            .ConfigureAwait(false);

        // A transform at post_tool_call rewrote tool_result.value (§4.3):
        // substitute the function result the caller observes.
        if (post.Target is { } transformed && !JsonNode.DeepEquals(transformed, resultValue))
        {
            context.Result = new FunctionResult(context.Result, transformed.DeepClone());
        }
    }

    /// <inheritdoc/>
    public async Task OnPromptRenderAsync(
        PromptRenderContext context, Func<PromptRenderContext, Task> next)
    {
        await next(context).ConfigureAwait(false);
        if (context.RenderedPrompt is not { } prompt)
        {
            return;
        }

        var session = await this.EnsureStartupAsync(context.Kernel).ConfigureAwait(false);
        var messages = new JsonArray(new JsonObject
        {
            ["role"] = "user",
            ["content"] = prompt,
        });
        var modelId = context.ExecutionSettings?.ModelId ?? "unknown";
        var outcome = await this.EmitAsync(session, session.Builder.PreModelCall(modelId, messages))
            .ConfigureAwait(false);

        // A transform rewrote messages (§4.3): substitute the rendered
        // prompt that will be submitted to the model.
        if (outcome.Target is JsonArray rewritten &&
            rewritten.Count == 1 &&
            rewritten[0] is JsonObject m &&
            m["content"]?.GetValue<string>() is { } newPrompt &&
            !string.Equals(newPrompt, prompt, StringComparison.Ordinal))
        {
            context.RenderedPrompt = newPrompt;
        }
    }

    /// <inheritdoc/>
    public async Task OnAutoFunctionInvocationAsync(
        AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
    {
        // Emit post_model_call once per model response: the first function of
        // the first request carries the response that scheduled the calls.
        if (context.FunctionSequenceIndex == 0)
        {
            var session = await this.EnsureStartupAsync(context.Kernel).ConfigureAwait(false);
            var toolCalls = new JsonArray();
            foreach (var item in context.ChatMessageContent.Items.OfType<FunctionCallContent>())
            {
                toolCalls.Add(new JsonObject
                {
                    ["id"] = item.Id ?? string.Empty,
                    ["name"] = item.PluginName is { } p ? $"{p}.{item.FunctionName}" : item.FunctionName,
                    ["args"] = item.Arguments is { } fa ? ToJsonObject(fa) : new JsonObject(),
                });
            }
            var modelId = context.ExecutionSettings?.ModelId ?? "unknown";
            await this.EmitAsync(
                    session,
                    session.Builder.PostModelCall(
                        modelId,
                        context.ChatMessageContent.Content,
                        toolCalls,
                        finishReason: "tool_calls"))
                .ConfigureAwait(false);
        }

        await next(context).ConfigureAwait(false);
    }

    private static JsonObject ToJsonObject(IDictionary<string, object?> arguments)
    {
        var json = new JsonObject();
        foreach (var (key, value) in arguments)
        {
            json[key] = value switch
            {
                null => null,
                JsonNode node => node.DeepClone(),
                _ => SerializeValue(value),
            };
        }
        return json;
    }

    private static JsonNode? SerializeValue(object value)
    {
        try
        {
            return JsonSerializer.SerializeToNode(value);
        }
        catch (NotSupportedException)
        {
            return JsonValue.Create(value.ToString());
        }
    }

    private static JsonNode? SerializeResult(FunctionResult result) =>
        result.GetValue<object>() switch
        {
            null => null,
            JsonNode node => node.DeepClone(),
            var v => SerializeValue(v),
        };
}

#pragma warning disable RCS1194 // Implement exception constructors: constructed from a record only, mirroring KernelFunctionCanceledException.
/// <summary>
/// Thrown when the combined verdict for an emission blocks the guarded
/// operation (AGENT-HOOKS-0.1 §6). Carries the payload-free interception
/// record for the blocked emission.
/// </summary>
public sealed class AgentHooksInterceptionBlockedException : KernelException
{
    /// <summary>Creates the exception for a blocked emission carrying its record.</summary>
    public AgentHooksInterceptionBlockedException(InterceptionRecord record)
        : base($"agent-hooks blocked {record.InterceptionPoint.ToWireName()}: " +
               $"{record.Verdict.Reason ?? "no reason"}")
    {
        this.Record = record;
    }

    internal AgentHooksInterceptionBlockedException()
        : base("agent-hooks blocked this session: agent_startup was denied")
    {
    }

    /// <summary>
    /// The interception record for the blocked emission (§10.3), or
    /// <see langword="null"/> when the session was blocked at startup and no
    /// further emissions occur.
    /// </summary>
    public InterceptionRecord? Record { get; }
}
#pragma warning restore RCS1194
