import http.client
import json

conn = http.client.HTTPSConnection("1ew9v9.api.infobip.com")
payload = json.dumps({
    "messages": [
        {
            "from": "447860088970",
            "to": "254716540107",
            "messageId": "0feb4fd9-e49f-4757-b2b3-e378ddf63c9e",
            "content": {
                "templateName": "test_whatsapp_template_en",
                "templateData": {
                    "body": {
                        "placeholders": ["Maurice"]
                    }
                },
                "language": "en"
            }
        }
    ]
})
headers = {
    'Authorization': 'App 6a7db667841d55dbce26f00b2df50efc-978ec5d6-fb0f-4c1f-b9b7-eac4733f403a',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
conn.request("POST", "/whatsapp/1/message/template", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))