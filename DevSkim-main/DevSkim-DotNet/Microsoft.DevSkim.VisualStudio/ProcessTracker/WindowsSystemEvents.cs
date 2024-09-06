// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

namespace Microsoft.DevSkim.VisualStudio.ProcessTracker
{
    public enum WindowsSystemEvents
    {
        EventMin = 0x00000001,                              // EVENT_MIN
        SystemSound = 0x0001,                               // EVENT_SYSTEM_SOUND
        SystemAlert = 0x0002,                               // EVENT_SYSTEM_ALERT
        SystemForeground = 0x0003,                          // EVENT_SYSTEM_FOREGROUND
        SystemMenuStart = 0x0004,                           // EVENT_SYSTEM_MENUSTART
        SystemMenuEnd = 0x0005,                             // EVENT_SYSTEM_MENUEND
        SystemMenuPopupStart = 0x0006,                      // EVENT_SYSTEM_MENUPOPUPSTART
        SystemMenuPopupEnd = 0x0007,                        // EVENT_SYSTEM_MENUPOPUPEND
        SystemCaptureStart = 0x0008,                        // EVENT_SYSTEM_CAPTURESTART
        SystemCaptureEnd = 0x0009,                          // EVENT_SYSTEM_CAPTUREEND
        SystemMoveSizeStart = 0x000A,                       // EVENT_SYSTEM_MOVESIZESTART
        SystemMoveSizeEnd = 0x000B,                         // EVENT_SYSTEM_MOVESIZEEND
        SystemContextHelpStart = 0x000C,                    // EVENT_SYSTEM_CONTEXTHELPSTART
        SystemContextHelpEnd = 0x000D,                      // EVENT_SYSTEM_CONTEXTHELPEND
        SystemDragStart = 0x000E,                           // EVENT_SYSTEM_DRAGDROPSTART
        SystemDragEnd = 0x000F,                             // EVENT_SYSTEM_DRAGDROPEND
        SystemDialogStart = 0x0010,                         // EVENT_SYSTEM_DIALOGSTART
        SystemDialogEnd = 0x0011,                           // EVENT_SYSTEM_DIALOGEND
        SystemScrollingStart = 0x0012,                      // EVENT_SYSTEM_SCROLLINGSTART
        SystemScrollingEnd = 0x0013,                        // EVENT_SYSTEM_SCROLLINGEND
        SystemSwitchStart = 0x0014,                         // EVENT_SYSTEM_SWITCHSTART
        SystemSwitchEnd = 0x0015,                           // EVENT_SYSTEM_SWITCHEND
        SystemMinimizeStart = 0x0016,                       // EVENT_SYSTEM_MINIMIZESTART
        SystemMinimizeEnd = 0x0017,                         // EVENT_SYSTEM_MINIMIZEEND
        ObjectCreate = 0x8000,                              // EVENT_OBJECT_CREATE
        ObjectDestroy = 0x8001,                             // EVENT_OBJECT_DESTROY
        ObjectShow = 0x8002,                                // EVENT_OBJECT_SHOW
        ObjectHide = 0x8003,                                // EVENT_OBJECT_HIDE
        ObjectReorder = 0x8004,                             // EVENT_OBJECT_REORDER
        ObjectFocus = 0x8005,                               // EVENT_OBJECT_FOCUS
        ObjectSelection = 0x8006,                           // EVENT_OBJECT_SELECTION
        ObjectSelectionAdd = 0x8007,                        // EVENT_OBJECT_SELECTIONADD
        ObjectSelectionRemove = 0x8008,                     // EVENT_OBJECT_SELECTIONREMOVE
        ObjectSelectionWithin = 0x8009,                     // EVENT_OBJECT_SELECTIONWITHIN
        ObjectStateChange = 0x800A,                         // EVENT_OBJECT_STATECHANGE
        ObjectLocationChange = 0x800B,                      // EVENT_OBJECT_LOCATIONCHANGE
        ObjectNameChange = 0x800C,                          // EVENT_OBJECT_NAMECHANGE
        ObjectDescriptionChange = 0x800D,                   // EVENT_OBJECT_DESCRIPTIONCHANGE
        ObjectValueChange = 0x800E,                         // EVENT_OBJECT_VALUECHANGE
        ObjectParentChange = 0x800F,                        // EVENT_OBJECT_PARENTCHANGE
        ObjectHelpChange = 0x8010,                          // EVENT_OBJECT_HELPCHANGE
        ObjectDefactionChange = 0x8011,                     // EVENT_OBJECT_DEFACTIONCHANGE
        ObjectAcceleratorChange = 0x8012,                   // EVENT_OBJECT_ACCELERATORCHANGE
        EventMax = 0x7FFFFFFF,                              // EVENT_MAX

        // Vista or later.
        ObjectContentScrolled = 0x8015,                     // EVENT_OBJECT_CONTENTSCROLLED
        ObjectTextSelectionChanged = 0x8014,                // EVENT_OBJECT_TEXTSELECTIONCHANGED
        ObjectInvoked = 0x8013,                             // EVENT_OBJECT_INVOKED
        SystemDesktopSwitch = 0x00000020,                   // EVENT_SYSTEM_DESKTOPSWITCH
    }
}
