VERSION 1.0 CLASS
BEGIN
MultiUse = -1  'True
END
Attribute VB_Name = "Xdebug"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

'namespace=xvba_modules\Xdebug

Public env As String

'Example of Package Create by XVBA-CLI

Private OS_TMP__FOLDER_PATH As String

Private IMMEDIATE_FOLDER As String

Private IMMEDIATE_FILE As String

Private DEBUG_FILE_PATH As String

Const EMPTY_TYPE = 0
Const NULL_TYPE = 1
Const ERROR_TYPE = 10
Const INTEGER_TYPE = 2
Const LONG_TYPE = 3
Const SINGLE_TYPE = 4
Const DOUBLE_TYPE = 5
Const CURRENCY_TYPE = 6
Const DATE_TYPE = 7
Const DECIMAL_TYPE = 14
Const LONG_LONG_TYPE = 20
Const BOOLEAN_TYPE = 11
Const STRING_TYPE = 8
Const ARRAY_TYPE = 8204
Const OBJECT_TYPE = 9
Const VARIANT_TYPE = 12
Const DATA_OBJECT_TYPE = 13
Private Const MESSAGE_SPACE = "                              "

Public errorSource As String
Public errorTitle As String

'/*
'Flag for Actrive os Deactive VBA Debug.Print
'*/
Public vbaDebugPrintActive As Boolean

Private Sub class_initialize()

     Dim fso  As Object
     Set fso = CreateObject("Scripting.FileSystemObject")
     OS_TMP__FOLDER_PATH = fso.GetSpecialFolder(2)
     IMMEDIATE_FOLDER = "xvba_immediate"
     IMMEDIATE_FILE = "immediate.txt"
     vbaDebugPrintActive = True
     errorSource = ""
     errorTitle = "XVBA: New Error Was Found"
     env = "DEV"

     DEBUG_FILE_PATH = OS_TMP__FOLDER_PATH & "\" & IMMEDIATE_FOLDER & "\" &  IMMEDIATE_FILE

End Sub




Public Function printx(inputValue As Variant,Optional messageType  As Integer = 1)

     if(env="DEV") Then
          Dim messageText  As String

          messageText = createOutputMessage(inputValue)

          Call writeDebugFileContent(messageText,messageType)
     End If
End Function

'/*
'Print A Error
'
'*/
Public  Function printError()
     if(env="DEV") Then

          Dim message As String

          message = ErrorHanddler()

          Call writeDebugFileContent(message,0)

     End If
End Function


'/*
'
'Write Debug ino on File
'
'
'*/  
Private Function writeDebugFileContent(messageText,messageType)

     Dim filePath As String
     Dim FileNum As Integer
     Dim PREFIX As String

     filePath = DEBUG_FILE_PATH

     FileNum = FreeFile

     PREFIX = Now & " - "

     Open filePath For Append As #FileNum

     Dim debugMessage As String
     Select Case messageType

      Case 0 'Error Message

          debugMessage= PREFIX & "Error:" & messageText
      Case 1 'Success
          debugMessage= PREFIX &  messageText
      Case Else 'No Type Set

          debugMessage= PREFIX & "Info:" & messageText
     End Select

     Print #FileNum,debugMessage 

     Close #FileNum

     If (vbaDebugPrintActive) Then

          Debug.Print debugMessage

     End If
End Function


Private  Function createOutputMessage(inputValue) As String

     Dim typeOfVar As Integer
     Dim response As String

     typeOfVar = VarType(inputValue) 


     'Set Error Source Macro/Function name 
     Err.Source="createOutputMessage"
     Select Case typeOfVar 
      Case STRING_TYPE 
          response = "String: " &  inputValue
      Case INTEGER_TYPE 
          response = "Integer: " & CStr(inputValue)
      Case LONG_TYPE
          response = "Long: " & CStr(inputValue)
      Case SINGLE_TYPE 
          response = "Single: " & CStr(inputValue)
      Case DOUBLE_TYPE 
          response = "Double: " & CStr(inputValue)
      Case CURRENCY_TYPE 
          response = "Currenty: " & CStr(inputValue)
      Case DATE_TYPE 
          response = "Date: " & CStr(inputValue)
      Case DECIMAL_TYPE 
          response = "Decimal: " & CStr(inputValue)
      Case LONG_LONG_TYPE 
          response = "LongLong: " & CStr(inputValue)
      Case BOOLEAN_TYPE 
          response = "Boolean: " & CStr(inputValue)
      Case ARRAY_TYPE 
          response = makeArrayTypeMessage(inputValue)
      Case EMPTY_TYPE 
          response = "Empty: "
      Case OBJECT_TYPE
          response = "Object: "  & TypeName(inputValue)
      Case NULL_TYPE 
          response = "Null: "
      Case ERROR_TYPE 
          response = "Error: "
      Case VARIANT_TYPE
          response = "Variant: "
      Case DATA_OBJECT_TYPE 
          response = "Data Object: " & TypeName(inputValue)
      Case Else 
          response = "Type Not Supported yet please inform xvba developer "
          Debug.Print typeOfVar
          Debug.Print inputValue

     End Select


     createOutputMessage = response

End Function


Private  Function makeArrayTypeMessage(inputValue)As String
     Dim nextItem As Variant
     Dim response As String
     Dim message As String

     For Each nextItem In inputValue
          message =  createOutputMessage(nextItem)
          response = response & "                              [ " & message & " ]" & vbCrLf 
     Next nextItem 
     makeArrayTypeMessage =    "Array: " & vbCrLf  & response
End Function



Private  Function ErrorHanddler() As String
     Dim errorDescription As String
     Dim numberDescription As String
     Dim lineError As String
     Dim sourceError As String
     Dim errorTitleMsg As String
     Dim errorSourceMsg As String

     errorTitleMsg = vbCrLf & MESSAGE_SPACE & errorTitle
     errorSourceMsg = vbCrLf  & MESSAGE_SPACE & "Error Source: " & errorSource


     Select Case Err.Number
      Case 11 
          numberDescription = vbCrLf  & MESSAGE_SPACE & "Error Number: " & Err.Number
          lineError = vbCrLf  & MESSAGE_SPACE & "Error Line: " & Erl
          errorDescription =  vbCrLf & MESSAGE_SPACE & "Error Description: " & Err.Description
      Case Else 
          numberDescription = vbCrLf  & MESSAGE_SPACE & "Error Number: " & Err.Number
          errorDescription =  vbCrLf & MESSAGE_SPACE & "Error Description: " & Err.Description
     End Select


     ErrorHanddler = errorTitleMsg & lineError & errorSourceMsg & numberDescription & errorDescription

End Function