// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Net;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Xunit;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// A test fixture for running shared process tests across multiple runtimes.
/// </summary>
public sealed class ProcessTestFixture : IDisposable, IAsyncLifetime
{
    private System.Diagnostics.Process? _process;
    private HttpClient? _httpClient;

    /// <summary>
    /// Called by xUnit before the test is run.
    /// </summary>
    /// <returns></returns>
    public async Task InitializeAsync()
    {
        this._httpClient = new HttpClient();
        await this.StartTestHostAsync();
    }

    /// <summary>
    /// Starts the test host by creating a new process with the Dapr cli. The startup process can take 30 seconds or more and so we wait for this to complete before returning.
    /// </summary>
    /// <returns></returns>
    private async Task StartTestHostAsync()
    {
        try
        {
            string workingDirectory = Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), @"..\..\..\..\Process.IntegrationTestHost.Dapr"));
            var processStartInfo = new ProcessStartInfo
            {
                FileName = "dapr",
                Arguments = "run --app-id daprprocesstests --app-port 5200 --dapr-http-port 3500 -- dotnet run --urls http://localhost:5200",
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = false,
                RedirectStandardError = false,
                UseShellExecute = true,
                CreateNoWindow = false
            };

            this._process = new System.Diagnostics.Process
            {
                StartInfo = processStartInfo
            };

            this._process.Start();
            await this.WaitForHostStartupAsync();
        }
        catch (Exception)
        {
            throw;
        }
    }

    private async Task ShutdownTestHostAsync()
    {
        var processStartInfo = new ProcessStartInfo
        {
            FileName = "dapr",
            Arguments = "stop --app-id daprprocesstests",
            RedirectStandardOutput = false,
            RedirectStandardError = false,
            UseShellExecute = true,
            CreateNoWindow = false
        };

        using var shutdownProcess = new System.Diagnostics.Process
        {
            StartInfo = processStartInfo
        };

        shutdownProcess.Start();
        await shutdownProcess.WaitForExitAsync();
    }

    /// <summary>
    /// Waits for the test host to be ready to accept requests. This is determined by making a request to the health endpoint.
    /// </summary>
    /// <returns></returns>
    /// <exception cref="InvalidProgramException"></exception>
    private async Task WaitForHostStartupAsync()
    {
        // Wait for the process to start
        var now = DateTime.Now;
        while (DateTime.Now - now < TimeSpan.FromSeconds(120))
        {
            if (this._process!.HasExited)
            {
                break;
            }

            try
            {
                var healthResponse = await this._httpClient!.GetAsync(new Uri("http://localhost:5200/daprHealth"));
                if (healthResponse.StatusCode == HttpStatusCode.OK)
                {
                    await Task.Delay(TimeSpan.FromSeconds(10));
                    return;
                }
            }
            catch (HttpRequestException)
            {
                // Do nothing, just wait
            }
        }

        throw new InvalidProgramException("Dapr Test Host did not start");
    }

    /// <summary>
    /// Starts a process.
    /// </summary>
    /// <param name="process">The process to start.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="initialEvent">An optional initial event.</param>
    /// <param name="externalMessageChannel">channel used for external messages</param>
    /// <returns>A <see cref="Task{KernelProcessContext}"/></returns>
    public async Task<KernelProcessContext> StartProcessAsync(KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent, IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        // Actual Kernel injection of Kernel and ExternalKernelProcessMessageChannel is in dotnet\src\Experimental\Process.IntegrationTestHost.Dapr\Program.cs
        var context = new DaprTestProcessContext(process, this._httpClient!);
        await context.StartWithEventAsync(initialEvent);
        return context;
    }

    /// <summary>
    /// Disposes of the test fixture.
    /// </summary>
    public void Dispose()
    {
        if (this._process is not null && this._process.HasExited)
        {
            this._process?.Kill();
            this._process?.WaitForExit();
        }

        this._process?.Dispose();
        this._httpClient?.Dispose();
    }

    /// <summary>
    /// Called by xUnit after the test is run.
    /// </summary>
    /// <returns></returns>
    public Task DisposeAsync()
    {
        return this.ShutdownTestHostAsync();
    }
}
