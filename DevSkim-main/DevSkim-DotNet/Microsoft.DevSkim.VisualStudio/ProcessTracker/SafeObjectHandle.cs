// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;
using Microsoft.Win32.SafeHandles;

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
    /// <summary>
    /// Represents a Win32 handle that can be closed with CloseHandle/>.
    /// </summary>
    public class SafeObjectHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="SafeObjectHandle"/> class.
        /// </summary>
        public SafeObjectHandle()
            : base(true)
        {
        }

        /// <summary>
        /// Initializes a new instance of the <see cref="SafeObjectHandle"/> class.
        /// </summary>
        /// <param name="preexistingHandle">An object that represents the pre-existing handle to use.</param>
        /// <param name="ownsHandle">
        ///     <see langword="true" /> to have the native handle released when this safe handle is disposed or finalized;
        ///     <see langword="false" /> otherwise.
        /// </param>
        public SafeObjectHandle(IntPtr preexistingHandle, bool ownsHandle = true)
            : base(ownsHandle)
        {
            SetHandle(preexistingHandle);
        }

        /// <inheritdoc />
        protected override bool ReleaseHandle() => NativeMethods.CloseHandle(handle);
    }
}
