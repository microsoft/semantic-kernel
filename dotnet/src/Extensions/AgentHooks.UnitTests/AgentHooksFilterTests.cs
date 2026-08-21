// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using AgentHooks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AgentHooks;
using Xunit;

namespace SemanticKernel.Extensions.AgentHooks.UnitTests;

public sealed class AgentHooksFilterTests
{
    private static Kernel BuildKernel(
        IInterceptor interceptor,
        Action<AgentHooksOptions>? configure = null,
        List<InterceptionRecord>? records = null)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(interceptor);
        builder.Services.AddAgentHooks(o =>
        {
            o.AgentId = "test-agent";
            if (records is not null)
            {
                o.RecordSink = records.Add;
            }
            configure?.Invoke(o);
        });
        return builder.Build();
    }

    private sealed class ScriptedInterceptor(Func<AgentContext, Verdict> script) : IInterceptor
    {
        public ValueTask<Verdict> InterceptAsync(AgentContext context, CancellationToken ct = default) =>
            ValueTask.FromResult(script(context));
    }

    private static string PointOf(AgentContext ctx) =>
        ctx.Json["interception_point"]!.GetValue<string>();

    [Fact]
    public async Task DenyAtPreToolCallBlocksFunctionInvocationAsync()
    {
        bool invoked = false;
        var kernel = BuildKernel(new ScriptedInterceptor(ctx =>
            PointOf(ctx) == "pre_tool_call"
                ? new Verdict(Decision.Deny, "blocked_by_test")
                : Verdict.Allow));
        var function = KernelFunctionFactory.CreateFromMethod(
            () => { invoked = true; return "ran"; }, "Probe");

        var ex = await Assert.ThrowsAsync<AgentHooksInterceptionBlockedException>(
            () => kernel.InvokeAsync(function));

        Assert.False(invoked);
        Assert.Equal("blocked_by_test", ex.Record!.Verdict.Reason);
        Assert.Equal(InterceptionPoint.PreToolCall, ex.Record!.InterceptionPoint);
    }

    [Fact]
    public async Task TransformAtPreToolCallRewritesArgumentsAsync()
    {
        string? observed = null;
        var kernel = BuildKernel(new ScriptedInterceptor(ctx =>
            PointOf(ctx) == "pre_tool_call"
                ? new Verdict(Decision.Transform,
                    Transform: new Transform("$target.text", JsonValue.Create("redacted")))
                : Verdict.Allow));
        var function = KernelFunctionFactory.CreateFromMethod(
            (string text) => { observed = text; return text; }, "Echo");

        var result = await kernel.InvokeAsync(function, new() { ["text"] = "secret" });

        Assert.Equal("redacted", observed);
        Assert.Equal("redacted", result.GetValue<string>());
    }

    [Fact]
    public async Task LiftableDenyWithApprovalProceedsAsync()
    {
        var resolver = new ApproveAllResolver();
        var kernel = BuildKernel(
            new ScriptedInterceptor(ctx =>
                PointOf(ctx) == "pre_tool_call"
                    ? Verdict.Escalate("needs_review")
                    : Verdict.Allow),
            o => o.ApprovalResolver = resolver);
        var function = KernelFunctionFactory.CreateFromMethod(() => "ran", "Probe");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("ran", result.GetValue<string>());
        Assert.True(resolver.Consulted);
    }

    [Fact]
    public async Task LiftableDenyWithoutResolverBlocksAsync()
    {
        var kernel = BuildKernel(new ScriptedInterceptor(ctx =>
            PointOf(ctx) == "pre_tool_call"
                ? Verdict.Escalate("needs_review")
                : Verdict.Allow));
        var function = KernelFunctionFactory.CreateFromMethod(() => "ran", "Probe");

        await Assert.ThrowsAsync<AgentHooksInterceptionBlockedException>(
            () => kernel.InvokeAsync(function));
    }

    [Fact]
    public async Task RecordsAreEmittedForStartupAndToolBracketsAsync()
    {
        var records = new List<InterceptionRecord>();
        var kernel = BuildKernel(
            new ScriptedInterceptor(_ => Verdict.Allow), records: records);
        var function = KernelFunctionFactory.CreateFromMethod(() => "ran", "Probe");

        await kernel.InvokeAsync(function);

        Assert.Equal(3, records.Count);
        Assert.Equal(InterceptionPoint.AgentStartup, records[0].InterceptionPoint);
        Assert.Equal(InterceptionPoint.PreToolCall, records[1].InterceptionPoint);
        Assert.Equal(InterceptionPoint.PostToolCall, records[2].InterceptionPoint);
        Assert.All(records, r => Assert.Equal("sequential/first_deny", r.Composition.Profile.ToWireName()));
    }

    private sealed class ApproveAllResolver : IApprovalResolver
    {
        public bool Consulted;

        public ValueTask<ApprovalResolution> ResolveAsync(ApprovalRequest request, CancellationToken ct = default)
        {
            this.Consulted = true;
            return ValueTask.FromResult(new ApprovalResolution(
                ApprovalOutcome.Approve, request.ContextIdentity, Verdict.Allow));
        }
    }

    [Fact]
    public async Task DeniedStartupPoisonsTheSessionAsync()
    {
        var kernel = BuildKernel(new ScriptedInterceptor(ctx =>
            PointOf(ctx) == "agent_startup"
                ? Verdict.Deny("startup_denied")
                : Verdict.Allow));
        var function = KernelFunctionFactory.CreateFromMethod(() => "ran", "Probe");

        await Assert.ThrowsAsync<AgentHooksInterceptionBlockedException>(
            () => kernel.InvokeAsync(function));

        // §6.1a: the session processes nothing after a blocked startup.
        var second = await Assert.ThrowsAsync<AgentHooksInterceptionBlockedException>(
            () => kernel.InvokeAsync(function));
        Assert.Null(second.Record);
    }

    [Fact]
    public async Task ToolErrorStillEmitsPostToolCallAsync()
    {
        var records = new List<InterceptionRecord>();
        var kernel = BuildKernel(
            new ScriptedInterceptor(_ => Verdict.Allow),
            records: records);
        var function = KernelFunctionFactory.CreateFromMethod(
            new Func<string>(() => throw new InvalidOperationException("boom")), "Probe");

        await Assert.ThrowsAsync<InvalidOperationException>(() => kernel.InvokeAsync(function));

        var post = Assert.Single(records, r => r.InterceptionPoint == InterceptionPoint.PostToolCall);
        Assert.True(post.Verdict.Decision == Decision.Allow);
    }
}
