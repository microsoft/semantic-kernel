/**
 * Base class for service-related errors.
 */
export class ServiceException extends Error {
  constructor(message?: string) {
    super(message)
    this.name = 'ServiceException'
    Object.setPrototypeOf(this, new.target.prototype)
  }
}

/**
 * Raised when a request to a service is invalid.
 */
export class ServiceInvalidRequestError extends ServiceException {
  constructor(message?: string) {
    super(message)
    this.name = 'ServiceInvalidRequestError'
  }
}

/**
 * Raised when a service returns an error response.
 */
export class ServiceResponseError extends ServiceException {
  constructor(message?: string) {
    super(message)
    this.name = 'ServiceResponseError'
  }
}

/**
 * Raised when a service is unavailable or times out.
 */
export class ServiceUnavailableError extends ServiceException {
  constructor(message?: string) {
    super(message)
    this.name = 'ServiceUnavailableError'
  }
}

/**
 * Raised when a service fails to initialize.
 */
export class ServiceInitializationError extends ServiceException {
  constructor(message?: string) {
    super(message)
    this.name = 'ServiceInitializationError'
  }
}

/**
 * Raised when execution settings are invalid.
 */
export class ServiceInvalidExecutionSettingsError extends ServiceException {
  constructor(message?: string) {
    super(message)
    this.name = 'ServiceInvalidExecutionSettingsError'
  }
}
