// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;
using System.Diagnostics;

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
    /// <summary>
    /// Provides tracking and termination for a collection of processes. Processes are killed when the tracker is disposed.
    /// </summary>
    public interface IProcessTracker : IDisposable
    {
        /// <summary>
        /// Adds a process to be tracked.
        /// </summary>
        /// <param name="process"></param>
        public void AddProcess(Process process);
    }
}
