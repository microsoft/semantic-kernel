# Object Model Requirements

## **Types**

- ✔ **Message**
    - Corresponds with user input or an agent response.
    - Requires robust support for how to access, identify most recent, transfer, count, etc...

- ❌ **Thread**
    - Every workflow invocation is associated with a single "user thread"
    - Each agent is associated with its own dedicated thread that is implicitly managed.
    - Exposing an explicit thread primitive within a workflow introduces additional complexity that is not required.

## **Actions**

The following table enumerates the actions currently supported by _Copilot Studio_ 
and those to be introduced specific to _Foundry_ workflows.
_CopilotStudio_ actions not supported by _Foundry_ workflows are marked with `❌`.

Name|Copilot Studio|Foundry|Priority|Note
:--|:--:|:--:|:--:|:--
ActionScope|✔|✔|✔|Container for actions
ActivateExternalTrigger|✔|❓||Not supported for v0.  Evaluate trigger actions in next phase.
AdaptiveCardPrompt|✔|❌
AnswerQuestionWithAI|✔|❌||Insufficient definition for _Foundry_. Use `InvokeChatCompletion` instead.
BeginDialog|✔|❌
BreakLoop|✔|✔|✔
CSATQuestion|✔|❌
CancelAllDialogs|✔|❌
CancelDialog|✔|❌
ClearAllVariables|✔|✔|✔
ConditionGroup|✔|✔|✔|Includes one or more `ConditionItem` and an `ElseActions`.
ContinueLoop|✔|✔|✔
CreateSearchQuery|✔|❌
DeleteActivity|✔|❓|❓|How does an _Activity_ differ from a _Message_?
DisableTrigger|✔|❓||Not supported for v0.  Evaluate trigger actions in next phase.
DisconnectedNodeContainer|✔|❌
EditTable|✔|❌||Favor `EditTableV2` instead.
EditTableV2|✔|✔|✔
EmitEvent|✔|❌
EndConversation|✔|✔|✔|Terminal action when specified.  A sequential workflow will automatically end after the final action.
EndDialog|✔|❌
Foreach|✔|✔|✔
GetActivityMembers|✔|❌
GetConversationMembers|✔|❌
GotoAction|✔|✔|✔
HttpRequestAction|✔|❌||Favor usage of `InvokeTool` instead.
InvokeAIBuilderModelAction|✔|❌
InvokeAgent|❌|✔|✔|Produce a response for _Foundry_ agent based on its name or identifier.
InvokeChatCompletion|❌|✔|✔|Invoke model using chat-completion API.
InvokeConnectorAction|✔|❌
InvokeCustomModelAction|✔|❌
InvokeFlowAction|✔|❌
InvokeResponse|❌|✔||Invoke model using response API.  Not supported for v0.  
InvokeSkillAction|✔|❌
InvokeTool|❌|✔|❓|Unify how tools are defined and invoke directly (outside of agent invocation).  Can include _Open API_, _Azure Function_, _Search_, etc...
LogCustomTelemetryEvent|✔|❓||Not supported for v0. Could be captured as part of a [_Foundry_ Observability](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/tracing).
OAuthInput|✔|❌
ParseValue|✔|✔|✔
Question|✔|✔|✔|Solicits user input (human-in-the-loop).
RecognizeIntent|✔|❌
RepeatDialog|✔|❌
ReplaceDialog|✔|❌
ResetVariable|✔|✔|✔
SearchAndSummarizeContent|✔|❌
SearchAndSummarizeWithCustomModel|✔|❌
SearchKnowledgeSources|✔|❌
SendActivity|✔|❓|❓|How does an _Activity_ differ from a _Message_?
SetTextVariable|✔|✔|✔
SetVariable|✔|✔|✔
SignOutUser|✔|❌
TransferConversation|✔|❌||Favor `TransferConversationV2` instead, if at all.
TransferConversationV2|✔|❌||Not supported for v0.  Could invoke invoke a different workflow; although, overloading action may be undesirable.
UnknownDialogAction|✔|❌||Serialization construct that represents an unknown action. Not explicitly expressed as a workflow action.
UpdateActivity|✔|❓|❓|How does an _Activity_ differ from a _Message_?
WaitForConnectorTrigger|✔|❓||Not supported for v0.  Evaluate trigger actions in next phase.

## Behaviors

### Is a _Foundry_ workflow specific to a single _Foundry_ project?

Always.
This implies that a _Foundry_ workflow has access to the resources associated with its project, 
including: models, agents, and connections.

### Can user defined workflow YAML be uploaded to a _Foundry_ project?

Yes.
As _VS Code_ extension will support the authoring of _Foundry_ workflows in YAML.
The resulting YAML can be uploaded to a _Foundry_ project.
Ostensibly, one could directly author raw YAML and upload.


### Can a Foundry workflow be hosted in different projects without modification?

Agent identifiers differ across projects even if model deployments match.
This creates an incompatibility between projects,
exception in the case where an agent is identified by name only.


### Can a _Copilot Studio_ workflow be hosted in _Foundry_ or vice-versa?

Since the actions diverge between what is supported for _Copilot Studio_ and _Foundry_, 
interoperability between platforms is not generally supported.
The special case where a workflow contains only the core actions that are supported by both platforms
might allow for interoperablity.

### How and when are declarative workflows (YAML) validated?

Validating a declarative workflow prior to execution provides a superior user experience.
This validation should be triggered for any workflow update:
- Uploading a YAML file that creates or overwrites a workflow.
- Creating or editing a workflow from the designer.

Validation must include:
- Schema validation:
  Can the YAML be deserialized and parsed?
- Functional validation:
  Does the YAML consist of only the actions supported by the _Foundry_ object model? 
  Is each action properly defined with valid identifiers?
- Reference validation:
  Are all referenced resources (models, agents, connections) valid and accessible?

At runtime the references shall be re-validated and, where relevant, logical names translated into physical identifiers.
