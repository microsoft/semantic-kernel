/**
 * Finish reason enumeration.
 */
export enum FinishReason {
  STOP = 'stop',
  LENGTH = 'length',
  CONTENT_FILTER = 'content_filter',
  TOOL_CALLS = 'tool_calls',
  FUNCTION_CALL = 'function_call',
}
