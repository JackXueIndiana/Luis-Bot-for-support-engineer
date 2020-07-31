# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datatypes_date_time.timex import Timex

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints
from .cancel_and_help_dialog import CancelAndHelpDialog
from .date_resolver_dialog import DateResolverDialog


class ShowListDialog(CancelAndHelpDialog):
    def __init__(self, dialog_id: str = None):
        super(ShowListDialog, self).__init__(dialog_id or ShowListDialog.__name__)

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(DateResolverDialog(DateResolverDialog.__name__))
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.alist_step,
                    self.confirm_step,
                    self.final_step,
                ],
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    async def alist_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
    
        showlist_details = step_context.options

        if showlist_details.alist is None:
            message_text = "I cannot understand you. Do you want to see incidents, outages or changes? Or you need help on an incident?"
            prompt_message = MessageFactory.text(
                message_text, message_text, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__, PromptOptions(prompt=prompt_message)
            )
        return await step_context.next(showlist_details.alist)

    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        Confirm the information the user has provided.
        :param step_context:
        :return DialogTurnResult:
        """
        showlist_details = step_context.options

        # Capture the results of the previous step
        message_text = ""
        if "Incidents" in showlist_details.alist or "Outages" in showlist_details.alist:
            message_text = (
                f"Please confirm, you want to see the list of recent { showlist_details.alist }."
            )
        elif "Changes" in showlist_details.alist:
            message_text = (
                f"Please confirm, you want to see the list of { showlist_details.alist } for Service Tree GUID {showlist_details.guid} in the last {showlist_details.age} days."
            )
        elif "Incident" in showlist_details.alist:
            message_text = (
                f"Please confirm, you need help on { showlist_details.alist } for IncidentId {showlist_details.incidentid}."
            )
        else:
            message_text = (
                f"Some needed info is missing. Let us do it again."
            )
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=prompt_message)
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """
        Complete the interaction and end the dialog.
        :param step_context:
        :return DialogTurnResult:
        """
        if step_context.result:
            showlist_details = step_context.options

            return await step_context.end_dialog(showlist_details)
        return await step_context.end_dialog()

    def is_ambiguous(self, timex: str) -> bool:
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
