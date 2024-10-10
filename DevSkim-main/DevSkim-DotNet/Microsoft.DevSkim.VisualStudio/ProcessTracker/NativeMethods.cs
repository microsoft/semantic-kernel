// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.InteropServices;

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
#pragma warning disable 0649
    /// <summary>
    /// Pinvoke and other win32 declarations.
    /// </summary>
    public static class NativeMethods
    {
        public const int WM_SYSCOMMAND = 0x0112;
        public const int SC_CLOSE = 0xF060;
        public const int STATE_SYSTEM_INVISIBLE = 0x00008000;
        public const int GWL_EXSTYLE = -0x14;
        public const int WS_EX_TOOLWINDOW = 0x0080;
        public const int BUFFER_E_RELOAD_OCCURRED = unchecked((int)0x80041009);
        public const int PROCESS_CREATE_PROCESS = (0x0080);
        public const int PROCESS_QUERY_LIMITED_INFORMATION = 0x001000;
        public const uint LOGON_NETCREDENTIALS_ONLY = 0x2;
        public const uint CREATE_NEW_PROCESS_GROUP = 0x200;

        public const int TOKEN_ASSIGN_PRIMARY = 0x0001;
        public const int TOKEN_DUPLICATE = 0x0002;
        public const int TOKEN_QUERY = 0x0008;
        public const int TOKEN_ADJUST_DEFAULT = 0x0080;
        public const int TOKEN_ADJUST_SESSIONID = 0x0100;

        public const int SecurityAnonymous = 0x0;
        public const int TokenPrimary = 0x1;

        // ListView messages
        public const int LVM_EDITLABEL = (0x1000 + 118);

        [DllImport("kernel32.dll", SetLastError = true)]
        [DefaultDllImportSearchPaths(DllImportSearchPath.UserDirectories)]
        public static extern bool CloseHandle(IntPtr handle);

        [DllImport("User32.dll", SetLastError = true)]
        [DefaultDllImportSearchPaths(DllImportSearchPath.UserDirectories)]
        public static extern IntPtr SetWinEventHook(
            WindowsSystemEvents eventMin,
            WindowsSystemEvents eventMax,
            IntPtr hmodWinEventProc,
            WindowEventHandler lpfnWinEventProc,
            uint idProcess,
            uint idThread,
            uint dwFlags);

        [DllImport("user32.dll")]
        [DefaultDllImportSearchPaths(DllImportSearchPath.UserDirectories)]
        public static extern bool UnhookWinEvent(IntPtr hWinEventHook);

        /// <summary>
        /// Creates or opens a job object.
        /// </summary>
        /// <param name="lpJobAttributes">A pointer to a <see cref="SECURITY_ATTRIBUTES"/> structure that specifies the security descriptor for the job object and determines whether child processes can inherit the returned handle.
        /// If lpJobAttributes is NULL, the job object gets a default security descriptor and the handle cannot be inherited.
        /// The ACLs in the default security descriptor for a job object come from the primary or impersonation token of the creator.
        /// </param>
        /// <param name="lpName">The name of the job. The name is limited to MAX_PATH characters. Name comparison is case-sensitive.
        /// If lpName is NULL, the job is created without a name.
        /// If lpName matches the name of an existing event, semaphore, mutex, waitable timer, or file-mapping object, the function fails and the GetLastError function returns ERROR_INVALID_HANDLE.
        /// This occurs because these objects share the same namespace.The object can be created in a private namespace.For more information, see Object Namespaces.
        /// Terminal Services:  The name can have a "Global\" or "Local\" prefix to explicitly create the object in the global or session namespace. The remainder of the name can contain any character except the backslash character (\). For more information, see Kernel Object Namespaces.
        /// </param>
        /// <returns>
        /// If the function succeeds, the return value is a handle to the job object. The handle has the JOB_OBJECT_ALL_ACCESS access right. If the object existed before the function call, the function returns a handle to the existing job object and GetLastError returns ERROR_ALREADY_EXISTS.
        /// If the function fails, the return value is NULL.To get extended error information, GetLastError/>.
        /// </returns>
        [DllImport("Kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
        [DefaultDllImportSearchPaths(DllImportSearchPath.UserDirectories)]
        public static extern SafeObjectHandle CreateJobObject(IntPtr lpJobAttributes, string lpName);

        /// <summary>
        /// Assigns a process to an existing job object.
        /// </summary>
        /// <param name="hJob">
        /// A handle to the job object to which the process will be associated.
        /// The CreateJobObject or OpenJobObject function returns this handle.
        /// The handle must have the JOB_OBJECT_ASSIGN_PROCESS access right. For more information, see Job Object Security and Access Rights.
        /// </param>
        /// <param name="hProcess">
        /// A handle to the process to associate with the job object. The handle must have the PROCESS_SET_QUOTA and PROCESS_TERMINATE access rights. For more information, see Process Security and Access Rights.
        /// If the process is already associated with a job, the job specified by hJob must be empty or it must be in the hierarchy of nested jobs to which the process already belongs, and it cannot have UI limits set(SetInformationJobObject with JobObjectBasicUIRestrictions).
        /// For more information, see Remarks.
        /// Windows 7, Windows Server 2008 R2, Windows XP with SP3, Windows Server 2008, Windows Vista, and Windows Server 2003:  The process must not already be assigned to a job; if it is, the function fails with ERROR_ACCESS_DENIED.This behavior changed starting in Windows 8 and Windows Server 2012.
        /// Terminal Services:  All processes within a job must run within the same session as the job.
        /// </param>
        /// <returns>
        /// If the function succeeds, the return value is nonzero.
        /// If the function fails, the return value is zero.To get extended error information, call GetLastError/>.
        /// </returns>
        [DllImport("Kernel32", SetLastError = true)]
        [DefaultDllImportSearchPaths(DllImportSearchPath.UserDirectories)]
        public static extern bool AssignProcessToJobObject(SafeObjectHandle hJob, SafeObjectHandle hProcess);

        /// <summary>
        /// Sets limits for a job object.
        /// </summary>
        /// <param name="hJob">
        /// A handle to the job whose limits are being set. The CreateJobObject or OpenJobObject function returns this handle. The handle must have the JOB_OBJECT_SET_ATTRIBUTES access right. For more information, see Job Object Security and Access Rights.
        /// </param>
        /// <param name="jobObjectInfoClass">
        /// The information class for the limits to be set.
        /// </param>
        /// <param name="lpJobObjectInfo">
        /// The limits or job state to be set for the job. The format of this data depends on the value of JobObjectInfoClass.
        /// </param>
        /// <param name="cbJobObjectInfoLength">
        /// The size of the job information being set, in bytes.
        /// </param>
        /// <returns>
        /// If the function succeeds, the return value is nonzero.
        /// If the function fails, the return value is zero.To get extended error information, call GetLastError/>.
        /// </returns>
        [DllImport("Kernel32", SetLastError = true)]
        [DefaultDllImportSearchPaths(DllImportSearchPath.UserDirectories)]
        public static extern bool SetInformationJobObject(SafeObjectHandle hJob, JOBOBJECTINFOCLASS jobObjectInfoClass, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength);
    }

    internal delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [Flags]
    public enum ThreadAccess : int
    {
        TERMINATE = (0x0001),
        SUSPEND_RESUME = (0x0002),
        GET_CONTEXT = (0x0008),
        SET_CONTEXT = (0x0010),
        SET_INFORMATION = (0x0020),
        QUERY_INFORMATION = (0x0040),
        SET_THREAD_TOKEN = (0x0080),
        IMPERSONATE = (0x0100),
        DIRECT_IMPERSONATION = (0x0200)
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TITLEBARINFO
    {
        public int cbSize;
        public RECT rcTitleBar;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
        public int[] rgstate;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int left;
        public int top;
        public int right;
        public int bottom;
    }

    [Flags]
    internal enum WinEventHookFlags
    {
        // The callback function is NOT mapped into the address space of the process that generates the event.
#pragma warning disable CA1008 // Enums should have zero value
        OutOfContext = 0x0000,
#pragma warning restore CA1008 // Enums should have zero value
        // Prevents this instance of the hook from receiving the events that are generated by the thread that
        // is registering this hook.
        SkipOwnThread = 0x0001,
        // Prevents this instance of the hook from receiving the events that are generated by threads
        // in this process. This flag does not prevent threads from generating events.
        SkipOwnProcess = 0x0002,
        // The callback function IS mapped into the address space of the process that generates the event.
        InContext = 0x0004
    }

    [Flags]
    public enum STARTFLAGS
    {
        STARTF_USESHOWWINDOW = 0x00000001,
        STARTF_USESIZE = 0x00000002,
        STARTF_USEPOSITION = 0x00000004,
        STARTF_USECOUNTCHARS = 0x00000008,
        STARTF_USEFILLATTRIBUTE = 0x00000010,
        STARTF_RUNFULLSCREEN = 0x00000020,
        STARTF_FORCEONFEEDBACK = 0x00000040,
        STARTF_FORCEOFFFEEDBACK = 0x00000080,
        STARTF_USESTDHANDLES = 0x00000100,
        STARTF_USEHOTKEY = 0x00000200
    };

    [StructLayout(LayoutKind.Sequential)]
    internal struct SECURITY_ATTRIBUTES
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public int bInheritHandle;
    }

    /// <summary>
    /// Contains basic and extended limit information for a job object.
    /// </summary>
    /// <remarks>
    /// <para>The system tracks the value of PeakProcessMemoryUsed and PeakJobMemoryUsed constantly. This allows you know the peak memory usage of each job. You can use this information to establish a memory limit using the JOB_OBJECT_LIMIT_PROCESS_MEMORY or JOB_OBJECT_LIMIT_JOB_MEMORY value.</para>
    /// <para>Note that the job memory and process memory limits are very similar in operation, but they are independent. You could set a job-wide limit of 100 MB with a per-process limit of 10 MB. In this scenario, no single process could commit more than 10 MB, and the set of processes associated with a job could never exceed 100 MB.</para>
    /// <para>To register for notifications that a job has exceeded its peak memory limit while allowing processes to continue to commit memory, use the SetInformationJobObject function with the JobObjectNotificationLimitInformation information class.</para>
    /// </remarks>
    internal struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        /// <summary>
        /// A <see cref="JOBOBJECT_BASIC_LIMIT_INFORMATION"/> structure that contains basic limit information.
        /// </summary>
        internal JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;

        /// <summary>
        /// Reserved.
        /// </summary>
        internal IO_COUNTERS IoInfo;

        /// <summary>
        /// If the <see cref="JOBOBJECT_BASIC_LIMIT_INFORMATION.LimitFlags"/> member of the <see cref="JOBOBJECT_BASIC_LIMIT_INFORMATION"/> structure specifies the
        /// <see cref="JOB_OBJECT_LIMIT_FLAGS.JOB_OBJECT_LIMIT_PROCESS_MEMORY"/> value, this member specifies the limit for the virtual memory that can be committed by a process.
        /// Otherwise, this member is ignored.
        /// </summary>
        internal UIntPtr ProcessMemoryLimit;

        /// <summary>
        /// If the <see cref="JOBOBJECT_BASIC_LIMIT_INFORMATION.LimitFlags"/> member of the <see cref="JOBOBJECT_BASIC_LIMIT_INFORMATION"/> structure specifies the
        /// <see cref="JOB_OBJECT_LIMIT_FLAGS.JOB_OBJECT_LIMIT_JOB_MEMORY"/> value,
        /// this member specifies the limit for the virtual memory that can be committed for the job. Otherwise, this member is ignored.
        /// </summary>
        internal UIntPtr JobMemoryLimit;

        /// <summary>
        /// The peak memory used by any process ever associated with the job.
        /// </summary>
        internal UIntPtr PeakProcessMemoryUsed;

        /// <summary>
        /// The peak memory usage of all processes currently associated with the job.
        /// </summary>
        internal UIntPtr PeakJobMemoryUsed;
    }

    /// <summary>
    /// Contains basic limit information for a job object.
    /// </summary>
    internal struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_PROCESS_TIME, this member is the per-process user-mode execution time limit, in 100-nanosecond ticks. Otherwise, this member is ignored.
        /// </summary>
        internal long PerProcessUserTimeLimit;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_JOB_TIME, this member is the per-job user-mode execution time limit, in 100-nanosecond ticks. Otherwise, this member is ignored.
        /// </summary>
        internal long PerJobUserTimeLimit;

        /// <summary>
        /// The limit flags that are in effect. This member is a bitfield that determines whether other structure members are used.
        /// </summary>
        internal JOB_OBJECT_LIMIT_FLAGS LimitFlags;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_WORKINGSET, this member is the minimum working set size in bytes for each process associated with the job. Otherwise, this member is ignored.
        /// </summary>
        internal UIntPtr MinWorkingSetSize;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_WORKINGSET, this member is the maximum working set size in bytes for each process associated with the job. Otherwise, this member is ignored.
        /// </summary>
        internal UIntPtr MaxWorkingSetSize;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_ACTIVE_PROCESS, this member is the active process limit for the job. Otherwise, this member is ignored.
        /// </summary>
        internal uint ActiveProcessLimit;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_AFFINITY, this member is the processor affinity for all processes associated with the job. Otherwise, this member is ignored.
        /// </summary>
        internal UIntPtr Affinity;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_PRIORITY_CLASS, this member is the priority class for all processes associated with the job. Otherwise, this member is ignored.
        /// </summary>
        internal uint PriorityClass;

        /// <summary>
        /// If LimitFlags specifies JOB_OBJECT_LIMIT_SCHEDULING_CLASS, this member is the scheduling class for all processes associated with the job. Otherwise, this member is ignored.
        /// </summary>
        internal uint SchedulingClass;
    }

    /// <summary>
    /// Contains I/O accounting information for a process or a job object.
    /// For a job object, the counters include all operations performed by all processes that have ever been associated with the job,
    /// in addition to all processes currently associated with the job.
    /// </summary>
    internal struct IO_COUNTERS
    {
        /// <summary>
        /// The number of read operations performed.
        /// </summary>
        internal ulong ReadOperationCount;

        /// <summary>
        /// The number of write operations performed.
        /// </summary>
        internal ulong WriteOperationCount;

        /// <summary>
        /// The number of I/O operations performed, other than read and write operations.
        /// </summary>
        internal ulong OtherOperationCount;

        /// <summary>
        /// The number of bytes read.
        /// </summary>
        internal ulong ReadTransferCount;

        /// <summary>
        /// The number of bytes written.
        /// </summary>
        internal ulong WriteTransferCount;

        /// <summary>
        /// The number of bytes transferred during operations other than read and write operations.
        /// </summary>
        internal ulong OtherTransferCount;
    }

    /// <summary>
    /// The limit flags that are in effect.
    /// </summary>
    [Flags]
    internal enum JOB_OBJECT_LIMIT_FLAGS
    {
        /// <summary>
        /// Causes all processes associated with the job to use the same minimum and maximum working set sizes.
        /// </summary>
        JOB_OBJECT_LIMIT_WORKINGSET = 0x1,

        /// <summary>
        /// Causes all processes associated with the job to use the same priority class.
        /// </summary>
        JOB_OBJECT_LIMIT_PROCESS_TIME = 0x2,

        /// <summary>
        /// Establishes a user-mode execution time limit for the job.
        /// </summary>
        JOB_OBJECT_LIMIT_JOB_TIME = 0x4,

        /// <summary>
        /// Establishes a maximum number of simultaneously active processes associated with the job.
        /// </summary>
        JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x8,

        /// <summary>
        /// Causes all processes associated with the job to use the same processor affinity.
        /// </summary>
        JOB_OBJECT_LIMIT_AFFINITY = 0x10,

        /// <summary>
        /// Causes all processes associated with the job to use the same priority class.
        /// </summary>
        JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x20,

        /// <summary>
        /// Preserves any job time limits you previously set. As long as this flag is set, you can establish a per-job time limit once, then alter other limits in subsequent calls.
        /// </summary>
        JOB_OBJECT_LIMIT_PRESERVE_JOB_TIME = 0x40,

        /// <summary>
        /// Causes all processes in the job to use the same scheduling class.
        /// </summary>
        JOB_OBJECT_LIMIT_SCHEDULING_CLASS = 0x80,

        /// <summary>
        /// Causes all processes associated with the job to limit their committed memory.
        /// </summary>
        JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x100,

        /// <summary>
        /// Causes all processes associated with the job to limit the job-wide sum of their committed memory.
        /// </summary>
        JOB_OBJECT_LIMIT_JOB_MEMORY = 0x200,

        /// <summary>
        /// Forces a call to the SetErrorMode function with the SEM_NOGPFAULTERRORBOX flag for each process associated with the job.
        /// </summary>
        JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x400,

        /// <summary>
        /// If any process associated with the job creates a child process using the CREATE_BREAKAWAY_FROM_JOB flag while this limit is in effect, the child process is not associated with the job.
        /// </summary>
        JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x800,

        /// <summary>
        /// Allows any process associated with the job to create child processes that are not associated with the job.
        /// </summary>
        JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x1000,

        /// <summary>
        /// Causes all processes associated with the job to terminate when the last handle to the job is closed.
        /// </summary>
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000,

        /// <summary>
        /// Allows processes to use a subset of the processor affinity for all processes associated with the job.
        /// </summary>
        JOB_OBJECT_LIMIT_SUBSET_AFFINITY = 0x4000,
    }

    /// <summary>
    /// The information class for the limits to be set.
    /// </summary>
    /// <remarks>
    /// Taken from https://msdn.microsoft.com/en-us/library/windows/desktop/ms686216(v=vs.85).aspx.
    /// </remarks>
    [SuppressMessage("Design", "CA1008:Enums should have zero value", Justification = "PInvoke API")]
    public enum JOBOBJECTINFOCLASS
    {
        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a <see cref="JOBOBJECT_BASIC_LIMIT_INFORMATION" /> structure.
        /// </summary>
        JobObjectBasicLimitInformation = 2,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_BASIC_UI_RESTRICTIONS structure.
        /// </summary>
        JobObjectBasicUIRestrictions = 4,

        /// <summary>
        /// This flag is not supported. Applications must set security limitations individually for each process.
        /// </summary>
        JobObjectSecurityLimitInformation = 5,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_END_OF_JOB_TIME_INFORMATION structure.
        /// </summary>
        JobObjectEndOfJobTimeInformation = 6,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_ASSOCIATE_COMPLETION_PORT structure.
        /// </summary>
        JobObjectAssociateCompletionPortInformation = 7,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a <see cref="JOBOBJECT_EXTENDED_LIMIT_INFORMATION" /> structure.
        /// </summary>
        JobObjectExtendedLimitInformation = 9,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a USHORT value that specifies the list of processor groups to assign the job to.
        /// The cbJobObjectInfoLength parameter is set to the size of the group data. Divide this value by sizeof(USHORT) to determine the number of groups.
        /// </summary>
        JobObjectGroupInformation = 11,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_NOTIFICATION_LIMIT_INFORMATION structure.
        /// </summary>
        JobObjectNotificationLimitInformation = 12,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a buffer that contains an array of GROUP_AFFINITY structures that specify the affinity of the job for the processor groups to which the job is currently assigned.
        /// The cbJobObjectInfoLength parameter is set to the size of the group affinity data. Divide this value by sizeof(GROUP_AFFINITY) to determine the number of groups.
        /// </summary>
        JobObjectGroupInformationEx = 14,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_CPU_RATE_CONTROL_INFORMATION structure.
        /// </summary>
        JobObjectCpuRateControlInformation = 15,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_NET_RATE_CONTROL_INFORMATION structure.
        /// </summary>
        JobObjectNetRateControlInformation = 32,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_NOTIFICATION_LIMIT_INFORMATION_2 structure.
        /// </summary>
        JobObjectNotificationLimitInformation2 = 34,

        /// <summary>
        /// The lpJobObjectInfo parameter is a pointer to a JOBOBJECT_LIMIT_VIOLATION_INFORMATION_2 structure.
        /// </summary>
        JobObjectLimitViolationInformation2 = 35,
    }
#pragma warning restore 649
}
