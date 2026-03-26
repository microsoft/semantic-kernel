import { experimental } from '../../../utils/feature-stage-decorator'

/**
 * Raised when a handler can't handle the exception.
 */
@experimental
export class CantHandleException extends Error {
  constructor(message?: string) {
    super(message)
    this.name = 'CantHandleException'
  }
}

/**
 * Raised when a message can't be delivered.
 */
@experimental
export class UndeliverableException extends Error {
  constructor(message?: string) {
    super(message)
    this.name = 'UndeliverableException'
  }
}

/**
 * Raised when a message is dropped by an intervention handler.
 */
@experimental
export class MessageDroppedException extends Error {
  constructor(message?: string) {
    super(message || 'Message was dropped by an intervention handler')
    this.name = 'MessageDroppedException'
  }
}

/**
 * Tried to access a value that is not accessible. For example if it is remote cannot be accessed locally.
 */
@experimental
export class NotAccessibleError extends Error {
  constructor(message?: string) {
    super(message)
    this.name = 'NotAccessibleError'
  }
}
