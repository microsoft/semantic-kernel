/**
 * Base class for all memory connector exceptions.
 */
export class MemoryConnectorException extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'MemoryConnectorException'
  }
}

/**
 * An error occurred while connecting to the memory connector.
 */
export class MemoryConnectorConnectionException extends MemoryConnectorException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'MemoryConnectorConnectionException'
  }
}

/**
 * An error occurred while initializing the memory connector.
 */
export class MemoryConnectorInitializationError extends MemoryConnectorException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'MemoryConnectorInitializationError'
  }
}

/**
 * The requested resource was not found in the memory connector.
 */
export class MemoryConnectorResourceNotFound extends MemoryConnectorException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'MemoryConnectorResourceNotFound'
  }
}
