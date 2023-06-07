import { Button, Text, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, DismissCircle24Regular } from '@fluentui/react-icons';
import { useState } from 'react';
import { ChatMessageState } from '../../../libs/models/ChatMessage';
import { IPlan, IPlanInput } from '../../../libs/models/Plan';
import { getPlanView } from '../../../libs/utils/PlanUtils';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { updateMessageState } from '../../../redux/features/conversations/conversationsSlice';
import { PlanStepCard } from './PlanStepCard';

const useClasses = makeStyles({
    container: {
        ...shorthands.gap(tokens.spacingVerticalM),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'baseline',
    },
    buttons: {
        display: 'flex',
        flexDirection: 'row',
        marginTop: tokens.spacingVerticalM,
        marginBottom: tokens.spacingVerticalM,
        ...shorthands.gap(tokens.spacingHorizontalL),
    },
    status: {
        ...shorthands.gap(tokens.spacingHorizontalMNudge),
    },
    text: {
        alignSelf: 'center',
    },
});

interface PlanViewerProps {
    message: string;
    planState: ChatMessageState;
    messageIndex: number;
    getResponse: (
        value: string,
        userApprovedPlan?: boolean,
        approvedPlanJson?: string,
        planUserIntent?: string,
    ) => Promise<void>;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({ message, planState, messageIndex, getResponse }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);
    const [plan, setPlan] = useState(getPlanView(message)!);

    // Track original plan from user message
    const parsedContent = JSON.parse(message);
    const [proposedPlan, setProposedPlan] = useState(parsedContent.proposedPlan);

    const [isDirty, setIsDirty] = useState(false);

    const onPlanApproval = async () => {
        dispatch(
            updateMessageState({
                newMessageState: ChatMessageState.PlanApproved,
                messageIndex: messageIndex,
                chatId: selectedId,
            }),
        );

        // Apply any edits
        if (isDirty) {
            if (parsedContent.Type === 'Sequential') {
                // TODO: handle nested steps
                // TODO: handle different input value data structures i.e., arrays
                // Update message in chat history to reflect new plan object
                for (var i = 0; i < plan.steps.length; i++) {
                    for (var inputIndex in plan.steps[i].stepInputs) {
                        const paramIndex = proposedPlan.steps[i].parameters.findIndex(
                            (element: IPlanInput) => element.Key === plan.steps[i].stepInputs[inputIndex].Key,
                        );
                        proposedPlan.steps[i].parameters[paramIndex] = plan.steps[i].stepInputs[inputIndex];
                    }
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

    const onDeleteStep = (index: number) => {
        setPlan({
            ...plan,
            steps: plan.steps.filter((_step, i) => i !== index),
        });
        setProposedPlan({
            ...proposedPlan,
            steps: proposedPlan.steps.filter((_step: any, i: number) => i !== index),
        });
    };

    return (
        <div className={classes.container}>
            <Text>Based on the request, Copilot Chat will run the following steps:</Text>
            <Text weight="bold">{`Goal: ${plan.description}`}</Text>
            {plan.steps.map((step: IPlan, index) => {
                return (
                    <PlanStepCard
                        key={`Plan step: ${index}`}
                        step={{ ...step, index: index }}
                        setIsPlanDirty={() => setIsDirty(true)}
                        enableEdits={planState === ChatMessageState.PlanApprovalRequired}
                        enableStepDelete={plan.steps.length > 1}
                        onDeleteStep={onDeleteStep}
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
