# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext
import sys, json

from showlist_details import ShowListDetails


class Intent(Enum):
    CANCEL = "Cancel"
    NONE_INTENT = "NoneIntent"
    SHOW_LIST = "ShowList"

def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score
            print("max_intent: {}, max_value: {}".format(max_intent, max_value))

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )
            
            if intent == Intent.SHOW_LIST.value:
                result = ShowListDetails()

                # We need to get the result from the LUIS JSON which at every level returns an array.
                # incidents
                alist = recognizer_result.entities.get("$instance", {}).get(
                    "incidents", []
                )
                if len(alist) > 0:
                    result.alist = alist[0]["text"].capitalize()

                # outages
                alist = recognizer_result.entities.get("$instance", {}).get(
                "outages", []
                )
                if len(alist) > 0:
                    result.alist = alist[0]["text"].capitalize()

                # changes
                alist = recognizer_result.entities.get("$instance", {}).get(
                    "changes", []
                )
                if len(alist) > 0:
                    result.alist = alist[0]["text"].capitalize()

                    blist = recognizer_result.entities.get("$instance", {}).get(
                    "stguid", []
                    )
                    if len(blist) > 0:
                        result.guid = blist[0]["text"].replace(" ", "")
                    
                    blist = recognizer_result.entities.get("$instance", {}).get(
                    "changesage", []
                    )
                    if len(blist) > 0:
                        result.age = int(''.join(c for c in blist[0]["text"] if c.isdigit()))
                    print("Changes entry: {}, {}, {}".format(result.alist, result.guid, result.age))

                # incident
                alist = recognizer_result.entities.get("$instance", {}).get(
                    "incident", []
                )
                if len(alist) > 0:
                    result.alist = alist[0]["text"].capitalize()

                    blist = recognizer_result.entities.get("$instance", {}).get(
                    "incidentid", []
                    )
                    if len(blist) > 0:
                        result.incidentid = blist[0]["text"].replace(" ", "")
                    
                    print("Changes entry: {}, {}, {}".format(result.alist, result.incidentid))

                if not result.alist:
                    result.unsupported_list.append(
                        alist[0]["text"].capitalize()
                    )

        except Exception as exception:
            print(exception)

        print("intent: {}".format(intent))
        print("result: {}, {}, {}".format(result.alist, result.guid, result.age))

        return intent, result
