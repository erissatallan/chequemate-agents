# chequemate-agents
Automations for chequemate.space

This repository hosts the smart tools that enhance user experience on chequemate.space (unpublished). Here is a brief description of these tools:

1. Match makers
These tools rely on player statistics—specifically elo rating, recent win streak, ECO profile, and prefered time settings—to match a player with another one depending on their present appetite for challenge. They rely on the chess.com and lichess.org APIs to retrieve this innformation. The aforementioned metrics are not provided by these APIs and are instead calculated within `chess.com_match_maker.py` and `lichess_match_maker.py`.

2. Chat moderator
This tool relies on Google's Perspective API to moderate chats between users. Perspective can intelligently determine whether a comment made by a user is harmful/ toxic by scoring it on a toxicity scale. Comments that potentially violate community guidelines are identified by checking whether the toxicity score is above a threshold of our choosing. If so, an agreeable alternative is suggested by using OpenAI API or XAI API to revise the intended text. This way, messaging between users in not halted but instead made safe.
```
test_data = {
    "username": "testuser",
    "message": "You're such an idiot, I hate you!"  # This should be flagged as toxic
}

response = requests.post(
    "http://127.0.0.1:3030/moderate", 
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print("Status Code:", response.status_code)
print("Response:", response.json())

-------------------Output-------------------
Status Code: 200
Response: {'flagged': True, 'suggestion': 'I must say, I find your actions quite unwise, and I have a strong dislike for you.', 'toxicity': 0.9563754}
```

#### Terms
ECO: Encyclopedia of Chess Openings
