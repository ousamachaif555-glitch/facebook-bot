from flask import Flask, request
import requests
import os

app = Flask(__name__)

PAGE_TOKEN = os.environ.get("PAGE_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge')
    return "خطأ", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    for entry in data['entry']:
        for msg in entry['messaging']:
            sender = msg['sender']['id']
            if 'message' in msg:
                text = msg['message'].get('text', '')
                if text:
                    reply = get_ai_reply(text)
                    send_message(sender, reply)
    return "OK"

def get_ai_reply(text):
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 500,
        "system": "أنت بوت ذكي واجتماعي اسمك هيبة. تتحدث بأسلوب طبيعي وممتع. لا تذكر أنك ذكاء اصطناعي.",
        "messages": [{"role": "user", "content": text}]
    }
    res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
    return res.json()['content'][0]['text']

def send_message(recipient_id, text):
    requests.post(
        "https://graph.facebook.com/v18.0/me/messages",
        params={"access_token": PAGE_TOKEN},
        json={"recipient": {"id": recipient_id}, "message": {"text": text}}
    )

if __name__ == '__main__':
    app.run(port=5000)
