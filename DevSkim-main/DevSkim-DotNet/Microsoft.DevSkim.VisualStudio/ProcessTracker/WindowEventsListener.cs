// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;
using System.Runtime.InteropServices;

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
    public class WindowEventsListener : IWindowEventsListener
    {
        private WindowEventHandler handler;
        private GCHandle handlerGCPin;
        private IntPtr hWinEventHook;

        public WindowEventsListener(
            WindowsSystemEvents min = WindowsSystemEvents.EventMin,
            WindowsSystemEvents max = WindowsSystemEvents.EventMax)
        {
            handler = new WindowEventHandler(InternalSystemEventHandler);
            handlerGCPin = GCHandle.Alloc(handler);

            hWinEventHook = NativeMethods.SetWinEventHook(
                min,
                max,
                IntPtr.Zero,
                handler,
                0,
                0,
                (uint)(WinEventHookFlags.OutOfContext | WinEventHookFlags.SkipOwnProcess));
        }

        public event EventHandler<WindowEventArgs>? SystemEvent;

        private void InternalSystemEventHandler(
            IntPtr hWinEventHook,
            WindowsSystemEvents anEvent,
            IntPtr hwnd,
            int idObject,
            int idChild,
            uint dwEventThread,
            uint dwmsEventTime)
        {
            SystemEvent?.Invoke(this, new WindowEventArgs(anEvent, hwnd));
        }

        ~WindowEventsListener()
        {
            Dispose(false);
        }

        #region IDisposable Members

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        #endregion

        protected virtual void Dispose(bool disposing)
        {
            if (hWinEventHook != IntPtr.Zero)
            {
                NativeMethods.UnhookWinEvent(hWinEventHook);
                hWinEventHook = IntPtr.Zero;
            }

            if (disposing)
            {
                if (handlerGCPin.IsAllocated)
                {
                    handlerGCPin.Free();
                }

                handler = null!;
            }
        }
    }

    public delegate void WindowEventHandler(
        IntPtr hWinEventHook,
        WindowsSystemEvents anEvent,
        IntPtr hwnd,
        int idObject,
        int idChild,
        uint dwEventThread,
        uint dwmsEventTime);
}
