// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
} from '@fluentui/react-components';
import React from 'react';
import { FileUploader } from './FileUploader';

// TODO: define the extension
const acceptedExtensions = ['sk', 'json'];

interface BotUploaderProps {
    onUpload: (file: File) => void;
}

export const BotUploader: React.FC<BotUploaderProps> = ({ onUpload }) => {
    const [file, setFile] = React.useState<File | undefined>(undefined);

    const onChange = React.useCallback(
        (file: File) => {
            setFile(file);
        },
        [setFile],
    );

    return (
        <DialogSurface>
            <DialogBody>
                <DialogTitle>Load a bot</DialogTitle>
                <DialogContent>
                    <FileUploader acceptedExtensions={acceptedExtensions} onSelectedFile={onChange} />
                </DialogContent>
                <DialogActions>
                    <DialogTrigger disableButtonEnhancement>
                        <Button appearance="secondary">Close</Button>
                    </DialogTrigger>
                    <Button
                        appearance="primary"
                        onClick={() => file && (onUpload(file), setFile(undefined))}
                        disabled={!file}
                    >
                        Upload
                    </Button>
                </DialogActions>
            </DialogBody>
        </DialogSurface>
    );
};
