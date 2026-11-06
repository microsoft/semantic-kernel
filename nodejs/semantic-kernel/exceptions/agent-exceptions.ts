/**
 * Base class for all agent exceptions.
 */
export class AgentException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'AgentException'
  }
}

/**
 * The requested file was not found.
 */
export class AgentFileNotFoundException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentFileNotFoundException'
  }
}

/**
 * An error occurred while initializing the agent.
 */
export class AgentInitializationException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentInitializationException'
  }
}

/**
 * An error occurred while executing the agent.
 */
export class AgentExecutionException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentExecutionException'
  }
}

/**
 * An error occurred while invoking the agent.
 */
export class AgentInvokeException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentInvokeException'
  }
}

/**
 * An error occurred while invoking the agent chat.
 */
export class AgentChatException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentChatException'
  }
}

/**
 * An error occurred while reducing the chat history.
 */
export class AgentChatHistoryReducerException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentChatHistoryReducerException'
  }
}

/**
 * An error occurred while initializing the agent thread.
 */
export class AgentThreadInitializationException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentThreadInitializationException'
  }
}

/**
 * An error occurred while performing an operation on the agent thread.
 */
export class AgentThreadOperationException extends AgentException {
  constructor(message: string) {
    super(message)
    this.name = 'AgentThreadOperationException'
  }
}
