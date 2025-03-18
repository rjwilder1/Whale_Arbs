from datetime import datetime
import json
import asyncio, os, classes, aiohttp
from patchright.async_api import async_playwright, Page, ElementHandle
failed = None
async def createbrowser():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "browserdata\\fanduel")
    p = await async_playwright().start()
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        channel="chrome",
        geolocation={"latitude": 42.0493, "longitude": -88.1065},
        permissions=["geolocation"],
        args=["--start-maximized"]
    )
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1920, "height": 1080})
    await page.goto("https://account.il.sportsbook.fanduel.com/account", timeout=60000)
    #await asyncio.Event().wait()
    return page

async def newbet(page: Page, bet: classes.Bet):
    await page.goto(bet.desktop_url)

    try:
        betslip = await page.wait_for_selector('span[aria-label*="selection in betslip"]', timeout=10000)
        #CHECK LOGIN
        loginbutton = await page.query_selector("span:has-text('Log back in')")
        if loginbutton:
            await page.goto("https://account.il.sportsbook.fanduel.com/login", timeout=60000)
            await asyncio.sleep(1)
            #data-test-id="button-submit"
            await page.click("[id='login-password']")
            await asyncio.sleep(1)
            await page.click("[data-test-id='button-submit']")
            await asyncio.sleep(1)
            await sendmsg("FanDuel: Logged back in...", title="Login", color=65280)

        adding = await page.query_selector('.ReactModal__Overlay.ReactModal__Overlay--after-open')
        if adding:
            await adding.click()
            print("Closed the add bet modal")
        if betslip:
            betslipct = await betslip.get_attribute('aria-label')
            if betslipct != "1 selection in betslip.":
                await clearbets(page)
                print(f"Had {betslipct} bets! Need to restart")
                return False

            element = await page.query_selector('span[aria-label^="Odds "]')
            if element:
                odds = await element.get_attribute('aria-label')
                odds = odds.replace("Odds ", "")
                if float(bet.price) == float(odds):
                    print(f"Odds match: {odds} == {bet.price}")
                else:
                    await clearbets(page)
                    await sendmsg(f"Odds don't match\nBet Slip: {odds}\nArbitrage: {bet.price}", color=16711680)
                    return False
            else:
                print("Odds element not found")
                return False

            return True  # Reaching here means everything checks out

    except Exception as e:
        print(f"Error in FanDuel: {e}")
        return False


async def placebet(page: Page, stake):
    locator = await page.query_selector_all('input[type="text"]')
    await locator[0].type(str(stake))
    await page.locator('span:has-text("Place 1 bet for $")').click()
    try:
        await page.wait_for_selector('span:has-text("Straight bet placed!")', timeout=8000)
        print("Placed FanDuel bet!")
        await sendmsg2("FanDuel: Bet was verified!", title="Bet Placed", color=65280)
        await asyncio.sleep(1)
        await page.reload()
        await clearbets(page)
    except:
        await sendmsg2("FanDuel: Bet was not verified!", title="Bet Placement Timeout", color=16711680)
    
async def clearbets(page: Page):
    try:
        waitforremove = await page.wait_for_selector('span:has-text("Remove all selections")', timeout=5000)
        await waitforremove.click()
    except:
        pass

async def sendmsg2(msg, title="Successful Arb Placement", color=65280, url="", image_path=""):
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
        "username": "Whale Arb",
        "avatar_url": "https://play-lh.googleusercontent.com/CPjzDLTfVr4if1FanT1XvSBeF_enE9K6qlSJeXWS7TZIHUeDNmEV3H0IFg6Miq7JZg"
    })
    
        data = aiohttp.FormData()
        if image_path and os.path.exists(image_path):
            data.add_field('file', open(image_path, 'rb'), filename=os.path.basename(image_path), content_type='application/octet-stream')
        data.add_field('payload_json', payload, content_type='application/json')
        print(msg)
        async with aiohttp.ClientSession() as client:
            await client.post("https://discord.com/api/webhooks/1342960629111062649/B1KKLi-Ka5H0Cb2ZzWpk4DiPnKRqXwpjNiNQ5kYAkrsOHQhNqwTopUoUlVJpecCtfVIF", data=data, headers=headers)
            #await client.post("https://discordapp.com/api/webhooks/1337252768544718898/HHlhShp20q74PtOjxDiNEZnxbosjd5eaT_yYO9ppmMv8Gbcn87bfTrHrob1mE7S2EaAg", data=data, headers=headers)

    except Exception as e:
        print(f"Error in sendmsg: {e}")
async def sendmsg(msg, title="FanDuel", color=65280, url="", image_path=""):
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
        "username": "Fanduel Arb",
        "avatar_url": "https://cdn.builtin.com/cdn-cgi/image/f=auto,fit=contain,w=200,h=200,q=100/https://builtin.com/sites/www.builtin.com/files/2023-07/fanduel_lg_vrt_rgb_blu_pos%20(1).png"
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
       