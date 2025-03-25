from datetime import datetime
import json, configparser, math, re, aiohttp, classes, time

config = configparser.ConfigParser()
config.read('config.ini')
TotalStake = int(config.get('DEFAULT', 'Stake'))
discordid = config.get('DEFAULT', 'DiscordChannelID')
discordtoken = config.get('DEFAULT', 'DiscordToken')
webhook = config.get('DEFAULT', 'WebhookURL')
instance = config.get('DEFAULT', 'Instance')
BetMGM = config.getboolean('DEFAULT', 'BetMGM')
DraftKings = config.getboolean('DEFAULT', 'DraftKings')
Rivers = config.getboolean('DEFAULT', 'Rivers')
cashoutloss = 0
NeedToClearBets = False
Version = config.get('DEFAULT', 'Version')

async def checkmsgs():
    try:
        url = f"https://discordapp.com/api/v6/channels/{discordid}/messages"
        authorization = discordtoken
        headers = {"Authorization": authorization}
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as client:
            async with client.get(url, headers=headers) as response:
                jsonResponse = await response.text()
                messages = json.loads(jsonResponse)
                return messages
    except Exception as e:
        globals.Log(f"Error in checkmsgs: {e}")
        return []
        
async def get_cookies(page):
    cookies = await page.context.cookies()
    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    return cookie_string

def payout(odds, wager):
    payout = wager * odds 

    return math.floor(payout * 100) / 100

def fractional_to_decimal(fractional_odds):
    num, denom = map(int, fractional_odds.split('/'))
    return round(num / denom + 1, 2)

def Log(msg):
    try:
        with open("log.txt", 'a', encoding='utf-8') as writer:
            dt = time.strftime("%m-%d-%Y [%H:%M:%S]")
            writer.write(f"{dt} - {msg}\n")
            print(f"[{dt}] | {msg}")
    except Exception as e:
        print(f"Error in Log: {e}")

def gettime():
    now = datetime.now()
    currenttime = now.time()
    return currenttime

async def captureimg(page):
    try:
        imgpath = f"images\\img{datetime.now().strftime('%H-%M-%S')}.png"
        await page.screenshot(path=imgpath)
        return imgpath
    except Exception as e:
        globals.Log(f"Error in captureimg: {e}")
        return ""
    
def add_new_arbitrage(new_arbitrage: classes.Arbitrage):
    with open("history.txt", 'a') as file:
        bets_str = json.dumps([bet.model_dump() for bet in new_arbitrage.bets])
        line = (
            f"bet_id='{new_arbitrage.bet_id}' "
            f"is_live='{str(new_arbitrage.is_live).lower()}' "
            f"in_game_status='{new_arbitrage.in_game_status or ''}' "
            f"percentage='{new_arbitrage.percentage}' "
            f"bets='{bets_str}'\n"
        )
        file.write(line)

def getstakes(odds):
    total_stake = TotalStake
    decimal_odds = []
    for odd in odds:
        if odd > 0:
            decimal_odds.append((odd / 100) + 1)
        else:
            decimal_odds.append((100 / abs(odd)) + 1)
    implied_probs = [1 / odd for odd in decimal_odds]
    arb_percent = sum(implied_probs)

    if arb_percent >= 1:
        return {"error": "No arbitrage opportunity"}
    stakes = [(total_stake * imp_prob) / arb_percent for imp_prob in implied_probs]
    #stakes = [0.5, 0.5]#REMOVE
    profit = (total_stake / arb_percent) - total_stake
    roi = (profit / total_stake) * 100
    return {
        "stakes": [round(stake, 2) for stake in stakes],
        "profit": round(profit, 2),
        "roi": round(roi, 2)
    }

def getarbtext(arb):

    return f"""**Bet ID:** {arb.bet_id}
**Live:** {arb.is_live}
**Game Status:** {arb.in_game_status}
**Profit Precentage:** ${round(float(int(TotalStake) / (float(arb.percentage) / 100)), 2)} ({arb.percentage}%)\n
**-----------[Bet 1]-----------**
**Bet:** {arb.bets[0].bet_name}
**Sportsbook:** {arb.bets[0].sportsbooks[0]}
**Odds:** {arb.bets[0].price}
**URL:** {arb.bets[0].desktop_url}\n
**-----------[Bet 2]-----------**
**Bet:** {arb.bets[1].bet_name}
**Sportsbook:** {arb.bets[1].sportsbooks[0]}
**Odds:** {arb.bets[1].price}
**URL:** {arb.bets[1].desktop_url}"""

def load_existing_bet_ids():
    existing_ids = set()
    try:
        with open("history.txt", "r") as file:
            for line in file:
                match = re.search(r"bet_id='(.*?)'", line)
                if match:
                    existing_ids.add(match.group(1))
    except FileNotFoundError:
        globals.Log("history.txt not found. Starting fresh.")
    return existing_ids







# async def toggleruntime(self):
#     currtime = self.gettime()
#     if (time(9, 0) <= currtime < time(17, 0)) or (time(17, 0) <= currtime < time(23, 30)):#if (time(9, 0) <= currtime < time(12, 0)) or (time(17, 0) <= currtime < time(23, 30)):
#         if self.timetorun == False:
#             await self.sendmsg2(msg = "", title = "Starting Whale Arbs...")
#             #await self.oddsjambrowserpage.click("[data-testid='betting-tools-refresh']")
#         self.timetorun = True
#     else:
#         if self.timetorun == True:
#             await self.sendmsg2(msg = "",title = "Pausing whale arbs...")
#         self.timetorun = False
