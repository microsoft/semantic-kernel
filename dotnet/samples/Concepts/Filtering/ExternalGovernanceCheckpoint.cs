// Copyright (c) Microsoft. All rights reserved.

using System.Security.Cryptography;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Filtering;

/// <summary>
/// Shows how to place an external governance checkpoint in front of automatic function invocation.
/// </summary>
public class ExternalGovernanceCheckpoint(ITestOutputHelper output) : BaseTest(output)
{
    [Theory]
    [InlineData("allow", "Executed wire transfer", "executed")]
    [InlineData("require_approval", "Paused for approval", "paused")]
    public async Task ExternalCheckpointCanAllowOrPauseFunctionInvocationAsync(string requestedVerdict, string expectedResult, string expectedStatus)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IExternalCheckpointClient>(new ExampleCheckpointClient(requestedVerdict));
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter, ExternalGovernanceFilter>();

        var kernel = builder.Build();
        var function = KernelFunctionFactory.CreateFromMethod(
            (decimal amount, string recipient) => "Executed wire transfer",
            "WireTransfer");

        KernelPlugin plugin = kernel.ImportPluginFromFunctions("Payments", [function]);
        KernelFunction importedFunction = plugin["WireTransfer"];

        var context = CreateAutoFunctionInvocationContext(
            kernel,
            importedFunction,
            new KernelArguments
            {
                ["amount"] = 1250m,
                ["recipient"] = "Fabrikam"
            });

        var filter = kernel.Services.GetRequiredService<IAutoFunctionInvocationFilter>();
        await filter.OnAutoFunctionInvocationAsync(context, async invocationContext =>
        {
            invocationContext.Result = await invocationContext.Function.InvokeAsync(kernel, invocationContext.Arguments);
        });

        Console.WriteLine(context.Result);
        Assert.Equal(expectedResult, context.Result.GetValue<string>());
        Assert.Equal(expectedStatus, context.Result.Metadata?["governance_status"]);

        // Output for allow:
        // Executed wire transfer
        //
        // Output for require_approval:
        // Paused for approval
    }

    [Fact]
    public async Task ExternalCheckpointCanDenyFunctionInvocationAsync()
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IExternalCheckpointClient>(new ExampleCheckpointClient("deny"));
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter, ExternalGovernanceFilter>();

        var kernel = builder.Build();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Deleted customer record", "DeleteCustomerRecord");

        KernelPlugin plugin = kernel.ImportPluginFromFunctions("CustomerAdmin", [function]);
        KernelFunction importedFunction = plugin["DeleteCustomerRecord"];

        var context = CreateAutoFunctionInvocationContext(kernel, importedFunction, new KernelArguments());
        var filter = kernel.Services.GetRequiredService<IAutoFunctionInvocationFilter>();

        var exception = await Assert.ThrowsAsync<UnauthorizedAccessException>(() =>
            filter.OnAutoFunctionInvocationAsync(context, _ => throw new InvalidOperationException("The function should not execute.")));

        Assert.Contains("denied", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    private static AutoFunctionInvocationContext CreateAutoFunctionInvocationContext(
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments)
    {
        var chatHistory = new ChatHistory("Transfer $1,250 to Fabrikam.");
        var functionCall = new FunctionCallContent(
            functionName: function.Name,
            pluginName: function.PluginName,
            id: "call_123",
            arguments: arguments);

        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, [functionCall]);
        chatHistory.Add(chatMessageContent);

        return new AutoFunctionInvocationContext(
            kernel,
            function,
            new FunctionResult(function),
            chatHistory,
            chatMessageContent)
        {
            Arguments = arguments,
            RequestSequenceIndex = 0,
            FunctionSequenceIndex = 0,
            ToolCallId = functionCall.Id
        };
    }

    private sealed class ExternalGovernanceFilter(IExternalCheckpointClient checkpointClient) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            ActionEnvelope envelope = ActionEnvelope.FromContext(context);
            string checkpointReference = ActionEnvelopeDigest.ComputeReference(envelope);

            CheckpointVerdict verdict = await checkpointClient.EvaluateAsync(envelope, checkpointReference, context.CancellationToken);

            switch (verdict.Decision)
            {
                case "allow":
                    await next(context);
                    context.Result = WithGovernanceMetadata(context.Result, checkpointReference, "executed");
                    return;

                case "require_approval":
                    context.Result = WithGovernanceMetadata(
                        context.Result,
                        checkpointReference,
                        "paused",
                        "Paused for approval");
                    context.Terminate = true;
                    return;

                case "deny":
                    string functionLabel = envelope.PluginName is { Length: > 0 }
                        ? $"{envelope.PluginName}.{envelope.FunctionName}"
                        : envelope.FunctionName;

                    throw new UnauthorizedAccessException(
                        $"Function call '{functionLabel}' was denied by checkpoint {checkpointReference}.");

                default:
                    throw new InvalidOperationException($"Unknown checkpoint verdict '{verdict.Decision}'.");
            }
        }

        private static FunctionResult WithGovernanceMetadata(
            FunctionResult result,
            string checkpointReference,
            string status,
            string? value = null)
        {
            Dictionary<string, object?> metadata = result.Metadata is not null ? new(result.Metadata) : [];
            metadata["governance_checkpoint"] = checkpointReference;
            metadata["governance_status"] = status;

            return new FunctionResult(result, value)
            {
                Metadata = metadata
            };
        }
    }

    private sealed record ActionEnvelope(
        string? PluginName,
        string FunctionName,
        IReadOnlyDictionary<string, object?> Arguments,
        int RequestSequenceIndex,
        int FunctionSequenceIndex,
        string? ToolCallId)
    {
        public static ActionEnvelope FromContext(AutoFunctionInvocationContext context)
        {
            SortedDictionary<string, object?> arguments = new(StringComparer.Ordinal);

            if (context.Arguments is not null)
            {
                foreach (var argument in context.Arguments.OrderBy(static item => item.Key, StringComparer.Ordinal))
                {
                    arguments[argument.Key] = argument.Value;
                }
            }

            return new(
                context.Function.PluginName,
                context.Function.Name,
                arguments,
                context.RequestSequenceIndex,
                context.FunctionSequenceIndex,
                context.ToolCallId);
        }
    }

    private static class ActionEnvelopeDigest
    {
        private static readonly JsonSerializerOptions s_serializerOptions = new(JsonSerializerDefaults.Web);

        public static string ComputeReference(ActionEnvelope envelope)
        {
            var reference = new ActionReference(envelope.PluginName, envelope.FunctionName, envelope.Arguments);
            byte[] envelopeBytes = JsonSerializer.SerializeToUtf8Bytes(reference, s_serializerOptions);
            byte[] digest = SHA256.HashData(envelopeBytes);

            return $"sha256:{Convert.ToHexString(digest).ToLowerInvariant()}";
        }

        private sealed record ActionReference(
            string? PluginName,
            string FunctionName,
            IReadOnlyDictionary<string, object?> Arguments);
    }

    private interface IExternalCheckpointClient
    {
        Task<CheckpointVerdict> EvaluateAsync(ActionEnvelope envelope, string checkpointReference, CancellationToken cancellationToken);
    }

    private sealed class ExampleCheckpointClient(string decision) : IExternalCheckpointClient
    {
        public Task<CheckpointVerdict> EvaluateAsync(
            ActionEnvelope envelope,
            string checkpointReference,
            CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();

            string functionLabel = envelope.PluginName is { Length: > 0 }
                ? $"{envelope.PluginName}.{envelope.FunctionName}"
                : envelope.FunctionName;

            Console.WriteLine($"Checkpoint {checkpointReference}: {decision} {functionLabel}");

            return Task.FromResult(new CheckpointVerdict(decision));
        }
    }

    private sealed record CheckpointVerdict(string Decision);
}
