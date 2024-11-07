// Copyright (c) Microsoft. All rights reserved.

//using System;
//using System.Collections.Generic;

//namespace Microsoft.SemanticKernel.Process.Runtime;

//internal sealed record MapOperationContext(in HashSet<string> EventTargets, in Dictionary<string, Type> CapturedEvents)  %%% REMOVE
//{
//    public Dictionary<string, object?> Results { get; } = [];

//    public bool Filter(ProcessEvent processEvent)
//    {
//        string eventName = processEvent.SourceId;
//        if (this.EventTargets.Contains(eventName))
//        {
//            this.CapturedEvents.TryGetValue(eventName, out Type? resultType);
//            if (resultType is null || resultType == typeof(object))
//            {
//                this.CapturedEvents[eventName] = processEvent.Data?.GetType() ?? typeof(object);
//            }

//            this.Results[eventName] = processEvent.Data;
//        }

//        return true;
//    }
//}
