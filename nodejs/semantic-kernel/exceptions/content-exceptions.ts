/**
 * Base class for all content exceptions.
 */
export class ContentException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ContentException'
  }
}

/**
 * An error occurred while initializing the content.
 */
export class ContentInitializationError extends ContentException {
  constructor(message: string) {
    super(message)
    this.name = 'ContentInitializationError'
  }
}

/**
 * An error occurred while serializing the content.
 */
export class ContentSerializationError extends ContentException {
  constructor(message: string) {
    super(message)
    this.name = 'ContentSerializationError'
  }
}

/**
 * An error occurred while adding content.
 */
export class ContentAdditionException extends ContentException {
  constructor(message: string) {
    super(message)
    this.name = 'ContentAdditionException'
  }
}

/**
 * An error occurred while validating the function name.
 */
export class FunctionCallInvalidNameException extends ContentException {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionCallInvalidNameException'
  }
}

/**
 * An error occurred while validating the function arguments.
 */
export class FunctionCallInvalidArgumentsException extends ContentException {
  constructor(message: string) {
    super(message)
    this.name = 'FunctionCallInvalidArgumentsException'
  }
}

/**
 * An error occurred while reducing chat history.
 */
export class ChatHistoryReducerException extends ContentException {
  constructor(message: string) {
    super(message)
    this.name = 'ChatHistoryReducerException'
  }
}
