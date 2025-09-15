// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

/// <summary>
/// The metadata associated with an input required by the CrewAI Crew. This metadata provides the information required to effectively describe the inputs to an LLM.
/// </summary>
/// <param name="Name">The name of the input</param>
/// <param name="Description">The description of the input. This is used to help the LLM understand the correct usage of the input.</param>
/// <param name="Type">The <see cref="Type"/> of the input.</param>
public record CrewAIInputMetadata(string Name, string Description, Type Type)
{
}
