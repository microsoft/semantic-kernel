/**
 * Base class for all Search related exceptions.
 */
export class SearchException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'SearchException'
  }
}

/**
 * Raised when there are no hits in the search results.
 */
export class SearchResultEmptyError extends SearchException {
  constructor(message: string) {
    super(message)
    this.name = 'SearchResultEmptyError'
  }
}

/**
 * An error occurred while executing a text search function.
 */
export class TextSearchException extends SearchException {
  constructor(message: string) {
    super(message)
    this.name = 'TextSearchException'
  }
}

/**
 * Raised when invalid options are given to a TextSearch function.
 */
export class TextSearchOptionsException extends SearchException {
  constructor(message: string) {
    super(message)
    this.name = 'TextSearchOptionsException'
  }
}
