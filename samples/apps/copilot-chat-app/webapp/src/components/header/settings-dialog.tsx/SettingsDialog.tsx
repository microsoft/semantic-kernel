// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogSurface,
    DialogTitle,
    makeStyles,
    shorthands,
} from '@fluentui/react-components';
import React from 'react';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { SettingSection } from './SettingSection';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100%',
    },
});

interface ISettingsDialogProps {
    open: boolean;
    closeDialog: () => void;
}

export const SettingsDialog: React.FC<ISettingsDialogProps> = ({ open, closeDialog }) => {
    const classes = useClasses();
    const { settings } = useAppSelector((state: RootState) => state.app);

    return (
        <Dialog
            open={open}
            onOpenChange={(_ev: any, data: DialogOpenChangeData) => {
                if (!data.open) closeDialog();
            }}
        >
            <DialogSurface>
                <DialogBody className={classes.root}>
                    <DialogTitle>Settings</DialogTitle>
                    <DialogContent>
                        {settings.map((setting) => {
                            return <SettingSection key={setting.title} setting={setting} />;
                        })}
                    </DialogContent>
                    <DialogActions>
                        <Button appearance="secondary" onClick={() => closeDialog()}>
                            Close
                        </Button>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
