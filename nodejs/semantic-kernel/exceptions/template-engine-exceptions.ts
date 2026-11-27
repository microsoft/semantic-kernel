/**
 * Base exception for block errors.
 */
export class BlockException extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'BlockException'
  }
}

/**
 * A block syntax error occurred.
 */
export class BlockSyntaxError extends BlockException {
  constructor(message: string) {
    super(message)
    this.name = 'BlockSyntaxError'
  }
}

/**
 * An error occurred while rendering a block.
 */
export class BlockRenderException extends BlockException {
  constructor(message: string) {
    super(message)
    this.name = 'BlockRenderException'
  }
}

/**
 * An invalid VarBlock syntax was found.
 */
export class VarBlockSyntaxError extends BlockSyntaxError {
  constructor(content: string) {
    super(
      `A VarBlock starts with a '$' followed by at least one letter, ` +
        `number or underscore, anything else is invalid. ` +
        `The content provided was: ${content}`
    )
    this.name = 'VarBlockSyntaxError'
  }
}

/**
 * An error occurred while rendering a VarBlock.
 */
export class VarBlockRenderError extends BlockRenderException {
  constructor(message: string) {
    super(message)
    this.name = 'VarBlockRenderError'
  }
}

/**
 * An invalid FunctionIdBlock syntax was found.
 */
export class FunctionIdBlockSyntaxError extends BlockSyntaxError {
  constructor(content: string) {
    super(
      `A FunctionIdBlock is composed of either a plugin name and ` +
        `function name separated by a single dot, or just a function name. ` +
        `Both plugin and function names can only contain letters, numbers and underscores. ` +
        `The content provided was: ${content}`
    )
    this.name = 'FunctionIdBlockSyntaxError'
  }
}

/**
 * An invalid NamedArgBlock syntax was found.
 */
export class NamedArgBlockSyntaxError extends BlockSyntaxError {
  constructor(content: string) {
    super(
      `A NamedArgBlock starts with a name (letters, numbers or underscore) ` +
        `followed by a single equal sign, then the value of the argument, ` +
        `which can either be a VarBlock (starting with '$') ` +
        `or a ValBlock (text surrounded by quotes). ` +
        `The content provided was: ${content}`
    )
    this.name = 'NamedArgBlockSyntaxError'
  }
}

/**
 * An invalid ValBlock syntax was found.
 */
export class ValBlockSyntaxError extends BlockSyntaxError {
  constructor(content: string) {
    super(
      `A ValBlock starts with a single or double quote followed by at least one letter, ` +
        `finishing with the same type of quote as the first one. ` +
        `The content provided was: ${content}`
    )
    this.name = 'ValBlockSyntaxError'
  }
}

/**
 * An invalid CodeBlock syntax was found.
 */
export class CodeBlockSyntaxError extends BlockSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'CodeBlockSyntaxError'
  }
}

/**
 * An error occurred while tokenizing a CodeBlock.
 */
export class CodeBlockTokenError extends BlockException {
  constructor(message: string) {
    super(message)
    this.name = 'CodeBlockTokenError'
  }
}

/**
 * An error occurred while rendering a CodeBlock.
 */
export class CodeBlockRenderException extends BlockRenderException {
  constructor(message: string) {
    super(message)
    this.name = 'CodeBlockRenderException'
  }
}

/**
 * An invalid Template syntax was found.
 */
export class TemplateSyntaxError extends BlockSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'TemplateSyntaxError'
  }
}

/**
 * An error occurred while rendering a Template.
 */
export class TemplateRenderException extends BlockRenderException {
  constructor(message: string) {
    super(message)
    this.name = 'TemplateRenderException'
  }
}

/**
 * An invalid HandlebarsTemplate syntax was found.
 */
export class HandlebarsTemplateSyntaxError extends BlockSyntaxError {
  constructor(message: string) {
    super(message)
    this.name = 'HandlebarsTemplateSyntaxError'
  }
}

/**
 * An error occurred while rendering a HandlebarsTemplate.
 */
export class HandlebarsTemplateRenderException extends BlockRenderException {
  constructor(message: string) {
    super(message)
    this.name = 'HandlebarsTemplateRenderException'
  }
}
