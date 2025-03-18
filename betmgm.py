#TODO
# - Add Cashout Loop
from datetime import datetime
import json, draftkings
import asyncio, os, classes, aiohttp, globals
from patchright.async_api import async_playwright, Page, ElementHandle
failed = None
activebet: classes.Bet = None

async def createbrowser():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "browserdata\\betmgm")
    p = await async_playwright().start()
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        channel="chrome",
        geolocation={"latitude": 42.0493, "longitude": -88.1065},
        permissions=["geolocation"],
        
    )
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1800, "height": 920})
    await page.goto("https://www.betmgm.com/")#, timeout=60000)
    #await asyncio.Event().wait()
    return page

async def checklogin(page: Page):
    try:
        loginbutton = await page.query_selector('vn-menu-item-text-content[data-testid="signin"]')
        if loginbutton:
            await loginbutton.click()
            await asyncio.sleep(2)
            await page.click('button[class^="login"]')
            await asyncio.sleep(1)
            avatar = await page.query_selector('svg[title="theme-avatar"]')
            maxct = 0
            while avatar is None:
                if maxct > 10:
                    await sendmsg("BetMGM: Unable to login", title="Login", color=16711680)
                    return
                maxct += 1
                await asyncio.sleep(1)
                avatar = await page.query_selector('svg[title="theme-avatar"]')
            await sendmsg("BetMGM: Logged back in...", title="Login", color=65280)
            return False
    except Exception as e:
        print(f"Error in checklogin BetMGM: {e}")
        return False
    
async def checkbalance(page: Page):
    try:
        # await page.goto("https://sports.il.betmgm.com/en/sports")
        # await asyncio.sleep(1)
        balance = await page.wait_for_selector('div.user-balance', timeout=10000)
        balance = await balance.text_content()
        balance = balance.strip()
        balance = balance.replace("$", "").replace(",", "")
        balance = float(balance)
        return balance
    
    except Exception as e:
        print(f"Error in checkbalance: {e}")
        return 0.00

async def getlivebetsct(page: Page):
    #ds-notification-bubble
    try:
        bubble = await page.wait_for_selector("ds-notification-bubble", timeout=5000)
        bubble = await bubble.text_content()
        bubble = bubble.strip()
        return bubble
    except:
        return "Error getting live bets count"

async def newbet(page: Page, bet: classes.Bet):
    global activebet
    activebet = bet
    await page.goto(bet.desktop_url)
    if "strongauthv2" in page.url:
        await sendmsg2("BetMGM: Need to verify account. Bets will not place anymore, shutting down...", title="2FA", color=16711680, image_path=await captureimg(page))
        await asyncio.sleep(5)
        os._exit(0)
        return False
    try:
        betslip = None
        try:
            betslip = await page.wait_for_selector("bs-digital-single-bet-pick.betslip-digital-pick.betslip-single-bet-pick", timeout=7000)
        except:
            print("Bet not available")
            return "Unavailable"
        if betslip:
            loggedin = await checklogin(page)
            if loggedin == False: return False
            totalbetele = await page.wait_for_selector("div.single-bet-linear__title")
            totalbetct = await totalbetele.text_content()
            if totalbetct != "Straights (1)":
                #await clearbets(page)
                print("Had more than 1 bet! Need to restart")
                return False
            if await betslip.query_selector("div.betslip-pick-odds__value--locked"):
                #await clearbets(page)
                return False
            oddshandle = await betslip.wait_for_selector("div.betslip-pick-odds__value")
            odds = await oddshandle.text_content()
            odds = int(odds.strip())

            if odds == bet.price:
                #print(f"Odds match: {odds} == {bet.price}")
                return True
            else:
                #await clearbets(page)
                await sendmsg(f"Odds don't match\nBet Slip: {odds}\nArbitrage: {bet.price}", color=16711680)
                return False

    except Exception as e:
        print(f"Error in BetMGM: {e}")
        draftkings.cashout = True
        return False
    
async def clearbets(page: Page):
    try:
        waitforremove = await page.wait_for_selector("div.betslip-picks-toolbar__remove-all-request", timeout=5000)
        await waitforremove.click()
    except:
        pass

async def placebet(page: Page, stake):
    # try:
    await page.locator('input.stake-input-value').clear()
    await asyncio.sleep(0.25)
    await page.locator('input.stake-input-value').fill(str(stake))
    await page.locator('input.stake-input-value').type(" ")
    await asyncio.sleep(0.3)
    await page.locator('.betslip-place-button > button').click()
    donect = 0
    await asyncio.sleep(0.5)

    while True:
        if donect > 70: break
        donect += 1

        placebetbutton = await page.query_selector(".betslip-place-button > button")
        if placebetbutton:
            buttontext = await placebetbutton.text_content()
            while "Processing bet" in buttontext:
                placebetbutton = await page.query_selector(".betslip-place-button > button")
                if placebetbutton is None:
                    break
                buttontext = await placebetbutton.text_content()
                await asyncio.sleep(1)

        alert = await page.query_selector("p.alert-content__message")
        maingeo = await page.query_selector("div.geo-comply-button")
        getverify = await page.query_selector(".pc-richtext")
        closed = await page.query_selector("div.betslip-pick-odds__value--closed")
        locked = await page.query_selector("div.betslip-pick-odds__value--locked")

        if closed:
            await sendmsg2(title="BetMGM: Bet was closed", color=16711680)
            raise Exception("Bet closed")
        
        if locked:
            await sendmsg2(title="BetMGM: Bet was locked", color=16711680)
            raise Exception("Bet locked")
        
        if maingeo:
            geobutton = await maingeo.query_selector("button")
            if geobutton:
                await geobutton.click()
                await asyncio.sleep(2)
                await sendmsg2(title="BetMGM: Geo Comply...", color=16711680)
                continue
                #raise Exception("Geo Comply")
        
        if alert:
            acceptchanges = await page.query_selector(".betslip-place-button > button")
            if acceptchanges:
                buttontext = await acceptchanges.text_content()
                if "will be removed" in buttontext:
                    raise Exception("Bet removed")
                elif "Place Bet" in buttontext:
                    await page.locator('input.stake-input-value').clear()
                    await asyncio.sleep(0.25)
                    await page.locator('input.stake-input-value').fill(str(stake))
                    await page.locator('input.stake-input-value').type(" ")
                    await asyncio.sleep(0.3)
                    await acceptchanges.click()
                    print("Placing bet again...")
                    await asyncio.sleep(2)
                    continue
        if getverify:
            break

        await asyncio.sleep(2)

    confirmbet = await page.wait_for_selector(".pc-richtext", timeout=5000)
    confirmbettext = await confirmbet.text_content()

    if "Your bet has been accepted. Good luck!" in confirmbettext:
        await sendmsg2(title = f"BetMGM: Bet was verified | Stake: ${stake}", color=65280)
    else:
        await sendmsg2(title = f"BetMGM: Bet was not verified | Stake: ${stake}", color=16711680)

    await page.reload()
    await clearbets(page)

async def cashoutlast(page: Page):
    global activebet
    try:
        if activebet is not None:
            with open("cashouts.txt", "a") as file:
                file.write(f"[{datetime.now().strftime('%H:%M:%S')}] BetMGM | {activebet.bet_name}\n")
                activebet = None
        await sendmsg2(title = "BetMGM: Attempting to cash out last bet", color=65280)
        await page.goto("https://sports.il.betmgm.com/en/sports/my-bets/open")
        table = await page.wait_for_selector('ms-my-bets-list-column')
        latestbet = await table.wait_for_selector(':scope > div:nth-child(1)')#span[class="ds-btn-container"]
        allbuttons = await latestbet.query_selector_all('span[class="ds-btn-container"]')
        cashout_button = allbuttons[1]

        cashouttext = await cashout_button.inner_text()
        if "Unavailable" in cashouttext:
            await sendmsg2(title = "BetMGM: Cash Out is suspended, unable to cash out", color=16711680, image_path=await captureimg(page))
            return
        await cashout_button.click()
        maxwait = 0
        while "Confirm" not in cashouttext:
            if maxwait > 20:
                await sendmsg2(title = "BetMGM: Cash Out timed out", color=16711680, image_path=await captureimg(page))
                return
            maxwait += 1
            allbuttons = await latestbet.query_selector_all('span[class="ds-btn-container"]')
            cashout_button = allbuttons[1]
            cashouttext = await cashout_button.inner_text()
            await asyncio.sleep(0.25)
        await cashout_button.click()

        latestbet = await table.wait_for_selector(':scope > div:nth-child(1)')#span[class="ds-btn-container"]
 
        gettxt = await latestbet.wait_for_selector('div[id="cashoutContainer"]')
        cashouttext = await gettxt.inner_text()
        maxwait = 0
        while "You Cashed Out" not in cashouttext:
            if maxwait > 10:
                await sendmsg2(title = "BetMGM: Unable to confirm cashout", color=16711680, image_path=await captureimg(page))
                return
            maxwait += 1
            latestbet = await table.wait_for_selector(':scope > div:nth-child(1)')
            gettxt = await latestbet.wait_for_selector('div[id="cashoutContainer"]')
            cashouttext = await gettxt.inner_text()
            await asyncio.sleep(1)

        await sendmsg2(title = "BetMGM: Cashout was confirmed!", color=65280)
    except Exception as e:
        print(f"Error in cashoutlast BetMGM: {e}")

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
        print(msg)
        async with aiohttp.ClientSession() as client:
            await client.post(globals.webhook, data=data, headers=headers)
            #await client.post("https://discordapp.com/api/webhooks/1337252768544718898/HHlhShp20q74PtOjxDiNEZnxbosjd5eaT_yYO9ppmMv8Gbcn87bfTrHrob1mE7S2EaAg", data=data, headers=headers)

    except Exception as e:
        print(f"Error in sendmsg: {e}")

async def sendmsg(msg = "", title="BetMGM", color=65280, url="", image_path=""):
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
        "username": f"[{globals.instance}] BetMGM Arb",
        "avatar_url": "https://www.sportsvideo.org/wp-content/uploads/2020/03/BetMGM-Logo-%E2%80%93-HiRes.png"
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

async def captureimg(page):
    try:
        imgpath = f"images\\img{datetime.now().strftime('%H-%M-%S')}.png"
        await page.screenshot(path=imgpath)
        return imgpath
    except Exception as e:
        print(f"Error in captureimg: {e}")
        return ""