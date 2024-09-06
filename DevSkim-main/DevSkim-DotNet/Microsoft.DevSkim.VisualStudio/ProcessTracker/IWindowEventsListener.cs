// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
    /// <summary>
    /// Can listen to specified window's events and fire callback when events  received.
    /// </summary>
    public interface IWindowEventsListener : IDisposable
    {
        event EventHandler<WindowEventArgs> SystemEvent;
    }
}
