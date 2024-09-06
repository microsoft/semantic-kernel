// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;
using System.ComponentModel;
using System.ComponentModel.Composition;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
    /// <summary>
    /// Allows processes to be automatically killed if this parent process unexpectedly quits
    /// (or when an instance of this class is disposed).
    /// </summary>
    [Export(typeof(IProcessTracker))]
    public sealed class JobObjectProcessTracker : IProcessTracker
    {
        private bool disposed;
        private readonly object disposeLock = new();

        /// <summary>
        /// The job handle.
        /// </summary>
        /// <remarks>
        /// Closing this handle would close all tracked processes. This will happen automatically when
        /// our process exits.
        /// </remarks>
        private readonly SafeObjectHandle jobHandle;

        /// <summary>
        /// Initializes a new instance of the <see cref="JobObjectProcessTracker"/> class.
        /// </summary>
        public JobObjectProcessTracker()
        {
            // The job name is optional (and can be null) but it helps with diagnostics.
            //  If it's not null, it has to be unique. Use SysInternals' Handle command-line
            //  utility: handle -a JobObjectProcessTracker
            string jobName = nameof(JobObjectProcessTracker) + Process.GetCurrentProcess().Id;

            jobHandle = NativeMethods.CreateJobObject(IntPtr.Zero, jobName);

            JOBOBJECT_EXTENDED_LIMIT_INFORMATION extendedInfo = new()
            {
                BasicLimitInformation = new JOBOBJECT_BASIC_LIMIT_INFORMATION
                {
                    LimitFlags = JOB_OBJECT_LIMIT_FLAGS.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
                        JOB_OBJECT_LIMIT_FLAGS.JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK,
                },
            };

            // This code can be a lot simpler if we use pointers, but since this class is so generally interesting
            // and may be copied and pasted to other projects that prefer to avoid unsafe code, we use Marshal and IntPtr's instead.
            int length = Marshal.SizeOf(extendedInfo);
            IntPtr pExtendedInfo = Marshal.AllocHGlobal(length);
            try
            {
                Marshal.StructureToPtr(extendedInfo, pExtendedInfo, fDeleteOld: false);
                try
                {
                    if (!NativeMethods.SetInformationJobObject(jobHandle, JOBOBJECTINFOCLASS.JobObjectExtendedLimitInformation, pExtendedInfo, (uint)length))
                    {
                        throw new Win32Exception();
                    }
                }
                finally
                {
                    Marshal.DestroyStructure<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>(pExtendedInfo);
                }
            }
            finally
            {
                Marshal.FreeHGlobal(pExtendedInfo);
            }
        }

        /// <summary>
        /// Ensures a given process is killed when the current process exits.
        /// </summary>
        /// <param name="process">The process whose lifetime should never exceed the lifetime of the current process.</param>
        public void AddProcess(Process process)
        {
            _ = process ?? throw new ArgumentNullException(nameof(process));

            lock (disposeLock)
            {
                // Do not assign the new process handle to the job object if it is disposed.
                // Use a lock to avoid race conditions with disposing and assigning processes to the job object.
                if (!disposed)
                {
                    bool success = NativeMethods.AssignProcessToJobObject(jobHandle, new SafeObjectHandle(process.Handle, ownsHandle: false));
                    if (!success && !process.HasExited)
                    {
                        throw new Win32Exception();
                    }
                }
            }
        }

        /// <summary>
        /// Kills all processes previously tracked with <see cref="AddProcess(Process)"/> by closing the Windows Job.
        /// </summary>
        public void Dispose()
        {
            lock (disposeLock)
            {
                if (!disposed)
                {
                    jobHandle?.Dispose();
                }

                disposed = true;
            }
        }
    }
}
