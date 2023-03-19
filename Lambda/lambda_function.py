### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response

def get_rec(level):
    if level == "None":
        rec = "100% bonds (AGG), 0% equities (SPY)"
    elif level == "Low":
        rec = "60% bonds (AGG), 40% equities (SPY)"
    elif level == "Medium":
        rec = "40% bonds (AGG), 60% equities (SPY)"
    elif level == "High":
        rec = "20% bonds (AGG), 80% equities (SPY)"
    else:
        rec = "Invalid Risk Level"
    return rec

def validate_age(age,intent_request):
    # Confirm age is between 0 and 65
    if age is not None:
        age = parse_int(age)
        if age <= 0:
            return build_validation_result(
                False,
                "age",
                "The age cannot be negative."
                "Please provide a valid age."
            )
        elif age >= 65:
            return build_validation_result(
                False,
                "age",
                "Unfortunately, age cannot be above 65."
                "We may only assist if you are under the age of 65."
            )
    return build_validation_result(True,None,None)

def validate_investment_amount(investmentAmount,intent_request):
    # Validate the age to be between 0 and 65
    if investmentAmount is not None:
        investmentAmount = parse_int(investmentAmount)
        if investmentAmount < 5000:
            # error message for lower investment threshold
            return build_validation_result(
                False,
                "investmentAmount",
                "Unfortunately, this investment amount is too low."
                "Please enter an investment amount no less than $5,000."
            )
    return build_validation_result(True,None,None)

### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # Get slots
        slots = get_slots(intent_request)

        # Validate age input
        validation_result = validate_age(age,intent_request)

        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None # Cleans the invalide slot

            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        investment_amount = validate_investment_amount(investment_amount,intent_request)

        if not investment_amount["isValid"]:
            slots[investment_amount["violatedSlot"]] = None # Cleans the invalide slot

            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                investment_amount["violatedSlot"],
                investment_amount["message"],
            )

        output_session_attributes = intent_request["sessionAttributes"]

    rec = get_rec(risk_level)

    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you, {}, you should allocate your funds like so: {}"""
            .format(first_name,rec),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
