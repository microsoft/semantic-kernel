/**
 * Semantic Kernel for Node.js/TypeScript
 *
 * Main entry point for the Semantic Kernel SDK
 */

// Export core kernel
export { Kernel } from './semantic-kernel/kernel'

// Export common types and classes
export type { KernelArguments } from './semantic-kernel/functions/kernel-arguments'
export type { KernelFunction } from './semantic-kernel/functions/kernel-function'
export type { KernelPlugin } from './semantic-kernel/kernel'

// Re-export commonly used items for convenience
export { ChatHistory } from './semantic-kernel/contents/chat-history'
export { ChatMessageContent } from './semantic-kernel/contents/chat-message-content'
export { TextContent } from './semantic-kernel/contents/text-content'
export { AuthorRole } from './semantic-kernel/contents/utils/author-role'
