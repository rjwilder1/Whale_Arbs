from datetime import datetime
import asyncio, os, classes, aiohttp, json, globals
from patchright.async_api import async_playwright, Page, ElementHandle
cashout = None
activebet: classes.Bet = None
async def createbrowser():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "browserdata\\caesars")
    p = await async_playwright().start()
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,

        channel="chrome",
        geolocation={"latitude": 42.0493, "longitude": -88.1065},
        permissions=["geolocation"],
        args = ["--window-position=-1800,-1080"]
    )
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1800, "height": 890})
    await page.goto("https://sportsbook.caesars.com/us/il/bet/")#, timeout=60000)
    #await asyncio.Event().wait()
    return page

async def checkbalance(page: Page):
    try:
        await asyncio.sleep(2)
        balance = await page.query_selector('p.balance')
        balance = await balance.text_content()
        balance = balance.strip()
        balance = balance.replace("$", "").replace(",", "")
        balance = float(balance)
        return balance
    except Exception as e:
        print(f"Error in checkbalance: {e}")
        return 0.00

async def clearbets(page: Page):
    try:
        waitforremove = await page.wait_for_selector('button[data-testid="clear-all-button"]', timeout=5000)
        await waitforremove.click()
    except:
        pass

async def newbet(page: Page, bet: classes.Bet):
    await page.goto(bet.desktop_url)
    global activebet
    activebet = bet
    try:
        betslip = None
        # try: # Check if location is verified FIX
        #     verify = await page.query_selector('a[data-test-id="Verify Account-cta-link"]')
        #     if verify:
        #         await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
        #         await verify.click()
        #         asyncio.sleep(2)
        #         return "Unavailable"
        # except:
        #     pass
        # locationrequired = await page.query_selector("div.user-status-banner__content")
        # if locationrequired:
        #     await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
        #     await page.goto("https://sportsbook.draftkings.com/auth")
        #     await asyncio.sleep(5)
        #     return "Unavailable"
    
        # errorbanner = await page.query_selector('div.dk-betslip-error-banner__wrapper') # Check if bet is available FIX
        # if errorbanner:
        #     errortext = await errorbanner.inner_text()
        #     if "no longer available" in errortext.lower():
        #         return "Unavailable"
            
        try:
            betslip = await page.wait_for_selector('div.selectionList', timeout=7000)
        except:
            print("Bet not available")
            return "Unavailable"
        
        if betslip:
            loggedin = await checklogin(page)
            if loggedin == False: return False
            totalbetele = await page.wait_for_selector("ul.react-tabs__tab-list > li:nth-child(1)")
            totalbetct = await totalbetele.query_selector("div.count")
            totalbetctt = await totalbetele.text_content()
            totalbetctt = totalbetctt.strip()
            if totalbetctt != "1":
                if totalbetct == "0": return "Unavailable"
                    #await clearbets(page)
                print("Caesars: Had more than 1 bet! Need to restart")
                return False
            
            oddshandle = await page.query_selector('span[data-qa="betslip-selection-odds"]')
            odds = await oddshandle.inner_text()
            odds = float(odds.strip())
            if odds == bet.price:
                print(f"Odds match: {odds} == {bet.price}")
                return True
            else:
                #await clearbets(page)
                await sendmsg(f"Odds don't match\nBet Slip: {odds}\nArbitrage: {bet.price}", color=16711680)
                return False

    except Exception as e:
        print(f"Error in Caesars: {e}")
        return False
    
async def checklogin(page: Page):
    try:
        if await page.query_selector('div.notLoggedInContainer'):

            loginbutton = await page.query_selector('div.account-icon')
            if loginbutton:
                await loginbutton.click()
                await asyncio.sleep(2)
                await page.click('button[data-qa="login-form-cta-log-in-button"]')
                await asyncio.sleep(1)
                avatar = await page.query_selector('div.loggedInContainer')
                maxct = 0
                while avatar is None:
                    if maxct > 10:
                        await sendmsg("Caesars: Unable to login", title="Login", color=16711680)
                        return
                    maxct += 1
                    await asyncio.sleep(1)
                    avatar = await page.query_selector('div.loggedInContainer')
                await sendmsg("Caesars: Logged back in...", title="Login", color=65280)
                return False
    except Exception as e:
        print(f"Error in checklogin Caesars: {e}")
        return False

async def placebet(page: Page, stake):
    allbets = await page.query_selector_all('input.betslipInputField')
    if len(allbets) > 1:
        placebetinput = allbets[0]
        await placebetinput.clear()
        await placebetinput.type(str(stake))

        placebetbutton = await page.query_selector('button[data-testid="place-bet-button"]')
        await asyncio.sleep(1)
        await placebetbutton.click()

        confirmbet = await page.wait_for_selector("div.betPlacedHeader", timeout=40000)
        confirmbettext = await confirmbet.text_content()

        if "Good Luck!" in confirmbettext:
            await sendmsg2(title = f"Caesars: Bet was verified | Stake: ${stake}", color=65280)
        else:
            await sendmsg2(title = f"Caesars: Bet was not verified | Stake: ${stake}", color=16711680)
        
        await asyncio.sleep(1)
        await page.reload()
        await clearbets(page)

async def cashoutlast(page: Page):
    global activebet
    try:
        if activebet is not None:
            with open("cashouts.txt", "a") as file:
                file.write(f"[{datetime.now().strftime('%H:%M:%S')}] Caesars | {activebet.bet_name}\n")
                activebet = None
            await sendmsg2(title = "Caesars: Attempting to cash out last bet", color=65280)

        table = await page.wait_for_selector("ul.react-tabs__tab-list > li:nth-child(2)")
        await table.click()
        await asyncio.sleep(1)
        allbets = await page.query_selector("div.OpenBets")
        maxct = 0
        while allbets is None:
            if maxct > 10:
                await sendmsg2("Caesars: Unable to cash out", title="Cash Out", color=16711680, image_path=await captureimg(page))
                return
            maxct += 1
            allbets = await page.query_selector("div.OpenBets")
            await asyncio.sleep(1)
        latestbet = await allbets.query_selector("div:nth-child(1)")
        cashout_button = await latestbet.query_selector('button[data-qa="cashout-button-default"]')
        await cashout_button.click()
        await asyncio.sleep(1)
        latestbet = await allbets.query_selector("div:nth-child(1)")
        cashout_button_confirm = await latestbet.query_selector('button[data-qa="cashout-button-confirmation"]')    
        maxct = 0
        while cashout_button_confirm is None:
            if maxct > 5:
                await sendmsg2("Caesars: Cash Out timed out", title="Cash Out", color=16711680, image_path=await captureimg(page))
                return
            maxct += 1
            latestbet = await allbets.query_selector("div:nth-child(1)")
            cashout_button_confirm = await latestbet.query_selector('button[data-qa="cashout-button-confirmation"]')
        await cashout_button_confirm.click()    
        confirmed = await page.query_selector('button[data-qa="cashout-button-complete"]')
        maxct = 0
        while confirmed is None:
            if maxct > 10:
                await sendmsg2("Caesars: Cash Out timed out", title="Cash Out", color=16711680, image_path=await captureimg(page))
                return
            maxct += 1
            confirmed = await page.query_selector('button[data-qa="cashout-button-complete"]')
            await asyncio.sleep(1)

        await sendmsg2(title = f"Caesars: Cashout was confirmed!", msg=f"", color=65280)
    except Exception as e:
        print(f"Error in cashoutlast: {e}")

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

async def sendmsg(msg = "", title="Caesars", color=65280, url="", image_path=""):
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
        "username": f"[{globals.instance}] Caesars Arb",
        "avatar_url": "https://www.rocketarena.com/assets/img/221231-sportsbook-betting-101-590x430-cc3fc1c0c0.png"
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
       