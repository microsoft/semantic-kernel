// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { DocumentImportService } from './DocumentImport';

export const useDocumentImportService = (uri: string) => {
    const [documentImportService] = React.useState(new DocumentImportService(uri));
    return documentImportService;
};