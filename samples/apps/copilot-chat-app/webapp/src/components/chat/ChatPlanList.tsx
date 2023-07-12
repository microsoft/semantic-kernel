import {
    Table,
    TableBody,
    TableCell,
    TableCellLayout,
    TableHeader,
    TableRow,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { DocumentTextRegular } from '@fluentui/react-icons';
import * as React from 'react';
import { SharedStyles } from '../../styles';

interface ChatPlanListProps {
    chatId: string;
}

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...SharedStyles.scroll,
    },
    table: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tableHeader: {
        fontWeight: tokens.fontSizeBase600,
    },
});

export const ChatPlanList: React.FC<ChatPlanListProps> = ({ chatId }) => {
    const classes = useClasses();
    return (
        <div className={classes.root}>
            <h2>Plans</h2>
            <p>Chat ID: {chatId} -- not necessary. </p> {/* Display the chatId */}
            <p>List all the plans that have been generated in the chat session here ...</p>
            <Table aria-label="External resource table" className={classes.table}>
                <TableHeader>
                    <TableRow>
                        <TableCell>Plan</TableCell>
                        <TableCell>Created On</TableCell>
                        <TableCell>Token Usage</TableCell>
                        <TableCell>Models Used</TableCell>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    <TableRow>
                        <TableCell>
                            <TableCellLayout media={<DocumentTextRegular />}>
                                <a href="#file-url">Summary of what plan does</a>
                            </TableCellLayout>
                        </TableCell>
                        <TableCell>{new Date().toLocaleString()}</TableCell>
                        <TableCell>1323</TableCell>
                        <TableCell>chat-3.5-turbo</TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </div>
    );
};
