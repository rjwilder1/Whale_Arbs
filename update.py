import os, requests, subprocess, globals

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

def download_file(file_name):
    url = f"https://raw.githubusercontent.com/{USERNAME}/{REPO}/{BRANCH}/{file_name}"
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(SAVE_DIR, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
        globals.Log(f"Downloaded: {file_name}")
    else:
        globals.Log(f"Failed to download: {file_name} (Status Code: {response.status_code})")
globals.Log("Downloading files...")
for file in FILES:
    download_file(file)

globals.Log("All files downloaded successfully!")

command = f'start cmd.exe /k python main.py'
subprocess.Popen(command, shell=True)
exit()
