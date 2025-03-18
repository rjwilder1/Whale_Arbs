#UPDATED
import asyncio, os, betmgm, json, classes, re, aiohttp, caesars, draftkings, rivers, globals
import subprocess
from datetime import datetime
from patchright.async_api import async_playwright

class Main:
    def __init__(self): 
        self.oddsjambrowser = None
        self.oddsjambrowserpage = None
        self.betmgmbrowser = None
        self.fanduelbrowser = None
        self.draftkingsbrowser = None
        self.riversbrowser = None
        self.caesarsbrowser = None
        self.placingbet = False
        self.timetorun = True
        self.refreshtime = False
        self.refreshrivers = False
        self.last_run_minute = None
        
        self.TotalStake = globals.TotalStake
        self.discordid = globals.discordid
        self.discordtoken = globals.discordtoken
        self.webhook = globals.webhook
        self.instance = globals.instance
        self.BetMGM = globals.BetMGM
        self.DraftKings = globals.DraftKings
        self.Rivers = globals.Rivers
        #self.Caesars = globals.Caesars

        self.newarbs = []
        self.oldbets = []
        self.unavailablearbs = []
        self.betsplacedct = 0
        self.cashoutsct = 0
        self.failed = 0
        self.attempted = 0
        self.lastcommand = ""
        self.allarbs = globals.load_existing_bet_ids()

    async def sendarb(self, arb: classes.Arbitrage, extra = "", firsttext = ""):
        if extra != "": extra = f"\n\n{extra}"
        betstosend = globals.getarbtext(arb)#, bet1=arb.bets[0].price, bet2=arb.bets[1].price)
        await self.sendmsg(f"{firsttext} {betstosend}{extra}", title="Found Arbitrage", color=13421568)

    async def arbupdate(self, response):
        currtime = datetime.now().strftime("%H:%M")
        lastnumb = int(currtime[-1])

        if (lastnumb == 0 or lastnumb == 5) and self.last_run_minute != currtime:
            self.last_run_minute = currtime
            try:
                if not self.refreshtime:
                    self.refreshtime = True
                    await self.draftkingsbrowser.goto("https://sportsbook.draftkings.com/mybets")
                    await self.riversbrowser.goto("https://il.betrivers.com/?page=my-account")
                else:
                    self.refreshtime = False
                    await self.draftkingsbrowser.goto("https://sportsbook.draftkings.com/auth")
                    await self.riversbrowser.goto("https://il.betrivers.com/?page=sportsbook#bethistory/")
            except Exception as e:
                globals.Log(f"Error refreshing DraftKings and Rivers: {e}")
            #await self.sendmsg(title="Reloaded Pages")
            await asyncio.sleep(5)

        arbon = 0
        self.allarbs = globals.load_existing_bet_ids()
        self.newarbs.clear()
        if response.request.method == "POST" and response.url == "https://oddsjam.com/api/backend/arbitrage" and self.timetorun == True:
            #await self.runtest()
            #input("Done Testing")
            if 1 + 1 == 2:#try:
                if self.placingbet == False:
                    self.newarbs.clear()
                    body = await response.json()
                    for arb_data in body.get("data", []):
                        arb = classes.Arbitrage(
                            bet_id=arb_data["bet_id"],
                            is_live=arb_data["is_live"],
                            in_game_status=arb_data.get("in_game_status"),
                            percentage=arb_data["percentage"],
                            bets=[
                                classes.Bet(
                                    bet_name=bet["bet_name"],
                                    price=bet["price"],
                                    sportsbooks=bet["sportsbooks"],
                                    no_vig_price=bet.get("no_vig_price"),
                                    edge_percent=bet.get("edge_percent"),
                                    order=bet["order"],
                                    bet_points=bet.get("bet_points"),
                                    desktop_url=next(
                                        (
                                            details["urls"]["desktop"]["url"]
                                            for sportsbook, details in (bet.get("deep_link_map") or {}).items()
                                            if isinstance(details, dict) and "urls" in details and "desktop" in details["urls"]
                                        ),
                                        None
                                    )
                                )
                                for bet in arb_data.get("bets", [])
                            ]
                        )
                        
                        if arb.bet_id not in self.unavailablearbs:
                            found = False
                            for i in arb.bets:
                                if i.desktop_url == None: 
                                    found = True

                            if not found: 
                                self.newarbs.append(arb)
                                globals.add_new_arbitrage(arb)
                    #try:
                    
                    for arb in reversed(self.newarbs):
                        try:
                            if self.newarbs:
                                arbon += 1
                                #if arbon >= 5: break
                                totalarbs = len(self.newarbs)
                                arbct = f"{arbon}/{totalarbs} | {datetime.now().strftime('%H:%M:%S')} "
                                if self.placingbet == False and arb:
                                    self.placingbet = True
                                    tasks = []
                                    betmgm_bet = None
                                    fanduel_bet = None
                                    rivers_bet = None
                                    draftkings_bet = None

                                    for bet in arb.bets:
                                        if "BetMGM" in bet.sportsbooks and globals.BetMGM == True:
                                            betmgm_bet = bet
                                        if "FanDuel" in bet.sportsbooks:
                                            fanduel_bet = bet
                                        if "DraftKings" in bet.sportsbooks and globals.DraftKings == True:
                                            draftkings_bet = bet  
                                        if "BetRivers" in bet.sportsbooks and globals.Rivers == True:
                                            rivers_bet = bet
                                    self.attempted += 1

                                    if rivers_bet and draftkings_bet:
                                        globals.Log(f"{arbct} | Found Rivers and DraftKings Arb...")
                                        rivers_task = rivers.getoddsrequest(rivers_bet.desktop_url)
                                        draftkings_task = draftkings.getoddsrequest(draftkings_bet.desktop_url)
                                        tasks = []
                                        rivers_result, draftkings_result = await asyncio.gather(rivers_task, draftkings_task)
                                        globals.Log(f"Rivers Result: {rivers_result}")
                                        globals.Log(f"DraftKings Result: {draftkings_result}")
                                        rivers_odds, draftkings_odds = None, None
                                        rivers_arbs_odds = rivers_bet.price
                                        draftkings_arbs_odds = draftkings_bet.price
                                        try:
                                            if rivers_result['american']: rivers_odds = rivers_result['american']
                                        except: pass
                                        try:
                                            if draftkings_result['american']: draftkings_odds = draftkings_result['american']
                                        except: pass
                                        await self.sendarb(arb, extra = f"**Live Rivers Odds:** {rivers_odds}\n**Live DraftKings Odds:** {draftkings_odds}", firsttext=f"[{arbct}]")

                                        if rivers_result == None or draftkings_result == None:
                                            self.unavailablearbs.append(arb.bet_id)
                                            self.placingbet = False
                                            continue
                                            #await self.sendmsg(f"[{arbct}] One or both bets had an error. Not placing any bets.\n**Rivers Odds:** {rivers_odds}\n**DraftKings Odds:** {draftkings_odds}", title="Unknown Error", color=16711680)

                                        if rivers_result == "Unavailable" or draftkings_result == "Unavailable":
                                            self.unavailablearbs.append(arb.bet_id)
                                            if rivers_result == "Unavailable": rivers_odds = "Unavailable"
                                            if draftkings_result == "Unavailable": draftkings_odds = "Unavailable"
                                            rivers_result, draftkings_result = None, None
                                            self.placingbet = False
                                            continue
                                        
                                        betstosend = f"[{arbct}] {globals.getarbtext(arb)}"
                                        if rivers_result and draftkings_result and rivers_odds != "Unavailable" and draftkings_odds != "Unavailable":
                                            if int(rivers_arbs_odds) == int(rivers_odds) and int(draftkings_arbs_odds) == int(draftkings_odds):
                                                globals.Log("Verified odds for Rivers and DraftKings Arb. Attempting to place bets...")
                                                await self.sendmsg2(f"[{arbct}] **Live Rivers Odds:** {rivers_odds}\n**Live DraftKings Odds:** {draftkings_odds}**\n\n{betstosend}", title="Verified Matchings Odds - Adding To Slip", color=16777113)
                                                if 1 + 1 == 2:
                                                    globals.NeedToClearBets = True
                                                    stakes = globals.getstakes([rivers_bet.price, draftkings_bet.price])
                                                    rivers_stake = stakes["stakes"][0]
                                                    draftkings_stake = stakes["stakes"][1]
                                                    rivers_add = rivers.addtoslip(self.riversbrowser, rivers_bet, rivers_stake)
                                                    draftkings_add = draftkings.addtoslip(self.draftkingsbrowser, draftkings_bet, draftkings_stake)
                                                    rivers_add_result, draftkings_add_result = await asyncio.gather(rivers_add, draftkings_add)
                                                    if rivers_add_result != False and draftkings_add_result != False:

                                                        rivers_task = rivers.getoddsrequest(rivers_bet.desktop_url)
                                                        draftkings_task = draftkings.getoddsrequest(draftkings_bet.desktop_url)
                                                        rivers_result, draftkings_result = await asyncio.gather(rivers_task, draftkings_task)
                                                        globals.Log(f"Rivers Result 2: {rivers_result}")
                                                        globals.Log(f"DraftKings Result 2: {draftkings_result}")
                                                        rivers_odds, draftkings_odds = None, None
                                                        rivers_arbs_odds = rivers_bet.price
                                                        draftkings_arbs_odds = draftkings_bet.price
                                                        try:
                                                            if rivers_result['american']: rivers_odds = rivers_result['american']
                                                        except: pass
                                                        try:
                                                            if draftkings_result['american']: draftkings_odds = draftkings_result['american']
                                                        except: pass

                                                        if rivers_result == None or draftkings_result == None:
                                                            self.unavailablearbs.append(arb.bet_id)
                                                            await self.sendmsg2(f"[{arbct}] One or both bets had an error while attempting to place the bet. Not placing any bets.\n**Rivers Odds:** {rivers_odds}\n**DraftKings Odds:** {draftkings_odds}", title="Unknown Error", color=16711680)

                                                        if rivers_result == "Unavailable" or draftkings_result == "Unavailable":
                                                            self.unavailablearbs.append(arb.bet_id)
                                                            if rivers_result == "Unavailable": rivers_odds = "Unavailable"
                                                            if draftkings_result == "Unavailable": draftkings_odds = "Unavailable"
                                                            await self.sendmsg2(f"[{arbct}] One or both bets became unavailable while placing the bet. Not placing any bets.\n**Rivers Odds:** {rivers_odds}\n**DraftKings Odds:** {draftkings_odds}", title="Bet Unavailable", color=16711680)
                                                            rivers_result, draftkings_result = None, None
                                                        
                                                        if rivers_result and draftkings_result and rivers_odds != "Unavailable" and draftkings_odds != "Unavailable":
                                                            if int(rivers_arbs_odds) == int(rivers_odds) and int(draftkings_arbs_odds) == int(draftkings_odds):
                                                                rivers_task_placebet = rivers.placebet(self.riversbrowser, rivers_stake)
                                                                draftkings_task_placebet = draftkings.placebet(self.draftkingsbrowser, draftkings_stake)
                                                                rivers_result_placebet, draftkings_result_placebet = await asyncio.gather(rivers_task_placebet, draftkings_task_placebet)
                                                                if rivers_result_placebet == True and draftkings_result_placebet == True:
                                                                    self.betsplacedct += 1
                                                                    DKBalance = await draftkings.checkbalance(self.draftkingsbrowser)
                                                                    riversBalance = await rivers.checkbalance(self.riversbrowser)
                                                                    
                                                                    globals.Log(f"[{arbct}] **Total Bets Placed:** {self.betsplacedct}\n**Bet placed successfully!**\n**DraftKings Balance:** ${DKBalance}\n**Rivers Balance:** ${riversBalance}\n**Profit:** ${stakes['profit']} ({stakes['roi']}% ROI)\n**Total Stake:** ${str(self.TotalStake)}\n{betstosend}")
                                                                    await self.sendmsg2(f"[{arbct}] **Total Bets Placed:** {self.betsplacedct}\n**Bet placed successfully!**\n**DraftKings Balance:** ${DKBalance}\n**Rivers Balance:** ${riversBalance}\n**Profit:** ${stakes['profit']} ({stakes['roi']}% ROI)\n**Total Stake:** ${str(self.TotalStake)}\n{betstosend}", color=65280)
                                                                    with open("placedbets.txt", "a") as file:
                                                                        file.write(f"[{datetime.now().strftime('%H:%M:%S')}] Profit: ${stakes['profit']} ({stakes['roi']}% ROI) (${self.TotalStake}) | Bet ID: {arb.bet_id}\n")
                                                                    if DKBalance < int(globals.TotalStake) or riversBalance < int(globals.TotalStake):
                                                                        await self.sendmsg2("Pausing whale arbs - Balance is too low! Please use command /reload then /start once funds have settled.", title="Balance Below $50", color=16711680)
                                                                        globals.Log("Pausing whale arbs - Balance is too low! Please use command /reload then /start once funds have settled.")
                                                                        await asyncio.sleep(5)
                                                                        self.timetorun = False
                                                                    break
                                                                else:#CashoutHere
                                                                    #break
                                                                    betstosend = globals.getarbtext(arb)
                                                                    globals.Log(f"Failed to place bet: {betstosend}")
                                                                    self.failed += 1
                                                                    if rivers_result_placebet == True and draftkings_result_placebet == False:
                                                                        await self.sendmsg2(f"[{arbct}] {betstosend}", title="DraftKings Failed To Place Bet, Cashing Out Rivers...", color=16711680, image_path=await globals.captureimg(self.draftkingsbrowser))
                                                                        await rivers.cashoutlast(self.riversbrowser)
                                                                    elif rivers_result_placebet == False and draftkings_result_placebet == True:
                                                                        await self.sendmsg2(f"[{arbct}] {betstosend}", title="Rivers Failed To Place Bet, Cashing Out DraftKings...", color=16711680, image_path=await globals.captureimg(self.riversbrowser))
                                                                        await draftkings.cashoutlast(self.draftkingsbrowser)
                                                                    else:
                                                                        await self.sendmsg2(f"[{arbct}] {betstosend}", title="Both DraftKings and Rivers Failed To Place Bet...", color=16711680, image_path=await globals.captureimg(self.riversbrowser))
                                                                        await self.sendmsg2(image_path=await globals.captureimg(self.draftkingsbrowser))
                                                            else:
                                                                betstosend = globals.getarbtext(arb)
                                                                globals.Log(f"Failed to place bet: {betstosend}")
                                                                await self.sendmsg2(f"[{arbct}] {betstosend}\n**Rivers Odds:** {rivers_odds}\n**DraftKings Odds:** {draftkings_odds}", title="Failed Due To Second Verification Odds Change", color=16711680)
                                                                self.failed += 1
                                                        else:
                                                            betstosend = globals.getarbtext(arb)
                                                            globals.Log(f"Failed to place bet: {betstosend}")
                                                            await self.sendmsg2(f"[{arbct}] {betstosend}", title="Failed Due To Bet Unavailable on 2nd Check", color=16711680)
                                                            self.failed += 1
                                                    else:
                                                        imagetosend = None
                                                        imagetosend2 = None
                                                        if rivers_add_result == False and draftkings_add_result == False:
                                                            imagetosend = await globals.captureimg(self.riversbrowser)
                                                            imagetosend2 = await globals.captureimg(self.draftkingsbrowser)
                                                        elif rivers_add_result == False:
                                                            imagetosend = await globals.captureimg(self.riversbrowser)
                                                        elif draftkings_add_result == False:
                                                            imagetosend = await globals.captureimg(self.draftkingsbrowser)
                                                        betstosend = globals.getarbtext(arb)
                                                        globals.Log(f"Failed to place bet: {betstosend}")
                                                        await self.sendmsg2(f"[{arbct}] {betstosend}", title="Failed Due To Bet Slip Not Adding", color=16711680, image_path=imagetosend)
                                                        if imagetosend2: await self.sendmsg2(image_path=imagetosend2)
                                                        self.failed += 1    

                            self.placingbet = False

                        except Exception as e:
                            globals.Log(f"Error placing bet!: {e}")
                    await asyncio.sleep(5)
                    if globals.NeedToClearBets == True:
                        globals.NeedToClearBets = False
                        try:
                            clear1 = draftkings.clearbets(self.draftkingsbrowser)
                            clear2 = rivers.clearbets(self.riversbrowser)
                            await asyncio.gather(clear1, clear2)
                        except Exception as e:
                            globals.Log(f"Failed to clear bets: {e}")

                    self.placingbet = False
                    reloaded = False
                    try:
                        await self.oddsjambrowserpage.click("[data-testid='betting-tools-refresh']")
                        reloaded = True
                    except Exception as e:
                        globals.Log(f"Error reloading oddsjam: {e}")
                    if reloaded == False:
                        await self.oddsjambrowserpage.reload()
                        refreshbutton = await self.oddsjambrowserpage.query_selector("[data-testid='betting-tools-refresh']")
                        await refreshbutton.click()

            # except Exception as e:
            #     globals.Log(f"Failed to parse JSON response: {e}")
            #     globals.Log("Error " + str(arbdata))

    async def sendmsg(self, msg = "", title="New Arbitrage", color=65280, url="", image_path=""):
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
            "username": f"[{self.instance}] Whale Arb",
            "avatar_url": "https://play-lh.googleusercontent.com/CPjzDLTfVr4if1FanT1XvSBeF_enE9K6qlSJeXWS7TZIHUeDNmEV3H0IFg6Miq7JZg"
        })
        
            data = aiohttp.FormData()
            if image_path and os.path.exists(image_path):
                data.add_field('file', open(image_path, 'rb'), filename=os.path.basename(image_path), content_type='application/octet-stream')
            data.add_field('payload_json', payload, content_type='application/json')
            async with aiohttp.ClientSession() as client:
                await client.post("https://discord.com/api/webhooks/1329543168919863406/JVXYp271RQXI6u8i_NkWvKOOSMZ-nmc8ZCQ1BuDYvRTYpdHBUTHelZwWNUfbwT7yOgOy", data=data, headers=headers)
                #await client.post("https://discordapp.com/api/webhooks/1337252768544718898/HHlhShp20q74PtOjxDiNEZnxbosjd5eaT_yYO9ppmMv8Gbcn87bfTrHrob1mE7S2EaAg", data=data, headers=headers)

        except Exception as e:
            globals.Log(f"Error in sendmsg: {e}")

    async def sendmsg2(self, msg = "", title="Successful Arb Placement", color=65280, url="", image_path=""):
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
            "username": f"[{self.instance}] Whale Arb",
            "avatar_url": "https://play-lh.googleusercontent.com/CPjzDLTfVr4if1FanT1XvSBeF_enE9K6qlSJeXWS7TZIHUeDNmEV3H0IFg6Miq7JZg"
        })
        
            data = aiohttp.FormData()
            if image_path and os.path.exists(image_path):
                data.add_field('file', open(image_path, 'rb'), filename=os.path.basename(image_path), content_type='application/octet-stream')
            data.add_field('payload_json', payload, content_type='application/json')
            async with aiohttp.ClientSession() as client:
                await client.post(self.webhook, data=data, headers=headers)
                #await client.post("https://discordapp.com/api/webhooks/1337252768544718898/HHlhShp20q74PtOjxDiNEZnxbosjd5eaT_yYO9ppmMv8Gbcn87bfTrHrob1mE7S2EaAg", data=data, headers=headers)

        except Exception as e:
            globals.Log(f"Error in sendmsg: {e}")

    async def start(self):
        # odds = await rivers.getoddsrequest("https://il.betrivers.com/?page=sportsbook#event/1021043951?coupon=single|3663249332|")
        # input(odds)
        # input("Done...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pattern = re.compile(
            r"bet_id='(?P<bet_id>.*?)' is_live='(?P<is_live>true|false)' "
            r"in_game_status='(?P<in_game_status>.*?)' percentage='(?P<percentage>.*?)' "
            r"bets='(?P<bets>.*?)'"
        )
        with open("placedbets.txt", 'r') as file:
            for line in file:
                self.betsplacedct += 1
        with open("cashouts.txt", 'r') as file:
            for line in file:
                self.cashoutsct += 1
        with open("history.txt", 'r') as file:
            for line in file:
                match = pattern.search(line.strip())
                if match:
                    bets_data = match.group('bets')
                    try:
                        bets = [classes.Bet(**bet_dict) for bet_dict in json.loads(bets_data)]
                    except json.JSONDecodeError as e:
                        globals.Log(f"Error decoding JSON bets: {e}")
                        continue
                    except Exception as e:
                        globals.Log(f"Unexpected error parsing bets: {e}")
                        continue

                    arbitrage = classes.Arbitrage(
                        bet_id=match.group('bet_id'),
                        is_live=match.group('is_live').lower() == 'true',
                        in_game_status=match.group('in_game_status') or None,
                        percentage=float(match.group('percentage')),
                        bets=bets,
                    )
                    self.newarbs.append(arbitrage)

        user_data_dir = os.path.join(script_dir, "browserdata\\oddsjam")
        p = await async_playwright().start()
        p1 = "142.173.128.7:9087:pumywuYUoA:HgWfqp1rVr".split(":")
        proxy = {
            "server": f'http://{p1[0]}:{p1[1]}',
            "username": p1[2],
            "password": p1[3]
        }
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            no_viewport=True,
            channel="chrome",
            #proxy=proxy
        )
        self.oddsjambrowser = browser

        page = await browser.new_page()
        self.oddsjambrowserpage = page
        await page.goto("https://oddsjam.com/betting-tools/arbitrage?tab=live")
        #await page.goto("https://oddsjam.com/betting-tools/arbitrage?tab=preMatch")
        #self.betmgmbrowser = await betmgm.createbrowser()
        #self.fanduelbrowserbrowser = await fanduel.createbrowser()
        self.riversbrowser = await rivers.createbrowser()
        self.draftkingsbrowser = await draftkings.createbrowser()
        #self.caesarsbrowser = await caesars.createbrowser()
        await asyncio.sleep(2)
        await rivers.checklogin(self.riversbrowser)
        page.on("response", self.arbupdate)
        globals.Log("Loaded All")
        #await asyncio.Event().wait()
        while True:
            #await self.toggleruntime()
            await self.checkdiscord()
            await asyncio.sleep(1)



    

    async def checkdiscord(self):
        try:
            msgs = await globals.checkmsgs()
            msgcontent = msgs[0]['content']
            msgtimestamp = msgs[0]['timestamp']
            if msgtimestamp != self.lastcommand:
                self.lastcommand = msgtimestamp
                if "/stats" in msgcontent:
                    DKBalance, MGMBalance, RiversBalance = 0, 0, 0
                    try:
                        DKBalance = await draftkings.checkbalance(self.draftkingsbrowser)
                    except Exception as e:
                        pass
                    try:
                        MGMBalance = await betmgm.checkbalance(self.betmgmbrowser)
                    except Exception as e:
                        pass
                    try:
                        RiversBalance = await rivers.checkbalance(self.riversbrowser)
                    except Exception as e:
                        pass

                    TotalBalance = round(float(DKBalance + MGMBalance + RiversBalance), 2)
                    #dkbets = await draftkings.checkbets(self.draftkingsbrowser)
                    await self.sendmsg2(title = "Whale Arb Stats", msg = f"**Total Bets Placed:** {self.betsplacedct}\n**Total Cashouts:** {self.cashoutsct}\n**Failed:** {self.failed}\n**Attemped Bets:** {self.attempted}\n**DraftKings Balance:** ${DKBalance}\n**BetMGM Balance:** ${MGMBalance}\n**Rivers Balance:** ${RiversBalance}\n**Total Balance:** ${TotalBalance}\n**Active:** {self.timetorun}", color = 65280)
                if "/pages" in msgcontent:
                    await self.sendmsg2(title="Oddsjam Browser", msg="", image_path=await globals.captureimg(self.oddsjambrowserpage))
                    await self.sendmsg2(title="DraftKings Browser",msg="", image_path=await globals.captureimg(self.draftkingsbrowser))
                    await self.sendmsg2(title="Rivers Browser",msg="", image_path=await globals.captureimg(self.riversbrowser))
                    await self.sendmsg2(title="BetMGM Browser",msg="", image_path=await globals.captureimg(self.betmgmbrowser))
                if "/stop" in msgcontent:
                    await self.sendmsg2(title = "Shutting Down!", msg = "Shutting down whale arbs...", color = 16711680)
                    await asyncio.sleep(5)
                    exit()
                if "/resume" in msgcontent:
                    if self.timetorun == False:
                        await self.sendmsg2(title = "Starting whale arbs...", msg = "", color = 65280)
                        self.timetorun =True
                        reloaded = False
                        try:
                            await self.oddsjambrowserpage.click("[data-testid='betting-tools-refresh']")
                            reloaded = True
                        except Exception as e:
                            globals.Log(f"Error reloading oddsjam: {e}")
                        if reloaded == False:
                            await self.oddsjambrowserpage.reload()
                            refreshbutton = await self.oddsjambrowserpage.query_selector("[data-testid='betting-tools-refresh']")
                            await refreshbutton.click()
                    else:
                        await self.sendmsg2(title = "Whale arbs already running!", msg = "", color = 16711680)
                if "/update" in msgcontent:
                    await self.sendmsg2("Upating files to latest version...", title="Updating Files", color=65280)
                    command = f'start cmd.exe /k python update.py'
                    subprocess.Popen(command, shell=True)
                    exit()

                if "/pause" in msgcontent:
                    if self.timetorun == True:
                        await self.sendmsg2(title = "Pausing whale arbs...", msg = "", color = 65280)
                        self.timetorun = False
                    else:
                        await self.sendmsg2(title = "Whale arbs already paused!", msg = "", color = 16711680)
                if "/reload" in msgcontent:
                    await self.sendmsg2(title = "Reloading all browsers...", msg = "", color = 65280)
                    self.placingbet = True
                    try:
                        reloadtasks = []
                        reloadtasks.append(self.riversbrowser.reload())
                        reloadtasks.append(self.draftkingsbrowser.reload())
                        #reloadtasks.append(self.betmgmbrowser.reload())
                        await asyncio.gather(*reloadtasks, return_exceptions=True)
                    except Exception as e:
                        globals.Log(f"Failed to reload browsers: {e}")
                    try:
                        checklogintasks = []
                        #checklogintasks.append(betmgm.checklogin(self.betmgmbrowser))
                        checklogintasks.append(rivers.checklogin(self.riversbrowser))
                        checklogintasks.append(draftkings.checklogin(self.draftkingsbrowser))
                        await asyncio.gather(*checklogintasks, return_exceptions=True)
                    except Exception as e:
                        globals.Log(f"Failed to check logins: {e}")
                    try:
                        clearbetstasks = []
                        clearbetstasks.append(draftkings.clearbets(self.draftkingsbrowser))
                        #clearbetstasks.append(betmgm.clearbets(self.betmgmbrowser))
                        clearbetstasks.append(rivers.clearbets(self.riversbrowser))
                        await asyncio.gather(*clearbetstasks, return_exceptions=True)
                    except Exception as e:
                        globals.Log(f"Failed to clear bets: {e}")
                    await self.sendmsg2(title = "Sucessfully reloaded all browsers!", msg = "", color = 65280)
                    self.placingbet = False
            return None
        except Exception as e:
            globals.Log(f"Failed to check discord: {e}")

    def arbexists(self, bet_id):
        return bet_id in self.allarbs or any(arb.bet_id == bet_id for arb in self.newarbs)

    def arbexistsunavailable(self, bet_id):
        return bet_id in self.unavailablearbs
    
    async def runtest(self):
        bet = classes.Bet(
            bet_name="Test Bet",
            price=-140,
            sportsbooks=["DraftKings"],
            no_vig_price=160,
            edge_percent=5,
            order=1,
            bet_points="Test Bet Points",
            desktop_url="https://sportsbook.draftkings.com/event/31944048?outcomes=0HC79053399P2250_3"#0ML79039652_3
        )
        #p=await draftkings.getoddsrequest(url = bet.desktop_url, page=self.draftkingsbrowser)
        #input(p)
        a = await draftkings.placebetrequest(page = self.draftkingsbrowser, url=bet.desktop_url, bet=bet, stake=0.1)
        input(a)

if __name__ == "__main__":
    main = Main()
    asyncio.run(main.start())
