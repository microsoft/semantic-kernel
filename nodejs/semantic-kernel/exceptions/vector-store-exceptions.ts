/**
 * Base class for all vector store exceptions.
 */
export class VectorStoreException extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreException'
  }
}

/**
 * Class for all vector store initialization exceptions.
 */
export class VectorStoreInitializationException extends VectorStoreException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreInitializationException'
  }
}

/**
 * Base class for all vector store model exceptions.
 */
export class VectorStoreModelException extends VectorStoreException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreModelException'
  }
}

/**
 * An error occurred while serializing the vector store model.
 */
export class VectorStoreModelSerializationException extends VectorStoreModelException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreModelSerializationException'
  }
}

/**
 * An error occurred while deserializing the vector store model.
 */
export class VectorStoreModelDeserializationException extends VectorStoreModelException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreModelDeserializationException'
  }
}

/**
 * An error occurred while validating the vector store model.
 */
export class VectorStoreModelValidationError extends VectorStoreModelException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreModelValidationError'
  }
}

/**
 * Raised when a mixin is used without the VectorSearchBase Class.
 */
export class VectorStoreMixinException extends VectorStoreException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreMixinException'
  }
}

/**
 * An error occurred while performing an operation on the vector store record collection.
 */
export class VectorStoreOperationException extends VectorStoreException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreOperationException'
  }
}

/**
 * An error occurred while performing an operation on the vector store record collection.
 */
export class VectorStoreOperationNotSupportedException extends VectorStoreOperationException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorStoreOperationNotSupportedException'
  }
}

/**
 * Raised when there is an error executing a VectorSearch function.
 */
export class VectorSearchExecutionException extends VectorStoreOperationException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorSearchExecutionException'
  }
}

/**
 * Raised when invalid options are given to a VectorSearch function.
 */
export class VectorSearchOptionsException extends VectorStoreOperationException {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options)
    this.name = 'VectorSearchOptionsException'
  }
}
