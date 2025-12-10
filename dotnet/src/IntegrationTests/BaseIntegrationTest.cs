// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.SemanticKernel;

namespace SemanticKernel.IntegrationTests;

public class BaseIntegrationTest
{
    protected IKernelBuilder CreateKernelBuilder()
    {
        var builder = Kernel.CreateBuilder();

        builder.Services.ConfigureHttpClientDefaults(c =>
        {
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.ShouldRetryAfterHeader = true;
                o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.TooManyRequests);
                o.CircuitBreaker = new HttpCircuitBreakerStrategyOptions
                {
                    SamplingDuration = TimeSpan.FromSeconds(60.0), // The duration should be least double of an attempt timeout
                };
                o.AttemptTimeout = new HttpTimeoutStrategyOptions
                {
                    Timeout = TimeSpan.FromSeconds(30.0)
                };
            });
        });

        return builder;
    }
}
