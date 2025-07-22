## Object Model Requirements

#### Definition

Name|Copilot Studio|Foundry|Note
:--|:--:|:--:|:--
ActionScope|✔|✔|Container for actions
ActivateExternalTrigger|✔|❌
AdaptiveCardPrompt|✔|❌
AnswerQuestionWithAI|✔|✔|Requires additional property: model (`ExternalModelConfiguration`)
BeginDialog|✔|❌
BreakLoop|✔|✔
CSATQuestion|✔|❌
CancelAllDialogs|✔|❌
CancelDialog|✔|❌
ClearAllVariables|✔|✔
ConditionGroup|✔|✔|Includes one or more `ConditionItem` and an `ElseActions`
ContinueLoop|✔|✔
CreateSearchQuery|✔|❌
DeleteActivity|✔|❓
DisableTrigger|✔|❌
DisconnectedNodeContainer|✔|❌
EditTable|✔|❓
EditTableV2|✔|✔|Are both `EditTable*` actions needed?
EmitEvent|✔|❓
EndConversation|✔|✔
EndDialog|✔|❌
Foreach|✔|✔
GetActivityMembers|✔|❓
GetConversationMembers|✔|❓
GotoAction|✔|✔
HttpRequestAction|✔|❌
InvokeAIBuilderModelAction|✔|❌
InvokeAgent|❌|✔|Based on _Foundry_ agent identifier
InvokeConnectorAction|✔|❌
InvokeCustomModelAction|✔|❌
InvokeFlowAction|✔|❌
InvokeSkillAction|✔|❌
LogCustomTelemetryEvent|✔|✔
OAuthInput|✔|❌
ParseValue|✔|✔
Question|✔|❓|Solicits user input
RecognizeIntent|✔|❓
RepeatDialog|✔|❌
ReplaceDialog|✔|❌
ResetVariable|✔|✔
SearchAndSummarizeContent|✔|❌
SearchAndSummarizeWithCustomModel|✔|❌
SearchKnowledgeSources|✔|❌
SendActivity|✔|✔
SetTextVariable|✔|✔
SetVariable|✔|✔
SignOutUser|✔|❌
TransferConversation|✔|❌
TransferConversationV2|✔|❌
UnknownDialogAction|✔|❓
UpdateActivity|✔|❓
WaitForConnectorTrigger|✔|❌

#### Open Questions
- Can a _Copilot Studio_ workflow be hosted in _Foundry_?  **NO**
- Can a _Foundry_ workflow be utlized in _Copilot Studio_?  **NO**
- Can a _Foundry_ workflow be hosted in different projects without modification? **NO**  
  (Agent identifiers differ even if model deployments match.)
- Is a _Foundry_ workfow specific to a single _Foundry_ project? **YES**
- Can user defined workflow YAML be uploaded to a _Foundry_ project? **YES**  
  (YAML can be authored in VS Code via a designer extension.)
- What is the validation process for a declarative YAML workflow?
