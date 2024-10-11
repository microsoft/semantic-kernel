// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.IO;
using Xunit.Abstractions;
using Xunit;
using System.Text;

namespace SemanticKernel.UnitTests;
public class AotCompatibilityTests(ITestOutputHelper output)
{
    /// <summary>
    /// The test verifies that SK Native-AOT compatible packages don't have issues by analyzing warnings emitted by the AOT compiler while publishing the `samples/Demos/AotCompatibility.TestApp` application.
    /// (TBD)It also executes the application to run several test samples from each of the Native-AOT enabled packages and checks their results.
    ///
    /// If this test fails, it is due to adding Native-AOT incompatible changes to SK Native-AOT compatible packages or their dependencies.
    ///
    /// To diagnose the problem(s), inspect the test output which will contain Native-AOT warrnings/errors.
    ///
    /// You can also 'dotnet publish -c Debug' the 'AotCompatibility.TestApp' as well to get the errors.
    /// </summary>
    [Fact]
    public void EnsureAotCompatibility()
    {
        string testAppPath = Path.Combine("..", "..", "..", "..", "..", "samples", "Demos", "AotCompatibility.TestApp");
        string testAppProject = "AotCompatibility.TestApp.csproj";

        // Ensure we run a clean publish every time
        DirectoryInfo testObjDir = new(Path.Combine(testAppPath, "obj"));
        if (testObjDir.Exists)
        {
            testObjDir.Delete(recursive: true);
        }

        using var process = new Process
        {
            // Using debug configuration to prevent source code formatting kicks in and fix waringns including AOT related ones.
            StartInfo = new ProcessStartInfo("dotnet", $"publish {testAppProject} -c Debug")
            {
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = testAppPath
            }
        };

        StringBuilder processOutputBuilder = new();

        process.OutputDataReceived += (sender, e) =>
        {
            if (e.Data is not null)
            {
                processOutputBuilder.Append(e.Data);
                output.WriteLine(e.Data);
            }
        };
        process.Start();
        process.BeginOutputReadLine();

        Assert.True(process.WaitForExit(milliseconds: 180_000), "Dotnet publish command timed out after 3 minutes.");

        Assert.True(process.ExitCode == 0, "Publishing the AotCompatibility.TestApp app failed. See output for more details.");

        string processOutput = processOutputBuilder.ToString();
        Assert.True(!processOutput.Contains("analysis warning IL") && !processOutput.Contains("analysis error IL"), "Native-AOT analysis warnings/errors found. See output for more details.");
    }
}
