import os
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
import requests
import google.generativeai as genai
from models.model import Users,db, AiChatHistory
from flask_login import current_user
import markdown
import africastalking


load_dotenv()

africastalking.initialize(
    username=os.getenv("AFRICAS_TALKING_USERNAME"),
    api_key=os.getenv("SMS_API_KEY")
)

sms = africastalking.SMS


api_bp = Blueprint("api", __name__)

weather_api_key = os.getenv("WEATHER_API_KEY")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


@api_bp.route("/weather", methods=["GET"])
def weather_api():
    print("WEATHER ROUTE HIT")

    location = request.args.get("location")
    if not location:
        return jsonify({"error": "No location provided"}), 400

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": weather_api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "location": data["name"],
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"]
            })
        else:
            return jsonify({"error": "Weather API failed"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/forecast",methods=["GET"])
def forecast():
    location = request.args.get("location")
    
    if not location:
        return jsonify(
            {
                "error":"Location not found"
            }
        ),400
        
    try:
        api_keys = os.getenv("WEATHER_API_KEY")
        
        url = "http://api.openweathermap.org/data/2.5/forecast"
        
        params = {
            "q":location,
            "appid":api_keys,
            "units":"metric"
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            forecast_data = []
            
            for item in data["list"][:7]:
                forecast_data.append(
                    {
                        "time":item["dt_txt"],
                        "temp":item["main"]["temp"],
                        "rain": item.get("rain", {}).get("3h", 0),
                        "sunny": item.get("weather")[0]["main"] == "Clear"
                    }
                )
                
            return jsonify(forecast_data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "error":f"{str(e)}"
        }
        ),500
        

@api_bp.route("/chat", methods=["POST"])
def chat_api():
    print("Farmhub AI responding...")
    if request.method == "POST":
        
        user_input = request.json.get("message")

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        try:
            model = genai.GenerativeModel("models/gemini-3.1-flash-lite-preview")
            
            for m in genai.list_models():
                print(m.name)
                print(model)
                break

            prompt = f"""
                You are a Kenyan agricultural assistant helping farmers in Kenya.
                Also accept and politely say hi to them either in engish or swahili

                Rules:
                - ONLY answer farming-related questions.
                - If the user asks anything unrelated, reply:
                'I only answer farming-related questions.'

                Tone & Style:
                - Speak in a friendly Kenyan way (simple, practical, relatable).
                - Use light Kenyan expressions like:
                - "Sawa"
                - "Hii ni muhimu"
                - "Kumbuka"
                - "Unaweza pia"
                - Keep it natural, not exaggerated slang.
                - Be clear like you're helping a local farmer.

                Context:
                - Assume the user is in Kenya.
                - Use examples relevant to Kenyan farming (maize, sukuma wiki, dairy, etc.)
                - Consider Kenyan climate (rainy seasons, dry seasons).

                Formatting:
                - Use HTML formatting:
                - <h2> or <h3> for headings
                - Numbered steps for main instructions
                - Bullet points for tips or notes

                Structure:
                <h2>Answer</h2>

                1. Step one  
                - Explanation  
                2. Step two  
                - Explanation  

                <h3>Tips</h3>
                - Tip 1  
                - Tip 2  

                User: {user_input}
                """

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.5,
                    "max_output_tokens": 300
                }
            )
            
        
            if hasattr(response, "candidates") and len(response.candidates) > 0:
                content_obj = response.candidates[0].content

                # Flatten content parts into one string
                if hasattr(content_obj, "parts"):
                    reply = "\n".join(part.text for part in content_obj.parts)
                else:
                    # fallback if it's already plain text
                    reply = str(content_obj)
            else:
                reply = "Sorry, I could not generate a response."

            # Save plain text to database
            chat_data = AiChatHistory(
                user_id=current_user.id,
                question=user_input,
                response=reply
            )
            db.session.add(chat_data)
            db.session.commit()

            # Convert markdown to HTML for frontend
            html_reply = markdown.markdown(reply)

            return jsonify({"reply": html_reply})

        except Exception as e:
            print(f"Error: {e}" )
            return jsonify({"error": str(e)}), 500
    
    else:
        return None
    
    
