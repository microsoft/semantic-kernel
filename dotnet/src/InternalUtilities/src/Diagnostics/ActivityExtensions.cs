// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Diagnostics;

[ExcludeFromCodeCoverage]
internal static class ActivityExtensions
{
    /// <summary>
    /// Starts an activity with the specified name and tags.
    /// </summary>
    public static Activity? StartActivityWithTags(this ActivitySource source, string name, List<KeyValuePair<string, object?>> tags)
    {
        return source.StartActivity(
            name,
            ActivityKind.Internal,
            Activity.Current?.Context ?? new ActivityContext(),
            tags);
    }

    /// <summary>
    /// Adds tags to the activity.
    /// </summary>
    public static Activity AddTags(this Activity activity, List<KeyValuePair<string, object?>> tags)
    {
        tags.ForEach(tag =>
        {
            activity.SetTag(tag.Key, tag.Value);
        });

        return activity;
    }

    /// <summary>
    /// Adds an event to the activity. Should only be used for events that contain sensitive data.
    /// </summary>
    public static Activity AttachSensitiveDataAsEvent(this Activity activity, string name, List<KeyValuePair<string, object?>> tags)
    {
        activity.AddEvent(new ActivityEvent(
            name,
            tags: new ActivityTagsCollection(tags)
        ));

        return activity;
    }

    /// <summary>
    /// Sets the error status and type on the activity.
    /// </summary>
    public static Activity SetError(this Activity activity, Exception exception)
    {
        activity.SetTag("error.type", exception.GetType().FullName);
        activity.SetStatus(ActivityStatusCode.Error, exception.Message);
        return activity;
    }
}
