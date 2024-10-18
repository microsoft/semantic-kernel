// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.IO;
using System.Text;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests;
public class AotCompatibilityTests(ITestOutputHelper outputHelper)
{
    /// <summary>
    /// The test verifies that SK Native-AOT compatible packages don't have issues by analyzing warnings emitted by the AOT compiler while publishing the `samples/Demos/AotCompatibility.TestApp` application.
    /// It also runs the published app to ensure all tests scenarios are working as expected.
    ///
    /// If this test fails, it is due to adding Native-AOT incompatible changes to SK Native-AOT compatible packages or their dependencies.
    ///
    /// To diagnose the problem(s), inspect the test output which will contain Native-AOT warrnings/errors.
    ///
    /// You can also 'dotnet publish -c Debug' the 'AotCompatibility.TestApp' as well to get the errors.
    /// </summary>
    [Fact(Skip = "To be replaced by PS1 script")]
    public void EnsureAotCompatibility()
    {
        string workingDirectory = Path.Combine("..", "..", "..", "..", "..", "samples", "Demos", "AotCompatibility.TestApp");

        string publishDirectory = Path.Combine("bin", "Debug", "net8.0", "publish");

        this.PublishAotCompatibilityTestApp(workingDirectory, publishDirectory);

        this.RunAotCompatibilityTestApp(workingDirectory, publishDirectory);
    }

    private void PublishAotCompatibilityTestApp(string workingDirectory, string publishDirectory)
    {
        outputHelper.WriteLine($"Publishing the AotCompatibility.TestApp app from {workingDirectory}");

        // Ensure we run a clean publish every time
        DirectoryInfo testObjDir = new(Path.Combine(workingDirectory, "obj"));
        if (testObjDir.Exists)
        {
            testObjDir.Delete(recursive: true);
        }

        Process? process = null;
        string? processOutput = null;

        try
        {
            // Using debug configuration to prevent source code formatting kicks in and fix warnings including AOT related ones.
            (process, processOutput) = this.RunProcess(workingDirectory, "dotnet", $"publish -c Debug -o .\\{publishDirectory}");

            Assert.True(process.ExitCode == 0, "Publishing the AotCompatibility.TestApp app failed. See output for more details.");

            Assert.True(!processOutput.Contains("analysis warning IL") && !processOutput.Contains("analysis error IL"), "Native-AOT analysis warnings/errors found. See output for more details.");
        }
        finally
        {
            process?.Dispose();
        }
    }

    private void RunAotCompatibilityTestApp(string workingDirectory, string publishDirectory)
    {
        string fullPublishDirectory = Path.Combine(workingDirectory, publishDirectory);
        string appPath = Path.Combine(fullPublishDirectory, "AotCompatibility.TestApp.exe");

        outputHelper.WriteLine(string.Empty);
        outputHelper.WriteLine($"Running the {appPath} app");

        Process? process = null;
        string? processOutput = null;

        try
        {
            (process, processOutput) = this.RunProcess(fullPublishDirectory, appPath, "-tests");

            Assert.True(process.ExitCode == 0, $"Running the {appPath} app failed. See output for more details.");
        }
        finally
        {
            process?.Dispose();
        }
    }

    private (Process Process, string output) RunProcess(string workingDirectory, string command, string arguments, int waitTimeout = 180_000)
    {
        var process = new Process
        {
            StartInfo = new ProcessStartInfo(command, arguments)
            {
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = workingDirectory
            }
        };

        StringBuilder processOutputBuilder = new();

        process.OutputDataReceived += (sender, e) =>
        {
            if (e.Data is not null)
            {
                processOutputBuilder.Append(e.Data);
                outputHelper.WriteLine(e.Data);
            }
        };
        process.Start();
        process.BeginOutputReadLine();

        Assert.True(process.WaitForExit(milliseconds: waitTimeout), $"The {command} timed out after 3 minutes.");

        return (process, processOutputBuilder.ToString());
    }
}
