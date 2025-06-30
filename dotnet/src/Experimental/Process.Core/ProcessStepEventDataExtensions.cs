// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

internal static class ProcessStepEventDataExtensions
{
    public static List<ProcessStepEventData> ExtractProcessStepEventsData(this KernelFunctionMetadata functionMetadata)
    {
        List<ProcessStepEventData> processEvents = [];

        if (functionMetadata.ReturnParameter.Schema != null)
        {
            var outputEventData = functionMetadata.ReturnParameter.ToKernelEventTypeData();

            processEvents.Add(new("default", outputEventData));
        }

        foreach (var outputEvent in functionMetadata.ProcessOutputEvents)
        {
            if (outputEvent.Value.Schema != null)
            {
                processEvents.Add(new(outputEvent.Key, outputEvent.Value.ToKernelEventTypeData()));
            }
        }

        return processEvents;
    }

    public static ProcessStepEventData CreateFromType(string eventName, Type objectType, bool isPublic = false)
    {
        var eventTypeData = KernelReturnParameterMetadataFactory.CreateFromType(objectType).ToKernelEventTypeData();

        return new ProcessStepEventData(eventName, eventTypeData) { IsPublic = isPublic };
    }
}
