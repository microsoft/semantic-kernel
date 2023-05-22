// Copyright (c) Microsoft. All rights reserved.

import { BaseService } from './BaseService';

export class DocumentImportService extends BaseService {

    importDocumentAsync = async (
        chatId: string,
        document: File,
        accessToken: string,
    ) => {
        const formData = new FormData();
        formData.append('chatId', chatId);
        formData.append('documentScope', 'Chat');
        formData.append('formFile', document);

        return await this.getResponseAsync(
            {
                commandPath: 'importDocument',
                method: 'POST',
                body: formData,
            },
            accessToken,
        );
    };
}
