/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

export function getLocalCallbackUrl(port: number): string {
    return `http://127.0.0.1:${port}/callback`;
}
