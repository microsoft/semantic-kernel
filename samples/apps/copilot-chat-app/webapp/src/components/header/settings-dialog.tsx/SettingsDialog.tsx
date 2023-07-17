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
    Label,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { TokenUsage } from '../../shared/TokenUsage';
import { SettingSection } from './SettingSection';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100%',
    },
    footer: {
        paddingTop: tokens.spacingVerticalL,
    },
});

interface ISettingsDialogProps {
    open: boolean;
    closeDialog: () => void;
}

export const SettingsDialog: React.FC<ISettingsDialogProps> = ({ open, closeDialog }) => {
    const classes = useClasses();
    const { settings, tokenUsage } = useAppSelector((state: RootState) => state.app);

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
                        <TokenUsage
                            sessionTotal
                            promptUsage={tokenUsage.prompt}
                            dependencyUsage={tokenUsage.dependency}
                        />
                        {settings.map((setting) => {
                            return <SettingSection key={setting.title} setting={setting} />;
                        })}
                        <Label size="small" color="brand" className={classes.footer}>
                            Join the Semantic Kernel open source community!{' '}
                            <a href="https://aka.ms/semantic-kernel" target="_blank" rel="noreferrer">
                                Learn More
                            </a>
                            .
                        </Label>
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
