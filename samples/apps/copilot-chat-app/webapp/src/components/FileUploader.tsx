// Copyright (c) Microsoft. All rights reserved.

import { makeStyles } from '@fluentui/react-components';
import React, { forwardRef } from 'react';

const useClasses = makeStyles({
    root: { display: 'none' },
});

interface FileUploaderProps {
    acceptedExtensions: string[] | undefined;
    onSelectedFile: (file: File) => void;
    ref?: React.Ref<HTMLInputElement>;
}

export const FileUploader: React.FC<FileUploaderProps> = forwardRef<HTMLInputElement, FileUploaderProps>(
    ({ acceptedExtensions, onSelectedFile }, ref) => {
        const classes = useClasses();

        const onChange = React.useCallback(
            (event: React.SyntheticEvent) => {
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

        return (
            <input
                ref={ref}
                type="file"
                id="fileInput"
                className={classes.root}
                accept={acceptedExtensions?.join(',')}
                onChange={onChange}
                title="Upload a .pdf, .txt, .jpg, .png or .tiff file"
            />
        );
    },
);

FileUploader.displayName = 'FileUploader';
