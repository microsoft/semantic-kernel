/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger, NullLogger } from '../utils/logger';
import { ContextVariables, SKContext } from '../orchestration';
import { Block, BlockTypes, CodeBlock, TextBlock, VarBlock } from './Blocks';
import { IPromptTemplateEngine } from './iPromptTemplateEngine';

/**
 * Given a prompt, that might contain references to variables and functions:
 * - Get the list of references
 * - Resolve each reference
 *   - Variable references are resolved using the context variables
 *   - Function references are resolved invoking those functions
 *     - Functions can be invoked passing in variables
 *     - Functions do not receive the context variables, unless specified using a special variable
 *     - Functions can be invoked in order and in parallel so the context variables must be immutable when invoked within the template
 */
export class PromptTemplateEngine implements IPromptTemplateEngine {
    private readonly _log: ILogger;

    constructor(log?: ILogger) {
        this._log = log ?? new NullLogger();
    }

    public extractBlocks(templateText?: string, validate: boolean = true): Block[] {
        this._log.trace(`Extracting blocks from template: ${templateText}`);
        const blocks = this.tokenizeInternal(templateText);
        if (validate) {
            this.validateBlocksSyntax(blocks);
        }

        return blocks;
    }

    public async render(templateText: string, executionContext: SKContext): Promise<string>;
    public async render(blocks: Block[], executionContext: SKContext): Promise<string>;
    public async render(textOrBlocks: string | Block[], executionContext: SKContext): Promise<string> {
        if (typeof textOrBlocks == 'string') {
            this._log.trace(`Rendering string template: ${textOrBlocks}`);
            const blocks = this.extractBlocks(textOrBlocks);
            return await this.render(blocks, executionContext);
        } else {
            this._log.trace(`Rendering list of ${textOrBlocks.length} blocks`);
            let result = '';
            for (const block of textOrBlocks) {
                switch (block.type) {
                    case BlockTypes.Text:
                        result += block.content;
                        break;

                    case BlockTypes.Variable:
                        result += block.render(executionContext.variables);
                        break;

                    case BlockTypes.Code:
                        result += await block.renderCode(executionContext);
                        break;

                    case BlockTypes.Undefined:
                    default:
                        throw new Error(`Invalid bock of type "${block.type}" encountered.`);
                }
            }

            // TODO: good time to count tokens, though that depends on the model used
            this._log.debug(`Rendered prompt: ${result}`);
            return result;
        }
    }

    public renderVariables(blocks: Block[], variables?: ContextVariables): Block[] {
        this._log.trace('Rendering variables');
        return blocks.map((block) => {
            return block.type != BlockTypes.Variable ? block : new TextBlock(block.render(variables), this._log);
        });
    }

    public async renderCode(blocks: Block[], executionContext: SKContext): Promise<Block[]> {
        this._log.trace('Rendering code');
        const updatedBlocks: Block[] = [];
        for (const block of blocks) {
            if (block.type != BlockTypes.Code) {
                updatedBlocks.push(block);
            } else {
                const codeResult = await block.renderCode(executionContext);
                updatedBlocks.push(new TextBlock(codeResult, this._log));
            }
        }

        return updatedBlocks;
    }

    // Blocks delimitation
    private readonly starter: string = '{';
    private readonly ender: string = '}';

    private tokenizeInternal(template?: string): Block[] {
        // An empty block consists of 4 chars: "{{}}"
        const EMPTY_CODE_BLOCK_LENGTH = 4;
        // A block shorter than 5 chars is either empty or invalid, e.g. "{{ }}" and "{{$}}"
        const MIN_CODE_BLOCK_LENGTH = EMPTY_CODE_BLOCK_LENGTH + 1;

        // Render NULL to ""
        if (template === null) {
            return [new TextBlock('', this._log)];
        }

        // If the template is "empty" return the content as a text block
        if (template.length < MIN_CODE_BLOCK_LENGTH) {
            return [new TextBlock(template, this._log)];
        }

        const blocks: Block[] = [];

        let cursor = 0;
        let endOfLastBlock = 0;

        let startPos = 0;
        let startFound = false;

        while (cursor < template.length - 1) {
            // When "{{" is found
            if (template[cursor] === this.starter && template[cursor + 1] === this.starter) {
                startPos = cursor;
                startFound = true;
            }
            // When "}}" is found
            else if (startFound && template[cursor] === this.ender && template[cursor + 1] === this.ender) {
                // If there is plain text between the current var/code block and the previous one, capture that as a TextBlock
                if (startPos > endOfLastBlock) {
                    blocks.push(new TextBlock(template, endOfLastBlock, startPos, this._log));
                }

                // Skip ahead to the second "}" of "}}"
                cursor++;

                // Extract raw block
                const contentWithDelimiters = this.subStr(template, startPos, cursor + 1);

                // Remove "{{" and "}}" delimiters and trim empty chars
                const contentWithoutDelimiters = contentWithDelimiters
                    .substring(2, contentWithDelimiters.length - EMPTY_CODE_BLOCK_LENGTH)
                    .trim();

                if (contentWithoutDelimiters.length === 0) {
                    // If what is left is empty, consider the raw block a Text Block
                    blocks.push(new TextBlock(contentWithDelimiters, this._log));
                } else {
                    // If the block starts with "$" it's a variable
                    if (VarBlock.hasVarPrefix(contentWithoutDelimiters)) {
                        // Note: validation is delayed to the time VarBlock is rendered
                        blocks.push(new VarBlock(contentWithoutDelimiters, this._log));
                    } else {
                        // Note: validation is delayed to the time CodeBlock is rendered
                        blocks.push(new CodeBlock(contentWithoutDelimiters, this._log));
                    }
                }

                endOfLastBlock = cursor + 1;
                startFound = false;
            }

            cursor++;
        }

        // If there is something left after the last block, capture it as a TextBlock
        if (endOfLastBlock < template.length) {
            blocks.push(new TextBlock(template, endOfLastBlock, template.length, this._log));
        }

        return blocks;
    }

    private subStr(text: string, startIndex: number, stopIndex: number): string {
        return text.substring(startIndex, stopIndex - startIndex);
    }

    private validateBlocksSyntax(blocks: Block[]): void {
        blocks.forEach((block) => {
            const { valid, error } = block.isValid();
            if (!valid) {
                throw new Error(`Prompt template syntax error: ${error}`);
            }
        });
    }
}
