import { Button } from '@fluentui/react-button';
import { Tooltip, makeStyles } from '@fluentui/react-components';
import {
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
} from '@fluentui/react-dialog';
import { Delete16 } from '../../../shared/BundledIcons';

const useClasses = makeStyles({
    root: {
        width: '450px',
    },
    actions: {
        paddingTop: '10%',
    },
});

interface IEditChatNameProps {
    chatId: string;
    chatName: string;
}

export const DeleteChatDialog: React.FC<IEditChatNameProps> = ({ chatName }) => {
    const classes = useClasses();

    return (
        <Dialog modalType="alert">
            <DialogTrigger>
                <Tooltip content={'Delete chat session'} relationship="label">
                    <Button icon={<Delete16 />} appearance="transparent" aria-label="Edit" />
                </Tooltip>
            </DialogTrigger>
            <DialogSurface className={classes.root}>
                <DialogBody>
                    <DialogTitle>Are you sure you want to delete chat {chatName}?</DialogTitle>
                    <DialogContent>
                        This will permanently delete the chat for you—but not for Chat Copilot. You need to delete
                        anything that you have shared (files, tasks, etc.) separately.
                    </DialogContent>
                    <DialogActions className={classes.actions}>
                        <DialogTrigger action="close" disableButtonEnhancement>
                            <Button appearance="secondary">Cancel</Button>
                        </DialogTrigger>
                        <DialogTrigger action="close" disableButtonEnhancement>
                            <Button
                                appearance="primary"
                                // onClick={ TODO: Handle delete chat }
                            >
                                Delete
                            </Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
