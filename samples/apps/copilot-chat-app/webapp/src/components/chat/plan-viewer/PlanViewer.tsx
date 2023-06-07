import { Button, Text, makeStyles, mergeClasses, shorthands } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, DismissCircle24Regular } from '@fluentui/react-icons';
import { useState } from 'react';
import { ChatMessageState } from '../../../libs/models/ChatMessage';
import { IPlan } from '../../../libs/models/Plan';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { updateMessageState } from '../../../redux/features/conversations/conversationsSlice';
import { PlanStepCard } from './PlanStepCard';

const useClasses = makeStyles({
    container: {
        ...shorthands.gap('11px'),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'baseline',
    },
    buttons: {
        display: 'flex',
        flexDirection: 'row',
        marginTop: '12px',
        marginBottom: '12px',
        ...shorthands.gap('16px'),
    },
    status: {
        ...shorthands.gap('10px'),
    },
    text: {
        alignSelf: 'center',
    },
});

interface PlanViewerProps {
    plan: IPlan;
    planState: ChatMessageState;
    messageIndex: number;
    messageContent: string;
    getResponse: (
        value: string,
        userApprovedPlan?: boolean,
        approvedPlanJson?: string,
        planUserIntent?: string,
    ) => Promise<void>;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({
    plan,
    planState,
    messageIndex,
    messageContent,
    getResponse,
}) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);

    const [isDirty, setIsDirty] = useState(false);

    var stepCount = 1;

    const onPlanApproval = async () => {
        dispatch(
            updateMessageState({
                newMessageState: ChatMessageState.PlanApproved,
                messageIndex: messageIndex,
                chatId: selectedId,
            }),
        );

        // Extract plan from bot response
        const parsedContent = JSON.parse(messageContent);
        var proposedPlan = parsedContent.proposedPlan;

        // Apply any edits
        if (isDirty) {
            if (parsedContent.Type === 'Sequential') {
                // TODO: handle nested steps
                // TODO: handle different input value data structures i.e., arrays
                // Update message in chat history to reflect new plan object
                for (var i = 0; i < plan.steps.length; i++) {
                    proposedPlan.steps[i].parameters = plan.steps[i].stepInputs;
                }
            } else {
                // TODO: Check if parameters or state take precendence
                proposedPlan.parameters = plan.steps[0].stepInputs;
            }
        }

        // Invoke plan
        await getResponse('Yes, proceed', true, JSON.stringify(proposedPlan), plan?.userIntent);
    };

    const onPlanCancel = async () => {
        dispatch(
            updateMessageState({
                newMessageState: ChatMessageState.PlanRejected,
                messageIndex: messageIndex,
                chatId: selectedId,
            }),
        );

        // Bail out of plan
        await getResponse('No, cancel', false);
    };

    return (
        <div className={classes.container}>
            <Text>Based on the request, Copilot Chat will run the following steps:</Text>
            <Text weight="bold">{`Goal: ${plan.description}`}</Text>
            {plan.steps.map((step: IPlan) => {
                const stepIndex = stepCount++;
                return (
                    <PlanStepCard
                        key={`Plan step: ${stepIndex}`}
                        index={stepIndex}
                        step={step}
                        setIsPlanDirty={setIsDirty}
                        enableEdit={planState === ChatMessageState.PlanApprovalRequired}
                    />
                );
            })}
            {planState === ChatMessageState.PlanApprovalRequired && (
                <>
                    Would you like to proceed with the plan?
                    <div className={classes.buttons}>
                        <Button appearance="secondary" onClick={onPlanCancel}>
                            No, cancel plan
                        </Button>
                        <Button type="submit" appearance="primary" onClick={onPlanApproval}>
                            Yes, proceed
                        </Button>
                    </div>
                </>
            )}
            {planState === ChatMessageState.PlanApproved && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <CheckmarkCircle24Regular />
                    <Text className={classes.text}> Plan Executed</Text>
                </div>
            )}
            {planState === ChatMessageState.PlanRejected && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <DismissCircle24Regular />
                    <Text className={classes.text}> Plan Cancelled</Text>
                </div>
            )}
        </div>
    );
};
