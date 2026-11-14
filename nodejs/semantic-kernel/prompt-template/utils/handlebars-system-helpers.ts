import { ChatHistory } from '../../contents/chat-history'
import { ChatMessageContent } from '../../contents/chat-message-content'
import { CHAT_MESSAGE_CONTENT_TAG } from '../../contents/const'
import { createDefaultLogger } from '../../utils/logger'

const logger = createDefaultLogger('HandlebarsSystemHelpers')

/**
 * Type definition for Handlebars helper context.
 */
interface HandlebarsContext {
  context: any
}

/**
 * Type definition for Handlebars options.
 */
interface HandlebarsOptions {
  fn?: (context: any) => string
  inverse?: (context: any) => string
}

/**
 * Helper for rendering chat messages from ChatHistory.
 */
function _messages(this: HandlebarsContext, _options: HandlebarsOptions, ..._args: any[]): string {
  if (!(this.context?.['chat_history'] instanceof ChatHistory)) {
    return ''
  }
  return this.context['chat_history'].toPrompt()
}

/**
 * Helper for rendering a single chat message to prompt format.
 */
function _messageToPrompt(this: HandlebarsContext, ..._args: any[]): string {
  if (this.context instanceof ChatMessageContent) {
    return String(this.context.toPrompt())
  }
  return String(this.context)
}

/**
 * Helper for creating a message tag with attributes.
 */
function _message(this: HandlebarsContext, options: HandlebarsOptions, ...args: any[]): string {
  const kwargs = args[args.length - 1] || {}

  // Build opening tag with attributes
  let start = `<${CHAT_MESSAGE_CONTENT_TAG}`
  for (const [key, value] of Object.entries(kwargs.hash || {})) {
    if (value !== null && value !== undefined) {
      const strValue = typeof value === 'object' && 'value' in value ? value.value : value
      start += ` ${key}="${strValue}"`
    }
  }
  start += '>'
  const end = `</${CHAT_MESSAGE_CONTENT_TAG}>`

  let content = ''
  try {
    if (options.fn) {
      content = options.fn(this)
    }
  } catch (e) {
    logger.error('Error rendering message content:', e)
    // Ignore error
  }

  return `${start}${content}${end}`
}

/**
 * Helper for setting a value in the context.
 */
function _set(this: HandlebarsContext, ...args: any[]): string {
  const kwargs = args[args.length - 1]
  if (kwargs?.hash) {
    if ('name' in kwargs.hash && 'value' in kwargs.hash) {
      this.context[kwargs.hash.name] = kwargs.hash.value
    }
  }
  if (args.length >= 2 && typeof args[0] === 'string') {
    this.context[args[0]] = args[1]
  }
  return ''
}

/**
 * Helper for getting a value from the context.
 */
function _get(this: HandlebarsContext, ...args: any[]): any {
  if (args.length === 0) {
    return ''
  }
  return this.context[args[0]] || ''
}

/**
 * Helper for creating an array from arguments.
 */
function _array(this: HandlebarsContext, ...args: any[]): any[] {
  // Filter out the options object that Handlebars appends
  return args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
}

/**
 * Helper for creating a range of numbers.
 */
function _range(this: HandlebarsContext, ...args: any[]): number[] {
  const filtered = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  const numArgs: number[] = []

  for (const arg of filtered) {
    if (typeof arg === 'number') {
      numArgs.push(arg)
    } else {
      const num = parseInt(String(arg), 10)
      if (!isNaN(num)) {
        numArgs.push(num)
      }
    }
  }

  if (numArgs.length === 1) {
    return Array.from({ length: numArgs[0] }, (_, i) => i)
  }
  if (numArgs.length === 2) {
    return Array.from({ length: numArgs[1] - numArgs[0] }, (_, i) => numArgs[0] + i)
  }
  if (numArgs.length === 3) {
    const [start, end, step] = numArgs
    const result: number[] = []
    for (let i = start; i < end; i += step) {
      result.push(i)
    }
    return result
  }
  return []
}

/**
 * Helper for concatenating values.
 */
function _concat(this: HandlebarsContext, ...args: any[]): string {
  // Filter out the options object
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.map((v) => String(v)).join('')
}

/**
 * Helper for logical OR operation.
 */
function _or(this: HandlebarsContext, ...args: any[]): boolean {
  // Filter out the options object
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.some((v) => !!v)
}

/**
 * Helper for adding numbers.
 */
function _add(this: HandlebarsContext, ...args: any[]): number {
  // Filter out the options object
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.reduce((sum, v) => sum + parseFloat(String(v)), 0)
}

/**
 * Helper for subtracting numbers.
 */
function _subtract(this: HandlebarsContext, ...args: any[]): number {
  // Filter out the options object
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  if (values.length === 0) return 0
  const first = parseFloat(String(values[0]))
  const rest = values.slice(1).reduce((sum, v) => sum + parseFloat(String(v)), 0)
  return first - rest
}

/**
 * Helper for equality comparison.
 */
function _equals(this: HandlebarsContext, ...args: any[]): boolean {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.length >= 2 && values[0] === values[1]
}

/**
 * Helper for less than comparison.
 */
function _lessThan(this: HandlebarsContext, ...args: any[]): boolean {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.length >= 2 && parseFloat(String(values[0])) < parseFloat(String(values[1]))
}

/**
 * Helper for greater than comparison.
 */
function _greaterThan(this: HandlebarsContext, ...args: any[]): boolean {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.length >= 2 && parseFloat(String(values[0])) > parseFloat(String(values[1]))
}

/**
 * Helper for less than or equal comparison.
 */
function _lessThanOrEqual(this: HandlebarsContext, ...args: any[]): boolean {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.length >= 2 && parseFloat(String(values[0])) <= parseFloat(String(values[1]))
}

/**
 * Helper for greater than or equal comparison.
 */
function _greaterThanOrEqual(this: HandlebarsContext, ...args: any[]): boolean {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  return values.length >= 2 && parseFloat(String(values[0])) >= parseFloat(String(values[1]))
}

/**
 * Helper for JSON serialization.
 */
function _json(this: HandlebarsContext, ...args: any[]): string {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  if (values.length === 0) return ''
  return JSON.stringify(values[0])
}

/**
 * Helper for outputting double open braces.
 */
function _doubleOpen(this: HandlebarsContext, ..._args: any[]): string {
  return '{{'
}

/**
 * Helper for outputting double close braces.
 */
function _doubleClose(this: HandlebarsContext, ..._args: any[]): string {
  return '}}'
}

/**
 * Helper for converting to camelCase.
 */
function _camelCase(this: HandlebarsContext, ...args: any[]): string {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  if (values.length === 0) return ''
  const str = String(values[0])
  return str
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join('')
}

/**
 * Helper for converting to snake_case.
 */
function _snakeCase(this: HandlebarsContext, ...args: any[]): string {
  const values = args.filter((arg) => typeof arg !== 'object' || !('hash' in arg))
  if (values.length === 0) return ''
  let str = String(values[0])
  str = str.replace(/([A-Z]+)([A-Z][a-z])/g, '$1_$2')
  str = str.replace(/([a-z\d])([A-Z])/g, '$1_$2')
  str = str.replace(/-/g, '_')
  return str.toLowerCase()
}

/**
 * Collection of Handlebars system helpers.
 */
export const HANDLEBAR_SYSTEM_HELPERS: Record<string, (...args: any[]) => any> = {
  set: _set,
  get: _get,
  array: _array,
  range: _range,
  concat: _concat,
  or: _or,
  add: _add,
  subtract: _subtract,
  equals: _equals,
  less_than: _lessThan,
  lessThan: _lessThan,
  greater_than: _greaterThan,
  greaterThan: _greaterThan,
  less_than_or_equal: _lessThanOrEqual,
  lessThanOrEqual: _lessThanOrEqual,
  greater_than_or_equal: _greaterThanOrEqual,
  greaterThanOrEqual: _greaterThanOrEqual,
  json: _json,
  double_open: _doubleOpen,
  doubleOpen: _doubleOpen,
  double_close: _doubleClose,
  doubleClose: _doubleClose,
  camel_case: _camelCase,
  camelCase: _camelCase,
  snake_case: _snakeCase,
  snakeCase: _snakeCase,
  message: _message,
  message_to_prompt: _messageToPrompt,
  messageToPrompt: _messageToPrompt,
  messages: _messages,
}
