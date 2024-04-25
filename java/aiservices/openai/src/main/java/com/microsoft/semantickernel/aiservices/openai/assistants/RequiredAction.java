package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Details on the action required to continue the run. Will be {@code null} if no action is required.
 */
public interface RequiredAction {

    RequiredActionType getType();

}
