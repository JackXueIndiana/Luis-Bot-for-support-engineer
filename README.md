# Luis-Bot-for-support-engineer
This is a repo of the python app built on the top of Microsoft Language Understanding and BOT framework to provide a toll for support engineer to look at different backend databases. It has four functions:

## Key components
- Conda Python 3.7
- Azure SDK for Bot and Kusto
- Bot Emulator for PC
- Microsoft LUI.AI account

## Key artifacts
- LUI AI app definition: incidentlookup.json. Defines the intent and entities with many utterances for training.
- Python scripts:
-- showlist_detail.py: Data object definition.
-- luis_helper.py: Interaction with Luis ai app.
-- mian_dialog.py: Overall diaglog flow controlling and calling out to Kusto actions
-- showlist_diaglog.py: Diaglogs specific to the intentions and entities.
