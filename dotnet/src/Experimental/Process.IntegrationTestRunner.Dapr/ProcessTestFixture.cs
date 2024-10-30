// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Net;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// A test fixture for running shared process tests across multiple runtimes.
/// </summary>
public class ProcessTestFixture : IDisposable, IAsyncLifetime
{
    private System.Diagnostics.Process? _process;
    private HttpClient? _httpClient;

    public async Task InitializeAsync()
    {
        this._httpClient = new HttpClient();
        await this.StartTestHostAsync();
    }

    private async Task StartTestHostAsync()
    {
        try
        {
            string workingDirectory = Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), @"..\..\..\..\Process.IntegrationTestHost.Dapr"));
            var procesStartInfo = new ProcessStartInfo
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
                StartInfo = procesStartInfo
            };

            this._process.Start();
            await this.WaitForHostStartupAsync();
        }
        catch (Exception)
        {
            throw;
        }
    }

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
    /// <returns>A <see cref="Task{KernelProcessContext}"/></returns>
    public async Task<KernelProcessContext> StartProcessAsync(KernelProcess process, Kernel kernel, KernelProcessEvent initialEvent)
    {
        var context = new DaprTestProcessContext(process, this._httpClient!);
        await context.StartWithEventAsync(initialEvent);
        return context;
    }

    public void Dispose()
    {
        if (!this._process.HasExited)
        {
            this._process?.Kill();
            this._process?.WaitForExit();
        }

        this._process?.Dispose();
        this._httpClient?.Dispose();
    }

    public Task DisposeAsync()
    {
        return Task.CompletedTask;
    }
}
