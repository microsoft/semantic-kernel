/**
 * Semantic Kernel for Node.js/TypeScript
 *
 * Main entry point for the Semantic Kernel SDK
 */

// Export core kernel
export { Kernel } from './semantic_kernel/kernel'

// Export common types and classes
export type { KernelArguments } from './semantic_kernel/functions/kernel-arguments'
export type { KernelFunction } from './semantic_kernel/functions/kernel-function'
export type { KernelPlugin } from './semantic_kernel/kernel'

// Re-export commonly used items for convenience
export { ChatHistory } from './semantic_kernel/contents/chat-history'
export { ChatMessageContent } from './semantic_kernel/contents/chat-message-content'
export { TextContent } from './semantic_kernel/contents/text-content'
export { AuthorRole } from './semantic_kernel/contents/utils/author-role'
