from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Blueprint
import os
import requests

# Load environment variables from the .env file
load_dotenv()

gpt_bp = Blueprint('gpt', __name__)

# Access the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("ERROR: OPENAI_API_KEY not found in environment variables.")

try:
    client = OpenAI(api_key=openai_api_key)
    print("OpenAI client initialized successfully.")
except Exception as e:
    print(f"ERROR initializing OpenAI client: {str(e)}")


@gpt_bp.route("/generate", methods=["POST"])
def generate_response(role, prompt):
    try:
        print(f"generate_response called with role: {role}, prompt: {prompt}")
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": role},
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        print(f"OpenAI response: {completion.choices[0].message.content}")
        return completion.choices[0].message.content
    except Exception as e:
        print(f"ERROR in generate_response: {str(e)}")
        return jsonify({"error": str(e)}), 500


@gpt_bp.route("/chat_response", methods=["POST"])
def generate_response_chat():
    try:
        # Parse JSON from the request body
        data = request.get_json()
        print("Incoming data:", data)  # Log full request data

        memory = data.get("memory")
        print("Extracted memory:", memory)  # Log extracted memory array

        if not memory:
            return jsonify({"error": "The 'memory' field is required."}), 400

        # Extract the latest user message from the memory
        user_input = next((msg["content"] for msg in reversed(
            memory) if msg["role"] == "user"), None)
        print("Extracted user input:", user_input)  # Log extracted user input

        if not user_input:
            return jsonify({"error": "No user input found in the memory."}), 400

        api_json = [{"description": "Gets all of a user's food scans",
            "url": "http://localhost:3001/foodmodel/api/foodscans/<int:user_id>"}]

        api_url = identify_intent(user_input, api_json)

        if not api_url or not api_url.startswith("http"):
            print(f"Invalid API URL identified: {api_url}")
            return jsonify({"error": "Failed to identify a valid API URL."}), 500

        # Execute the API URL
        try:
            api_response = requests.get(api_url)
            api_response.raise_for_status()
            api_result = api_response.json()  # Assuming the API returns JSON
        except Exception as e:
            print(f"Error while calling the API: {e}")
            return jsonify({"error": "Failed to retrieve data from the identified API."}), 500

        # Include api_result in the context for the GPT model
        system_message = {
            "role": "system",
            "content": f"The API returned the following data: {api_result}. Use this information to answer the user's query."
        }

        # Add system message to memory
        updated_memory = [system_message] + memory

        # Generate the response
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=updated_memory,
        )

        return jsonify({
            "response": completion.choices[0].message.content
            # "api_url": api_url,
            # "api_result": api_result
        })

    except Exception as e:
        print("Error in /chat_response:", str(e))  # Log exception
        return jsonify({"error": str(e)}), 500



def identify_intent(user_input, api_descriptions):
    """
    Identifies the intent of the user's input and maps it to the most suitable API URL.

    Args:
        user_input (str): The input from the user.
        api_descriptions (list): A list of dictionaries with "description" and "url" keys.

    Returns:
        str: The URL of the most suitable API based on the user's intent.
    """

    # Prepare the prompt for the OpenAI API
    api_descriptions_text = "\n".join(
        [f"Description: {api['description']}\nURL: {api['url']}" for api in api_descriptions]
    )

    prompt = (
        "The following are API descriptions with their respective URLs. Based on the user's input, determine the most suitable API URL. "
        "Return only the URL.\n\n"
        f"User input: {user_input}\n\n"
        f"API descriptions:\n{api_descriptions_text}\n\n"
        "Suitable API URL:"
    )

    try:
        # Call the OpenAI API using generate_response
        role = "You are an assistant that maps user queries to appropriate API URLs."
        url = generate_response(role, prompt)
        return url.strip()
    except Exception as e:
        print(f"Error while identifying intent: {e}")
        return None
