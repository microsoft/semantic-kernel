// Copyright (c) Microsoft. All rights reserved.

import { Input } from '@fluentui/react-northstar';
import React from 'react';

interface FileUploaderProps {
    acceptedExtensions: string[] | undefined;
    onSelectedFile: (file: File) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ acceptedExtensions, onSelectedFile }) => {
    const onChange = React.useCallback(
        (event: React.SyntheticEvent<Element>) => {
            const target = event.target as HTMLInputElement;
            const selectedFiles = target.files;
            event.stopPropagation();
            event.preventDefault();
            if (!selectedFiles || selectedFiles.length !== 1) {
                console.error('There are none or multiple selected files.');
                return;
            }
            const file = selectedFiles.item(0);
            if (file) {
                onSelectedFile(file);
            } else {
                console.error('The selected file contains no file object.');
            }
        },
        [onSelectedFile],
    );

    return <Input type="file" id="fileInput" accept={acceptedExtensions?.join(',')} onChange={onChange} />;
};
