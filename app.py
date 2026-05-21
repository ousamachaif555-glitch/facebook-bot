from flask import Flask, request
import requests
import os
import json
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic()

PAGE_TOKEN = os.environ.get("PAGE_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mybot123")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

conversation_history = {}

def get_conversation(sender_id):
    if sender_id not in conversation_history:
        conversation_history[sender_id] = []
    return conversation_history[sender_id]

@app.route('/webhook', methods=['GET'])
def verify():
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if verify_token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return challenge
    return "Unauthorized", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                if "message" not in messaging:
                    continue
                
                sender_id = messaging["sender"]["id"]
                message_text = messaging.get("message", {}).get("text", "")
                
                if message_text:
                    print(f"📨 Message from {sender_id}: {message_text}")
                    
                    # Get AI response
                    response_text = get_ai_response(sender_id, message_text)
                    
                    # Send message
                    send_message(sender_id, response_text)
    
    return "ok", 200

def get_ai_response(sender_id, user_message):
    try:
        conversation = get_conversation(sender_id)
        conversation.append({
            "role": "user",
            "content": user_message
        })
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system="أنت مساعد ذكي ودود يتحدث باللغة العربية. أرد بشكل مختصر (أقل من 300 حرف).",
            messages=conversation
        )
        
        ai_message = response.content[0].text
        print(f"✅ Response: {ai_message[:100]}")
        
        conversation.append({
            "role": "assistant",
            "content": ai_message
        })
        
        # Keep only last 20 messages
        if len(conversation) > 20:
            conversation_history[sender_id] = conversation[-20:]
        
        return ai_message
        
    except Exception as e:
        print(f"❌ Error from Claude: {e}")
        return "معذراً، حدث خطأ. حاول مجددا."

def send_message(recipient_id, message_text):
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        params = {"access_token": PAGE_TOKEN}
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Message sent to {recipient_id}")
        else:
            print(f"❌ Failed to send: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
