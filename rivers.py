from datetime import datetime
import asyncio, os, classes, aiohttp, json, globals, re, certifi, ssl
from patchright.async_api import async_playwright, Page, ElementHandle

cashout = None
activebet: classes.Bet = None

async def getoddsrequest(url):
    try:
        match = re.search(r'\|(\d+)\|', url)
        eventid = 0
        if match:
            eventid = match.group(1)
        else:
            print("Failed to get eventid")
            await sendmsg(title = "Failed to get eventid", msg=f"Failed to get eventid...: {url}")
            return None
        
        querystring = {"lang":"en_US","market":"US-IL","id":eventid}

        api_url = "https://eu1.offering-api.kambicdn.com/offering/v2018/rsiusil/betoffer/outcome.json"
        data = None
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://il.betrivers.com",
            "priority": "u=1, i",
            "referer": "https://il.betrivers.com/",
            "sec-ch-ua": '""Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134""',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '""Windows""',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context)

        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(api_url, headers=headers, params=querystring, proxy="http://pumywuYUoA:HgWfqp1rVr@142.173.138.227:11857") as response:
                data = await response.text()
                if "No bet offers found" in data:
                    globals.Log(f"Failed to get Rivers odds...: {data}")
                    #await sendmsg(title = "Rivers Bet Unavailable", msg=f"Bet is unavailable.")
                    return "Unavailable"
                if response.status == 200:
                    data = await response.json()

                    matching_outcome = None
                    for bet_offer in data.get("betOffers", []):
                        for outcome in bet_offer.get("outcomes", []):
                            if str(outcome["id"]).strip() == str(eventid).strip():
                                matching_outcome = outcome
                                break
                        if matching_outcome:
                            break
                    if matching_outcome is None:
                        print(f"Failed to find matching outcome: {data}")
                        await sendmsg(title = "Failed to find matching outcome", msg=f"Failed to find matching outcome...: {data}")
                        return None

                    american_odds = matching_outcome["oddsAmerican"]
                    decimal_odds = globals.fractional_to_decimal(matching_outcome["oddsFractional"])
                    #await sendmsg(f"Odds: {american_odds}")
                    return {"american": american_odds, "decimal": decimal_odds}
                else:
                    globals.Log(f"Failed to get Rivers odds...: {data}")
                    await sendmsg(title = "Failed to get Rivers odds", msg=f"Failed to get Rivers odds...: {data}")
                    return None
    except Exception as e:
        globals.Log(f"Error in getoddsrequest: {e}")
        return None

async def createbrowser():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "browserdata\\rivers")
    p = await async_playwright().start()
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        channel="chrome",
        geolocation={"latitude": 42.0493, "longitude": -88.1065},
        permissions=["geolocation"],
        #args = ["--window-position=-900,-1080"]
    )
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1800, "height": 890})
    await page.goto("https://il.betrivers.com/?page=sportsbook#bethistory/")#, timeout=60000)
    #await asyncio.Event().wait()
    return page

async def checkbalance(page: Page):
    try:
        # await page.goto("https://sportsbook.draftkings.com/mybets")
        await asyncio.sleep(3)
        balance = await page.query_selector('div[data-target="menu-quick-deposit"]')

        balance = await balance.text_content()
        balance = balance.replace("$", "").replace(",", "").replace("Wallet", "").strip()
        balance = float(balance)
        return balance
    except Exception as e:
        print(f"Error in checkbalance: {e}")
        return 0.00

async def clearbets(page: Page):
    await page.reload()
    cleared = False
    try:
        waitforremove = await page.wait_for_selector("button.mod-KambiBC-betslip__clear-btn", timeout=5000)
        await waitforremove.click()
        await asyncio.sleep(1)
        cleared = True
    except:
        pass

    if cleared == False:
        try:
            clears = await page.query_selector_all('div[data-betty-theme="icon--betslipClose"]')
            for clear in clears:
                await clear.click()
                await asyncio.sleep(1)
            cleared = True
        except:
            pass

async def newbet(page: Page, bet: classes.Bet):
    await page.goto("https://il.betrivers.com/?page=my-account&subpage=account")
    await page.goto(bet.desktop_url)
    global activebet
    activebet = bet

    try:
        betslip = None
        try:
            betslip = await page.wait_for_selector("span.mod-KambiBC-betslip__header-outcome-count", timeout=8000)
        except:
            print("Rivers | Bet not available")
            return "Unavailable"
        
        if betslip:
            loggedin = await checklogin(page)
            if loggedin == False: return False
            totalbetele = await page.wait_for_selector("span.mod-KambiBC-betslip__header-outcome-count")
            totalbetct = await totalbetele.text_content()
            while totalbetct == "": 
                totalbetele = await page.wait_for_selector("span.mod-KambiBC-betslip__header-outcome-count")
                totalbetct = await totalbetele.text_content()
                await asyncio.sleep(0.1)

            totalbetct = totalbetct.strip()
            if "1" not in totalbetct:
                #await clearbets(page)
                print("Rivers: Had more than 1 bet! Need to restart")
                return False
            
            #Possible edit here!
            # placebetbutton = await page.query_selector('div.dk-place-bet-button__wrapper')
            # placebetbuttontext = await placebetbutton.inner_text()

            # if "Verify" in placebetbuttontext:
            #     await placebetbutton.click()
            #     await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
            #     return False
            
            oddshandle = await page.query_selector('span.mod-KambiBC-betslip-outcome__odds')
            odds = await oddshandle.inner_text()
            if "SUSPENDED" in odds:
                #await clearbets(page)
                await sendmsg(f"Odds are suspended\nBet Slip: {odds}\nArbitrage: {bet.price}", color=16711680)
                return False
            odds = int(odds.strip())
            if odds == bet.price:
                #print(f"Odds match: {odds} == {bet.price}")
                return True
            else:
                #await clearbets(page)
                await sendmsg(f"Odds don't match\nBet Slip: {odds}\nArbitrage: {bet.price}", color=16711680)
                return False

    except Exception as e:
        print(f"Error in Rivers: {e}")
        return False
    
async def checklogin(page: Page):
    try:
        loginbutton = await page.query_selector('button[color="primary"]')
        if loginbutton:
            await page.goto("https://il.betrivers.com/?page=my-account", timeout=30000)
            await asyncio.sleep(2)
            btnlogin = await page.wait_for_selector('button[data-translate="BTN_LOGIN_TITLE"]', timeout=15000)
            await btnlogin.click()

            avatar = await page.query_selector('div[data-target="menu-user-account"]')
            maxct = 0
            while avatar is None:
                if maxct > 10:
                    await sendmsg("Rivers: Unable to login", title="Login", color=16711680)
                    return
                maxct += 1
                await asyncio.sleep(1)
                avatar = await page.query_selector('div[data-target="menu-user-account"]')
            await sendmsg("Rivers: Logged back in...", title="Login", color=65280)
            return False
    except Exception as e:
        print(f"Error in checklogin Rivers: {e}")
        return False

async def addtoslip(page: Page, bet: classes.Bet, stake):
    await page.goto("https://il.betrivers.com/?page=my-account&subpage=account")
    await page.goto(bet.desktop_url)
    try:
        await page.wait_for_selector("span.mod-KambiBC-betslip__header-outcome-count", timeout=12000)
    except:
        print("Rivers | Bet not available")
        return False
    try:#UNCOMMENT
        alert = await page.query_selector('div[data-testid="alert"]')
        if alert:
            alerttext = await alert.text_content()
            if "Geolocation" in alerttext:
                await sendmsg2(f"Geolocation Error!", color=16711680, image_path=await captureimg(page))
                await page.reload()
                return False
    except:
        pass
    
    loggedin = await checklogin(page)
    if loggedin == False: return False
    inputbets = await page.query_selector_all('input.mod-KambiBC-stake-input')
    if len(inputbets) == 0:
        return False
    await inputbets[0].type(str(stake), delay=20)


async def placebet(page: Page, stake):
    # await sendmsg2(title = f"Rivers: Bet was verified | Stake: ${stake}", color=65280)
    # await page.reload()
    # await clearbets(page)
    # return True
    try:
        placebet = await page.query_selector('button.mod-KambiBC-betslip__place-bet-btn')
        await placebet.click()
        maxct = 0
        retried = 0
        while True:
            try:
                maxct += 1
                if maxct > 70: break
                placebetbutton = await page.query_selector('button.mod-KambiBC-betslip__place-bet-btn')
                placedbet = await page.query_selector("div.mod-KambiBC-betslip-receipt-header")
                betnotplaced = await page.query_selector("div.mod-KambiBC-betslip-feedback")
                wagerapproval = await page.query_selector("div.mod-KambiBC-betslip-pba__title")

                if wagerapproval:
                    confirmtext = await wagerapproval.text_content()
                    confirmtext = confirmtext.strip()
                    if "Wager approval" in confirmtext:
                        await sendmsg2(title=f"Rivers: Wager Approval needed... Attempting to automatically approve.", color=16711680)
                        sendall = await page.query_selector('input[id="PBA_SEND_ALL"]')
                        await sendall.click()
                        await asyncio.sleep(1)
                        allbuttons = await page.query_selector('mod-KambiBC-betslip-pba__button-wrapper')
                        continuebutton = await allbuttons.query_selector_all('button')
                        await continuebutton[1].click()
                        await asyncio.sleep(1)

                if betnotplaced:
                    betnotplacedtext = await betnotplaced.text_content()
                    betnotplacedtext = betnotplacedtext.strip()
                    if "Bet not placed" in betnotplacedtext:
                        if retried >= 2:
                            await sendmsg2(title=f"Rivers: Bet not placed", color=16711680)
                            break
                        retried += 1
                        #await savepage(page)
                        await sendmsg2(title=f"Rivers: Bet likely closed, retrying...", color=16711680)
                        #await sendmsg2(title=f"WAITING FOR THIS ERROR PLS NOTIFY RJ", color=16711680)
                        back = await page.query_selector('button.mod-KambiBC-betslip-button')
                        await back.click()
                        
                    
                    if "Odds for one or more" in betnotplacedtext:
                        await sendmsg2(f"Rivers: Odds changed while placing. Trying again...", title="Retrying...", color=16711680)
                        buttons = await page.query_selector_all('button.mod-KambiBC-betslip-button')
                        await buttons[1].click(timeout=5000)
                
                if placedbet: 
                    confirmbettext = await placedbet.text_content()
                    confirmbettext = confirmbettext.strip()
                    if "been placed!" in confirmbettext:
                        break
                    print("Bet Placed Rivers...")

                if placebetbutton:
                    try:
                        if await placebetbutton.get_attribute("disabled") == None:
                            await placebetbutton.click(timeout=5000)
                    except:
                        pass
            except Exception as e:
                print(f"Error in placebet: {e}")
                return False

            await asyncio.sleep(1)

        confirmbet = await page.wait_for_selector("div.mod-KambiBC-betslip-receipt-header", timeout=15000)
        confirmbettext = await confirmbet.text_content()
        confirmbettext = confirmbettext.strip()

        if "been placed!" in confirmbettext:
            await sendmsg2(title = f"Rivers: Bet was verified | Stake: ${stake}", color=65280)
            return True
        else:
            await sendmsg2(title = f"Rivers: Unable To Place Bet | Stake: ${stake}", color=16711680, image_path=await captureimg(page))
            await asyncio.sleep(1)
            await page.reload()
            await clearbets(page)
            return False
    except Exception as e:
        globals.Log(f"Error 6 in Rivers: {e}")
        return False

async def savepage(page):
    filename = f"browserhtml\\HTML_{datetime.now().strftime('%H-%M-%S')}.html"
    html_content = await page.content()
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)
    await sendmsg2(msg = f"Page HTML saved to {filename}", title="HTML Saved", color=65280)

async def cashoutlast(page: Page):
    global activebet
    try:
        if activebet is not None:
            with open("cashouts.txt", "a") as file:
                file.write(f"[{datetime.now().strftime('%H:%M:%S')}] Rivers | {activebet.bet_name}\n")
                activebet = None
            await sendmsg2(title = "Rivers: Attempting to cash out last bet", color=65280)
        await page.goto("https://il.betrivers.com/?page=sportsbook#bethistory/")
        await page.wait_for_selector('div.KambiBC-my-bets-summary__coupons-list')
        allbets = await page.query_selector_all('div.KambiBC-react-collapsable-container')
        latestbet = allbets[0]
        cashout_button = await latestbet.wait_for_selector('div.KambiBC-react-cash-out-button')
        cashouttext = await cashout_button.inner_text()
        #Possible Edit Here!
        # if "Cash Out Suspended" in cashouttext:
        #     await sendmsg2("DraftKings: Cash Out is suspended, unable to cash out", title="Cash Out", color=16711680, image_path=await captureimg(page))
        #     return
        await cashout_button.click()
        maxwait = 0
        while "Confirm" not in cashouttext:
            if maxwait > 10:
                await sendmsg2("Rivers: Cash Out timed out", title="Cash Out", color=16711680, image_path=await captureimg(page))
                return
            maxwait += 1
            cashout_button = await latestbet.wait_for_selector('div.KambiBC-react-cash-out-button')
            cashouttext = await cashout_button.inner_text()
            await asyncio.sleep(0.25)

        await cashout_button.click()
        allbets = await page.query_selector_all('div.KambiBC-react-collapsable-container')
        latestbet = allbets[0]
        confirmbet = await latestbet.query_selector('div.KambiBC-react-cash-out-button')
        maxwait = 0
        while confirmbet:
            if maxwait > 20:
                await sendmsg2(title = "Rivers: Unable to confirm cashout", color=16711680, image_path=await captureimg(page))
                return
            maxwait += 1
            allbets = await page.query_selector_all('div.KambiBC-react-collapsable-container')
            latestbet = allbets[0]
            confirmbet = await latestbet.query_selector('div.KambiBC-react-cash-out-button')
            await asyncio.sleep(1)
        await sendmsg2(title = f"Rivers: Cashout was confirmed!", color=65280)
    except Exception as e:
        print(f"Error in cashoutlast: {e}")
        #await sendmsg2("DraftKings: Cash Out failed", title="Cash Out", color=16711680)

async def captureimg(page):
    try:
        imgpath = f"images\\img{datetime.now().strftime('%H-%M-%S')}.png"
        await page.screenshot(path=imgpath)
        return imgpath
    except Exception as e:
        print(f"Error in captureimg: {e}")
        return ""
    
async def sendmsg2(msg = "", title="Successful Arb Placement", color=65280, url="", image_path=""):
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
        "username": f"[{globals.instance}] Whale Arb",
        "avatar_url": "https://play-lh.googleusercontent.com/CPjzDLTfVr4if1FanT1XvSBeF_enE9K6qlSJeXWS7TZIHUeDNmEV3H0IFg6Miq7JZg"
    })
    
        data = aiohttp.FormData()
        if image_path and os.path.exists(image_path):
            data.add_field('file', open(image_path, 'rb'), filename=os.path.basename(image_path), content_type='application/octet-stream')
        data.add_field('payload_json', payload, content_type='application/json')
        async with aiohttp.ClientSession() as client:
            await client.post(globals.webhook, data=data, headers=headers)
            #await client.post("https://discordapp.com/api/webhooks/1337252768544718898/HHlhShp20q74PtOjxDiNEZnxbosjd5eaT_yYO9ppmMv8Gbcn87bfTrHrob1mE7S2EaAg", data=data, headers=headers)

    except Exception as e:
        print(f"Error in sendmsg: {e}")

async def sendmsg(msg = "", title="Rivers", color=65280, url="", image_path=""):
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
        "username": f"[{globals.instance}] Rivers Arb",
        "avatar_url": "https://cdcgaming.com/wp-content/uploads/2024/05/BetRivers-Rush-Street-Interactive.jpg"
    })
    
        data = aiohttp.FormData()
        if image_path and os.path.exists(image_path):
            data.add_field('file', open(image_path, 'rb'), filename=os.path.basename(image_path), content_type='application/octet-stream')
        data.add_field('payload_json', payload, content_type='application/json')
        async with aiohttp.ClientSession() as client:
            await client.post("https://discord.com/api/webhooks/1329543168919863406/JVXYp271RQXI6u8i_NkWvKOOSMZ-nmc8ZCQ1BuDYvRTYpdHBUTHelZwWNUfbwT7yOgOy", data=data, headers=headers)
            #await client.post("https://discordapp.com/api/webhooks/1337252768544718898/HHlhShp20q74PtOjxDiNEZnxbosjd5eaT_yYO9ppmMv8Gbcn87bfTrHrob1mE7S2EaAg", data=data, headers=headers)

    except Exception as e:
        print(f"Error in sendmsg: {e}")
       