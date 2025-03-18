from datetime import datetime
import os, requests, subprocess, asyncio, globals, json, aiohttp
USERNAME = "rjwilder1"
REPO = "Whale_Arbs"
BRANCH = "main" 

FILES = [
    "betmgm.py",
    "caesars.py",
    "classes.py",
    "draftkings.py",
    "fanduel.py",
    "globals.py",
    "main.py",
    "rivers.py"
]

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))

async def sendmsg(msg = "", title="Successfully Updated", color=65280, url="", image_path=""):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"}
    try:
        payload = json.dumps({
        "embeds": [{
            "type": "rich",
            "title": title,
            "description": msg,
            "color": color,
            "url": url,
            "fields": [{
                "name": url,
                "value": datetime.now().strftime("%H:%M:%S"),
                "inline": True
            }],
        }],
        "username": f"Whale Arbs Updater",
        "avatar_url": "https://play-lh.googleusercontent.com/CPjzDLTfVr4if1FanT1XvSBeF_enE9K6qlSJeXWS7TZIHUeDNmEV3H0IFg6Miq7JZg"
    })
    
        data = aiohttp.FormData()
        if image_path and os.path.exists(image_path):
            data.add_field('file', open(image_path, 'rb'), filename=os.path.basename(image_path), content_type='application/octet-stream')
        data.add_field('payload_json', payload, content_type='application/json')
        async with aiohttp.ClientSession() as client:
            await client.post(globals.webhook, data=data, headers=headers)
    except Exception as e:
        globals.Log(f"Error in sendmsg: {e}")

def download_file(file_name):
    url = f"https://raw.githubusercontent.com/{USERNAME}/{REPO}/{BRANCH}/{file_name}"
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {file_name}")
    else:
        print(f"Failed to download: {file_name} (Status Code: {response.status_code})")

for file in FILES:
    download_file(file)

globals.Log("All files downloaded successfully!")
asyncio.run(sendmsg("All files downloaded successfully! Restarting Whale Arbs."))
command = f'start cmd.exe /k python main.py'
subprocess.Popen(command, shell=True)
exit()
