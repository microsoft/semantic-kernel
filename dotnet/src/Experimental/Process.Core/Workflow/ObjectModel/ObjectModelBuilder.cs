// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Workflows;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder for converting CPS Topic ObjectModel YAML definition in a process.
/// </summary>
public static class ObjectModelBuilder
{
    /// <summary>
    /// Builds a process from the provided YAML definition of a CPS Topic ObjectModel.
    /// </summary>
    /// <param name="processId">The identifier for the process.</param>
    /// <param name="workflowYaml">The YAML string defining the CPS Topic ObjectModel.</param>
    /// <param name="messageId">The identifier for the message.</param>
    /// <param name="environment">The environment for the process actions.</param>
    /// <returns>The <see cref="KernelProcess"/> that corresponds with the YAML object model.</returns>
    public static KernelProcess Build(string processId, string workflowYaml, string messageId, ProcessActionEnvironment? environment = null)
    {
        ProcessBuilder processBuilder = new(processId);
        ProcessActionWalker walker = new(processBuilder, messageId, environment ?? ProcessActionEnvironment.Default);
        walker.ProcessYaml(workflowYaml);
        return processBuilder.Build();
    }
}
