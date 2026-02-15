import requests
url = "https://api.meetingbaas.com/bots"

headers = {
    "Content-Type": "application/json",
    "x-meeting-baas-api-key": "51a9fe8967eab1e85e5e975ddaa10e536e7af03d67bac4cd00aff249bb413f07",
}

config = {
    "meeting_url": "https://meet.google.com/puo-neku-for",
    "bot_name": "AI Notetaker",
    "recording_mode": "speaker_view",
    "bot_image": "https://example.com/bot.jpg",
    "entry_message": "I am a good meeting bot :)",
    "reserved": False,
    "speech_to_text": {
        "provider": "Default"
    },
    "automatic_leave": {
        "waiting_room_timeout": 600  # 10 minutes in seconds
    }
}
response = requests.post(url, json=config, headers=headers)
print(response.json())