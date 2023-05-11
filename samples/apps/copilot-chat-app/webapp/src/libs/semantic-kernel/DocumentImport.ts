// Copyright (c) Microsoft. All rights reserved.


export class DocumentImportService {
    constructor(private readonly serviceUrl: string) { }

    importDocumentAsync = async (
        userId: string,
        chatId: string,
        document: File,
        accessToken: string,
    ) => {
        const formData = new FormData();
        formData.append('userId', userId);
        formData.append('chatId', chatId);
        formData.append('documentScope', 'Chat');
        formData.append('formFile', document);
        
        const commandPath = `importDocument`;
        const requestUrl = new URL(commandPath, this.serviceUrl);

        const headers = new Headers({
            Authorization: `Bearer ${accessToken}`,
        });

        try {
            const response = await fetch(requestUrl, {
                method: 'POST',
                body: formData,
                headers: headers,
            });

            if (!response.ok) {
                throw Object.assign(new Error(response.statusText + ' => ' + (await response.text())));
            }
        } catch (e) {
            var additional_error_msg = '';
            if (e instanceof TypeError) {
                // fetch() will reject with a TypeError when a network error is encountered.
                additional_error_msg =
                    '\n\nPlease check that your backend is running and that it is accessible by the app';
            }
            throw Object.assign(new Error(e + additional_error_msg));
        }
    };
}