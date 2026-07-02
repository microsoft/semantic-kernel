/**
 * Template format name for Semantic Kernel template format.
 */
export const KERNEL_TEMPLATE_FORMAT_NAME = 'semantic-kernel' as const

/**
 * Template format name for Handlebars template format.
 */
export const HANDLEBARS_TEMPLATE_FORMAT_NAME = 'handlebars' as const

/**
 * Template format name for Jinja2 template format.
 */
export const JINJA2_TEMPLATE_FORMAT_NAME = 'jinja2' as const

/**
 * Union type for all supported template format types.
 */
export type TemplateFormatTypes = 'semantic-kernel' | 'handlebars' | 'jinja2'
