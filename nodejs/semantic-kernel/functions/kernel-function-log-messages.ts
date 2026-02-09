import { FunctionResult } from './function-result'
import { KernelArguments } from './kernel-arguments'

/**
 * Kernel function log messages.
 *
 * This class contains static methods to log messages related to kernel functions.
 */
export class KernelFunctionLogMessages {
  /**
   * Log message when a kernel function is invoked.
   *
   * @param logger - The logger instance
   * @param kernelFunctionName - The name of the kernel function
   */
  static logFunctionInvoking(logger: Console, kernelFunctionName: string): void {
    logger.info(`Function ${kernelFunctionName} invoking.`)
  }

  /**
   * Log message with function arguments.
   *
   * @param logger - The logger instance
   * @param args - The function arguments
   */
  static logFunctionArguments(logger: Console, args: KernelArguments): void {
    logger.debug(`Function arguments:`, args)
  }

  /**
   * Log message when a kernel function is invoked successfully.
   *
   * @param _logger - The logger instance (unused, kept for API compatibility)
   * @param kernelFunctionName - The name of the kernel function
   */
  static logFunctionInvokedSuccess(_logger: Console, kernelFunctionName: string): void {
    console.info(`Function ${kernelFunctionName} succeeded.`)
  }

  /**
   * Log message when a kernel function result is returned.
   *
   * @param logger - The logger instance
   * @param functionResult - The function result
   */
  static logFunctionResultValue(logger: Console, functionResult?: FunctionResult | null): void {
    if (functionResult !== undefined && functionResult !== null) {
      try {
        logger.debug(`Function result:`, functionResult)
      } catch (error) {
        logger.error('Function result: Failed to convert result value to string, error:', error)
      }
    } else {
      logger.debug('Function result: None')
    }
  }

  /**
   * Log message when a kernel function fails.
   *
   * @param logger - The logger instance
   * @param error - The error that occurred
   */
  static logFunctionError(logger: Console, error: Error): void {
    logger.error(`Function failed. Error:`, error)
  }

  /**
   * Log message when a kernel function is completed.
   *
   * @param _logger - The logger instance (unused, kept for API compatibility)
   * @param duration - The duration in seconds
   */
  static logFunctionCompleted(_logger: Console, duration: number): void {
    console.info(`Function completed. Duration: ${duration}s`)
  }

  /**
   * Log message when a kernel function is invoked via streaming.
   *
   * @param logger - The logger instance
   * @param kernelFunctionName - The name of the kernel function
   */
  static logFunctionStreamingInvoking(logger: Console, kernelFunctionName: string): void {
    logger.info(`Function ${kernelFunctionName} streaming.`)
  }

  /**
   * Log message when a kernel function is completed via streaming.
   *
   * @param logger - The logger instance
   * @param duration - The duration in seconds
   */
  static logFunctionStreamingCompleted(logger: Console, duration: number): void {
    logger.info(`Function streaming completed. Duration: ${duration}s`)
  }
}
