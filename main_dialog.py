# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory, TurnContext
from botbuilder.schema import InputHints

from showlist_details import ShowListDetails
from luis_app_recognizer import LuisAppRecognizer
from helpers.luis_helper import LuisHelper, Intent
from .showlist_dialog import ShowListDialog

import helpers.kusto_helper as kusto_helper

class MainDialog(ComponentDialog):
    def __init__(
        self, luis_recognizer: LuisAppRecognizer, showlist_dialog: ShowListDialog
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)

        self._luis_recognizer = luis_recognizer
        self._showlist_dialog_id = showlist_dialog.id

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(showlist_dialog)
        self.add_dialog(
            WaterfallDialog(
                "WFDialog", [self.intro_step, self.act_step, self.final_step]
            )
        )

        self.initial_dialog_id = "WFDialog"

        self.kc = kusto_helper.kustoclient()


    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )

            return await step_context.next(None)
        message_text = (
            str(step_context.options)
            if step_context.options
            else "Hi, I am DRI BOT. What can I help you with today?"
        )
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )

        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=prompt_message)
        )

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            # LUIS is not configured.
            return await step_context.begin_dialog(
                self._showlist_dialog_id, ShowListDetails()
            )

        # Call LUIS and gather any potential details. (Note the TurnContext has the response to the prompt.)
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )

        if intent == Intent.SHOW_LIST.value and luis_result:
            # Show a warning for list if we can't resolve them.
            await MainDialog._show_warning_for_unsupported_list(
                step_context.context, luis_result
            )

            # Run the ShowListDialog giving it whatever details we have from the LUIS call.
            return await step_context.begin_dialog(self._showlist_dialog_id, luis_result)

        else:
            didnt_understand_text = (
                "Sorry, I didn't get that. Please try asking in a different way"
            )
            didnt_understand_message = MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(didnt_understand_message)

        return await step_context.next(None)

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.
        if step_context.result is not None:
            result = step_context.result
            
            kustoRet = ""
            if "incidents" in result.alist.lower():
                kustoRet = self.kc.get_recent_incidents()
            elif "outages" in result.alist.lower():
                kustoRet = self.kc.get_recent_outages()
            elif "changes" in result.alist.lower():
                kustoRet = self.kc.get_recent_changes(stguid=result.guid, age=result.age)
            elif "incident" in result.alist.lower():
                kustoRet = self.kc.get_incident(incidentid=result.incidentid)
            msg_txt = f"I am showing you a list of {result.alist} as below:\r\n {kustoRet}"
            message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            await step_context.context.send_activity(message)

        prompt_message = "What else can I do for you?"
        return await step_context.replace_dialog(self.id, prompt_message)

    @staticmethod
    async def _show_warning_for_unsupported_list(
        context: TurnContext, luis_result: ShowListDetails
    ) -> None:
        if luis_result.unsupported_list:
            message_text = (
                f"Sorry but the following operations are not supported:"
                f" {', '.join(luis_result.unsupported_list)}"
            )
            message = MessageFactory.text(
                message_text, message_text, InputHints.ignoring_input
            )
            await context.send_activity(message)
