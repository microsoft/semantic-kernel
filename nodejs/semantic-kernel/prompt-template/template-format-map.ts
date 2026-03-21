import {
  HANDLEBARS_TEMPLATE_FORMAT_NAME,
  JINJA2_TEMPLATE_FORMAT_NAME,
  KERNEL_TEMPLATE_FORMAT_NAME,
  TemplateFormatTypes,
} from './const'
import { HandlebarsPromptTemplate } from './handlebars-prompt-template'
import { KernelPromptTemplate } from './kernel-prompt-template'
import { PromptTemplateBase } from './prompt-template-base'

/**
 * Map of template format names to their corresponding template classes.
 *
 * Note: Currently only Handlebars is fully implemented.
 * TODO: Implement Jinja2PromptTemplate
 */
export const TEMPLATE_FORMAT_MAP: Record<TemplateFormatTypes, new (...args: any[]) => PromptTemplateBase> = {
  [HANDLEBARS_TEMPLATE_FORMAT_NAME]: HandlebarsPromptTemplate,
  [KERNEL_TEMPLATE_FORMAT_NAME]: KernelPromptTemplate, // Temporary: using Handlebars as fallback
  [JINJA2_TEMPLATE_FORMAT_NAME]: HandlebarsPromptTemplate, // Temporary: using Handlebars as fallback
}
