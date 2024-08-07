from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
import random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import datetime
from googletrans import Translator
import nltk

nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['complaint_db']
complaints_collection = db['complaints']
feedback_collection = db['feedback']

complaint_categories = {
    "maintenance": ["broken", "repair", "leak", "fix", "electricity"],
    "cleanliness": ["dirty", "clean", "trash", "garbage"],
    "noise": ["loud", "noise", "noisy", "disturbance", "sound"],
    "Academics": ["grades", "assignments", "exams", "professors", "teachers", "classes", "class", "grades"],
    "Infrastructure": ["campus", "facilities", "maintenance", "buildings"],
    "Food": ["canteen", "mess", "food quality", "hygiene", "menu", "prices"],
    "Hostel": ["hostel", "mess food", "accommodation", "room", "hostel life", "warden"],
    "Safety": ["unsafe", "danger", "security", "harassment"],
    "plumbing": ['leak', 'pipe', 'plumbing', 'water', 'faucet'],
    "electrical": ['electric', 'light', 'power', 'outlet', 'circuit'],
    "HVAC": ['heating', 'cooling', 'ventilation', 'HVAC', 'thermostat'],
    "payment": ['payment', 'billing', 'charge'],
    "delivery": ['delivery', 'shipping', 'shipment'],
    "product quality": ['quality', 'defective', 'faulty'],
    "Others": ["general", "miscellaneous", "other"]
}

def classify_complaint(complaint_text):
    tokens = word_tokenize(complaint_text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    features = {}
    for category, keywords in complaint_categories.items():
        for keyword in keywords:
            if keyword in tokens:
                features[category] = features.get(category, 0) + 1
    return max(features, key=features.get) if features else "Others"

def translate_text(text, lang):
    try:
        translator = Translator()
        translation = translator.translate(text, dest=lang)
        return translation.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def greeting():
    current_time = datetime.datetime.now().time()
    if current_time < datetime.time(12, 0):
        return "Good morning! How can I help you?"
    elif current_time < datetime.time(17, 0):
        return "Good afternoon! How can I help you?"
    elif current_time < datetime.time(20, 0):
        return "Good evening! How can I help you?"
    else:
        return "Good night! How can I help you?"

def nl2br(value):
    return value.replace('\n', '<br>\n')

app.jinja_env.filters['nl2br'] = nl2br

def handle_chat(user_input):
    if user_input in ['quit', 'exit', 'not more', 'no', 'by', 'byy', 'bye']:
        return "redirect:index"
    
    elif any(greeting in user_input for greeting in ["hello", "hi", "hey", "hii"]):
        return greeting()
    
    elif user_input in ['complain', 'about complain', 'about complaint', 'complaint', 'register complain', 'register complaint', 'register my complaint']:
        return "redirect:complaint"
    
    elif "translate" in user_input:
        parts = user_input.split()
        if len(parts) >= 3:
            lang = parts[1]
            text = ' '.join(parts[2:])
            translated_text = translate_text(text, lang)
            return f"Translated text:\n{translated_text}"
        else:
            return "Usage: translate <language_code> <text>"
    
    else:
        return "I didn't understand that. Please try again!"

@app.route('/')
def home():
    return render_template('index.html', response="Hello! Welcome to the complaint resolution chatbot.")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['message'].lower()
    response = handle_chat(user_input)
    if response.startswith("redirect:"):
        if response == "redirect:index":
            return redirect(url_for('home'))
        return render_template(f'{response[9:]}.html')
    return render_template('index.html', response=response)

@app.route('/complaint', methods=['POST'])
def complaint():
    user_name = request.form['name']
    user_id = request.form['id']
    user_phone = request.form['phone']
    user_address = request.form['address']
    complaint_text = request.form['complaint']
    complaint_details = request.form['complaint_details']
    complaint_category = classify_complaint(complaint_text)

    complaint_data = {
        'name': user_name,
        'id': user_id,
        'phone': user_phone,
        'address': user_address,
        'complaint_text': complaint_text,
        'complaint_details': complaint_details,
        'category': complaint_category
    }

    complaints_collection.insert_one(complaint_data)

    response_message = (f"Your complaint has been categorized as '{complaint_category}' related problem.\n"
                        f"Thank you, {user_name}. Your complaint has been recorded.\n"
                        f"Thank you for helping our campus.")
    return render_template('complaint_response.html', response=response_message)

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    email = request.form['email']
    feedback_text = request.form['feedback']

    feedback_data = {
        'name': name,
        'email': email,
        'feedback_text': feedback_text
    }

    feedback_collection.insert_one(feedback_data)
    response = (f"Thank you for your feedback, {name}! I hope you will visit again. Bye...")

    return render_template('index.html', response=response)

if __name__ == '__main__':
    app.run(debug=True)
