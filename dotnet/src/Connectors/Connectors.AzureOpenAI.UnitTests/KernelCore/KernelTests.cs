// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Moq;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.KernelCore;

public sealed class KernelTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _multiMessageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;
    private readonly Mock<ILogger<KernelTests>> _mockLogger;

    public KernelTests()
    {
        this._multiMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._multiMessageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
        this._mockLogger = new Mock<ILogger<KernelTests>>();
        this._mockLoggerFactory.Setup(lf => lf.CreateLogger(It.IsAny<string>())).Returns(this._mockLogger.Object);
        this._mockLogger.Setup(l => l.IsEnabled(It.IsAny<LogLevel>())).Returns(true);
    }

    [Fact]
    public async Task FunctionUsageMetricsLoggingHasAllNeededData()
    {
        // Arrange
        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(ChatCompletionResponse) }
        );
        using MeterListener listener = EnableTelemetryMeters();

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureOpenAIChatCompletion(deploymentName: "model", endpoint: "https://localhost", apiKey: "apiKey", httpClient: this._httpClient);
        var kernel = builder.Build();

        var kernelFunction = KernelFunctionFactory.CreateFromPrompt("prompt", loggerFactory: this._mockLoggerFactory.Object);

        // Act
        var result = await kernel.InvokeAsync(kernelFunction);

        // Assert not getting usage problem logs
        this._mockLogger.VerifyLog(LogLevel.Information, "No model ID provided to capture usage details", Times.Never());
        this._mockLogger.VerifyLog(LogLevel.Information, "No metadata provided to capture usage details", Times.Never());
        this._mockLogger.VerifyLog(LogLevel.Information, "No usage details provided to capture usage details", Times.Never());
        this._mockLogger.VerifyLog(LogLevel.Warning, "Error while parsing usage details from model result", Times.Never());
        this._mockLogger.VerifyLog(LogLevel.Warning, "Unable to get token details from model result", Times.Never());
    }

    [Fact]
    public async Task FunctionUsageMetricsAreCapturedByTelemetryAsExpected()
    {
        // Set up a MeterListener to capture the measurements
        using MeterListener listener = EnableTelemetryMeters();

        var measurements = new Dictionary<string, List<int>>
        {
            ["semantic_kernel.function.invocation.token_usage.prompt"] = [],
            ["semantic_kernel.function.invocation.token_usage.completion"] = [],
        };

        listener.SetMeasurementEventCallback<int>((instrument, measurement, tags, state) =>
        {
            if (instrument.Name == "semantic_kernel.function.invocation.token_usage.prompt" ||
                instrument.Name == "semantic_kernel.function.invocation.token_usage.completion")
            {
                measurements[instrument.Name].Add(measurement);
            }
        });

        var completed = false;

        listener.MeasurementsCompleted = (instrument, state) =>
        {
            completed = true;
            // Stop the listener to stop collecting data
            Assert.Contains(12, measurements["semantic_kernel.function.invocation.token_usage.prompt"]);
            Assert.Contains(5, measurements["semantic_kernel.function.invocation.token_usage.completion"]);
        };

        listener.Start();  // Start the listener to begin collecting data

        this._multiMessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(ChatCompletionResponse) }
        );

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this._mockLoggerFactory.Object);
        builder.AddAzureOpenAIChatCompletion(deploymentName: "model", endpoint: "https://localhost", apiKey: "apiKey", httpClient: this._httpClient);
        var kernel = builder.Build();

        var kernelFunction = KernelFunctionFactory.CreateFromPrompt("prompt", loggerFactory: this._mockLoggerFactory.Object);

        // Act & Assert
        var result = await kernel.InvokeAsync(kernelFunction);

        listener.Dispose();

        while (!completed)
        {
            // Wait for the measurements to be completed
            await Task.Delay(100);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._multiMessageHandlerStub.Dispose();
    }

    private static MeterListener EnableTelemetryMeters()
    {
        var listener = new MeterListener();
        // Enable the listener to collect data for our specific histogram
        listener.InstrumentPublished = (instrument, listener) =>
        {
            if (instrument.Name == "semantic_kernel.function.invocation.token_usage.prompt" ||
                instrument.Name == "semantic_kernel.function.invocation.token_usage.completion")
            {
                listener.EnableMeasurementEvents(instrument);
            }
        };
        listener.Start();
        return listener;
    }

    private const string ChatCompletionResponse = """
        {
          "id": "chatcmpl-8IlRBQU929ym1EqAY2J4T7GGkW5Om",
          "object": "chat.completion",
          "created": 1699482945,
          "model": "gpt-3.5-turbo",
          "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test.",
                    "refusal": null
                },
                "logprobs": null,
                "finish_reason": "stop"
            }
          ],
          "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 5,
            "total_tokens": 17,
            "prompt_tokens_details": {
                "cached_tokens": 0
            },
            "completion_tokens_details": {
                "reasoning_tokens": 0
            }
          },
          "system_fingerprint": null
        }
        """;
}
