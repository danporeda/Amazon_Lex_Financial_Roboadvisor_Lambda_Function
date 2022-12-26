import json

# Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###

#Securely converts a non-integer value to integer.
def parse_int(n):
    
    try:
        return int(n)
    except ValueError:
        return float("nan")

# Define a result message structured as Lex response.
def build_validation_result(is_valid, violated_slot, message_content):
   
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }
    
# Validates the data provided by the user.
def validate_data(first_name, age, investment_amount, risk_level, intent_request):

    # Validate that the user's age is > 0 and < 65
    if age is not None:
        age = parse_int(age)
        if age <= 0:
            return build_validation_result(
                False,
                "age",
                f"{first_name}, you must exist in the flesh to have a portfolio.",
            )
        elif age >= 65:
            return build_validation_result(
                False,
                "age",
                f"Congratulations {first_name}, you are aged for retirement already. You are past investing, go collect Social Security.",
            )

    # Verify investment amount is at least $5,000
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                f"We are sorry {first_name}, but the minimum investment is $5000."
            )
            
    # Verify correct input option for risk level
    if risk_level is not None:
        risk = risk_level.lower()
        if risk != "none" and risk != "low" and risk != "medium" and risk != "high":
            return build_validation_result(
                False,
                "riskLevel",
                f"{first_name}, please enter one of the following options: 'none', 'low', 'medium', 'high'",
                )
    
    # A True results is returned if age, investment amount, and risk level are valid
    return build_validation_result(True, None, None)



### Dialog Actions Helper Functions ###

# Fetch all the slots and their values from the current intent.
def get_slots(intent_request):
    
    return intent_request["currentIntent"]["slots"]

# Defines an elicit slot type response.
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):

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

# Defines a delegate slot type response.
def delegate(session_attributes, slots):
   
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }

# Defines a close slot type response.
def close(session_attributes, fulfillment_state, message):
    
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response



# Enhance the Robo Advisor with an Amazon Lambda Function.
# Validate the data provided by the user on the Robo Advisor.

### Intents Handlers ###

# Performs dialog management and fulfillment for recommending a portfolio.
def recommend_portfolio(intent_request):
    
    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    # Gets the invocation source, for Lex dialogs "DialogCodeHook" is expected.
    
    if source == "DialogCodeHook":

        slots = get_slots(intent_request)
       
        validation_result = validate_data(first_name, age, investment_amount, risk_level, intent_request)

        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attributes
        output_session_attributes = intent_request["sessionAttributes"]

        # Once all slots are valid, a delegate dialog is returned to Lex to choose the next course of action.
        return delegate(output_session_attributes, get_slots(intent_request))


    # Assign investing advice message to the bot response based on risk_level
    
    if risk_level.lower() == 'none':
        advice = f"Thank you {first_name}, we recommend 100%\ bonds (AGG), 0% equities (SPY)"
    elif risk_level.lower() == 'low':
        advice = f"Thank you {first_name}, we recommend 60% bonds (AGG), 40% equities (SPY)"
    elif risk_level.lower() == 'medium':
        advice = f"Thank you {first_name}, we recommend 40% bonds (AGG), 60% equities (SPY)"
    elif risk_level.lower() == 'high':
        advice = f"Thank you {first_name}, we recommend 20% bonds (AGG), 80% equities (SPY)"

    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": advice,
        },
    )

### Intents Dispatcher ###
    
# Called when the user specifies an intent for this bot.
def dispatch(intent_request):
    
    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###

# Route the incoming request based on intent.
# The JSON body of the request is provided in the event slot.
def lambda_handler(event, context):
   
    return dispatch(event)