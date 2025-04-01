// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="KernelProcessState"/>.
/// </summary>
public class ProcessSerializationTests
{
    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/>.
    /// </summary>
    [Fact]
    public void KernelProcessFromYamlWorks()
    {
        // Arrange
        var yaml = ReadResource("workflow1.yaml");

        // Act
        var process = KernelProcess.ReadFromStringAsync(yaml);

        // Assert
        Assert.NotNull(process);
    }

    private string ReadResource(string name)
    {
        // Get the current assembly
        Assembly assembly = Assembly.GetExecutingAssembly();

        // Specify the resource name
        string resourceName = $"SemanticKernel.Process.UnitTests.Resources.{name}";


        var resoures = assembly.GetManifestResourceNames();

        // Get the resource stream
        using (Stream resourceStream = assembly.GetManifestResourceStream(resourceName))
        {
            if (resourceStream != null)
            {
                using (StreamReader reader = new(resourceStream))
                {
                    string content = reader.ReadToEnd();
                    return content;
                }
            }
            else
            {
                throw new Exception($"Resource {resourceName} not found in assembly {assembly.FullName}");
            }
        }
    }
}
