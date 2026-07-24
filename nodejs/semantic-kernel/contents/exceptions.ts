/**
 * Exception raised when content serialization fails.
 */
export class ContentSerializationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ContentSerializationError'
  }
}

/**
 * Exception raised when content initialization fails.
 */
export class ContentInitializationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ContentInitializationError'
  }
}
