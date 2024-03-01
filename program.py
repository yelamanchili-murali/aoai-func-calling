import os
import json
from openai import AzureOpenAI

# client = OpenAI()
client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT");

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    print ("get_current_weather called: ", location, " ", unit);
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def get_most_popular_restaurant(location, preference="vegan"):
    """Get the most popular restaurant in a given location"""
    print ("get_most_popular_restaurant called: ", location, " ", preference);
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "restaurant": "Sushi Dai"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "restaurant": "House of Prime Rib"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "restaurant": "Le Jules Verne"})
    else:
        return json.dumps({"location": location, "restaurant": "unknown"})

def run_conversation():
    # Step 1: send the conversation and available functions to the model
    messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris? And what is the most popular vegan restaurant in each city?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_most_popular_restaurant",
                "description": "Get the most popular restaurant in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "preference": {"type": "string", "enum": ["vegan", "seafood", "any"]},
                    },
                    "required": ["location", "preference"],
                },
            }
        }

    ]
    response = client.chat.completions.create(
        model=aoai_deployment,
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
            "get_most_popular_restaurant": get_most_popular_restaurant,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            if(function_name == "get_current_weather"):
                function_response = get_current_weather(location=function_args.get("location"),
                    unit=function_args.get("unit"))
            elif(function_name == "get_most_popular_restaurant"):
                function_response = get_most_popular_restaurant(location=function_args.get("location"),
                    preference=function_args.get("preference"))
            else:
                # unhandled function
                function_response = "I'm sorry, I don't know how to handle that function"

            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model=aoai_deployment,
            messages=messages,
        )  # get a new response from the model where it can see the function response
        
        print("-" * 80)
        print(second_response.choices[0].message.content);
        print("-" * 80)

        return second_response
print(run_conversation())
