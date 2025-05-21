// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining message sources in a Foundry process.
/// </summary>
[Experimental("SKEXP0081")]
public class FoundryMessageSourceBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MessageSourceBuilder"/> class.
    /// </summary>
    /// <param name="messageType">The meassage type</param>
    /// <param name="source">The source step builder</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    public FoundryMessageSourceBuilder(string messageType, ProcessStepBuilder source, string? condition)
    {
        this.MessageType = messageType;
        this.Source = source;
        this.Condition = condition;
    }

    /// <summary>
    /// The message type
    /// </summary>
    public string MessageType { get; }

    /// <summary>
    /// The source step builder.
    /// </summary>
    public ProcessStepBuilder Source { get; }

    /// <summary>
    /// The condition that must be met for the message to be processed.
    /// </summary>
    public string? Condition { get; }

    /// <summary>
    /// Builds the message source.
    /// </summary>
    /// <returns></returns>
    internal MessageSourceBuilder Build()
    {
        KernelProcessEdgeCondition? edgeCondition = null;
        if (!string.IsNullOrWhiteSpace(this.Condition))
        {
            edgeCondition = new KernelProcessEdgeCondition(
            (e, s) =>
            {
                var wrapper = new DeclarativeConditionContentWrapper
                {
                    State = s,
                    Event = e.Data
                };

                var result = JMESPathConditionEvaluator.EvaluateCondition(wrapper, this.Condition);
                return Task.FromResult(result);
            });
        }
        return new MessageSourceBuilder(this.MessageType, this.Source, edgeCondition);
    }
}
