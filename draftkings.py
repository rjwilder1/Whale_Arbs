from datetime import datetime
import asyncio, os, classes, aiohttp, json, globals, requests
from patchright.async_api import async_playwright, Page, ElementHandle
cashout = None
activebet: classes.Bet = None
TotalStake = 0.10

async def createbrowser():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(script_dir, "browserdata\\draftkings")
    p = await async_playwright().start()
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,

        channel="chrome",
        geolocation={"latitude": 42.0493, "longitude": -88.1065},
        permissions=["geolocation"],
        #args = ["--window-position=-1800,-1080"]
    )
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1800, "height": 890})
    await page.goto("https://myaccount.draftkings.com/login", timeout=60000)
    #await asyncio.Event().wait()
    return page

async def getoddsrequest(url):
    try:
        eventid = url.split("=")[1]
        querystring = {"siteName": "dkusil", "selectionIds": eventid.replace("%23", "#")}

        api_url = "https://sportsbook-nash.draftkings.com/api/sdinfo/dkusil/v1/selectioninfo"
        data = None
        headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://sportsbook.draftkings.com",
            "priority": "u=1, i",
            "referer": "https://sportsbook.draftkings.com/",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers, params=querystring, proxy="http://pumywuYUoA:HgWfqp1rVr@142.173.138.227:11857") as response:
                if response.status == 200:
                    data = await response.json()
                    american_odds = data["selections"][0]["displayOdds"]["american"].replace("−", "-")
                    decimal_odds = float(data["selections"][0]["displayOdds"]["decimal"])
                    #await sendmsg(f"Odds: {american_odds}")
                    return {"american": american_odds, "decimal": decimal_odds}
                else:
                    #await sendmsg(title = "Failed to get DraftKings odds", msg=f"Failed to get DraftKings odds...: {data}")
                    return "Unavailable"
    except Exception as e:
        globals.Log(f"Error in getoddsrequest: {e}")
        return None



    # eventid = url.split("=")[1]
    # async with aiohttp.ClientSession() as session:
    #     headers = {
    #         'accept': 'application/json',
    #         'accept-language': 'en-US,en;q=0.9',
    #         'content-type': 'application/json',
    #         'origin': 'https://sportsbook.draftkings.com',
    #         'priority': 'u=1, i',
    #         'referer': 'https://sportsbook.draftkings.com/',
    #         'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    #         'sec-ch-ua-mobile': '?0',
    #         'sec-ch-ua-platform': '"Windows"',
    #         'sec-fetch-dest': 'empty',
    #         'sec-fetch-mode': 'cors',
    #         'sec-fetch-site': 'same-site',
    #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    #         #'Cookie': k
    #     }
    #     async with session.get(f"https://sportsbook-nash.draftkings.com/api/sdinfo/dkusil/v1/selectioninfo?siteName=dkusil&selectionIds={eventid}", headers=headers) as response:
    #         data = await response.text()
    #         if response.status == 200:
    #             data = await response.json()
    #             american_odds = data["selections"][0]["displayOdds"]["american"].replace("−", "-")
    #             decimal_odds = float(data["selections"][0]["displayOdds"]["decimal"])
    #             return {"american": american_odds, "decimal": decimal_odds}
    #         else:
    #             print(f"Failed to get DK odds...: {data}")
    #             return data

async def placebetrequest(page, bet: classes.Bet, stake):#, bet: classes.Bet, stake):
    url = bet.desktop_url
    #try:
    odds = await getoddsrequest(url)
    if odds == None: raise Exception("Odds are None")
    if odds == "Unavailable":
        await sendmsg(title = "Unable to place bet", msg="Odds are no longer available", color=16711680)
        return False
    
    american_odds = odds['american'].replace("−", "-")
    decimal_odds = odds["decimal"]
    oddsppr = int(american_odds.strip())
    #bet.price = oddsppr
    if oddsppr == bet.price:
        american_odds = odds["american"]
        payout = globals.payout(odds=decimal_odds, wager=stake)
        eventid = url.split("=")[1]
        eventid = eventid.replace("%23", "#")

        cookie_string = await globals.get_cookies(page)
        desired_cookies = ["_gcl_au", "_tgpc", "_scid", "_fbp", "__ssid", "_svsid", "_hjSessionUser_2150570",
    "_ScCbts", "_sctr", "_csrf", "STIDN", "STH", "_gid", "site", "PRV", "bm_sz",
    "ak_bmsc", "_dpm_ses.16f4", "uk", "gch_sb", "_tguatd", "_tgidts", "_tglksd",
    "_scid_r", "ss-id", "ss-pid", "_sp_srt_ses.16f4", "_sp_srt_id.16f4",
    "_uetsid", "_uetvid", "_ga", "_ga_M8T3LWXCC5", "_rdt_uuid", "_dpm_id.16f4",
    "ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42", "_tgsid", "hgg",
    "jws_sb", "jws_gs", "jwe", "iv", "_ga_QG8WHJSQMJ", "bm_sv", "STE", "_abck"]
        cookie_pairs = [cookie.split("=", 1) for cookie in cookie_string.split("; ") if "=" in cookie]
        filtered_cookies = [f"{key}={value}" for key, value in cookie_pairs if key in desired_cookies]
        filtered_cookie_string = "; ".join(filtered_cookies)

        url = "https://gaming-us-il.draftkings.com/api/wager/v1/placeBets"

        payload = {
    "bets": [
        {
            "type": "Single",
            "selectionsMapped": [{"id": eventid}],
            "stake": stake,
            "trueOdds": decimal_odds,
            "displayOdds": f"{american_odds}",
            "numberOfBets": 1,
            "isSP": False,
            "potentialReturns": payout
        }
    ],
    "selections": [
        {
            "id": eventid,
            "trueOdds": decimal_odds,
            "displayOdds": f"{american_odds}"
        }
    ],
    "selectionsForYourBet": [],
    "locale": "en-US",
    "oddsStyle": "american",
    "autoAcceptMode": "AcceptHigher",
    "binaryMetaData": {
        "betSlipAdditionalInformation": {
            "betSlipId": "88ab13db-8283-4330-a1aa-2516134bd4ce",
            "betSlipOrder": 1
        }
    }
}

        headers = {
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "clienttype": "Website",
            "content-type": "application/json",
            "origin": "https://sportsbook.draftkings.com",
            "priority": "u=1, i",
            "referer": "https://sportsbook.draftkings.com/",
            "sec-ch-ua": '""Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134""',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '""Windows""',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "x-client-feature": "betslip",
            "x-client-name": "web",
            "x-client-page": "home",
            "x-client-version": "2511.2.1.9",
            "x-client-widget-name": "betslip",
            "x-client-widget-version": "2511.2.1",
            "x-request-client-timestamp": "1741880292769",
            "Cookie": filtered_cookie_string
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            if status == "LiveDelay":
                print("Bet placed successfully!")
                await sendmsg2(title = "Bet placed successfully!", msg=f"Bet: {bet.bet_name}\nOdds: {american_odds}\nStake: ${TotalStake}\nPotential Returns: ${payout}")
                return True
            else:
                await sendmsg2(title = "Unable to place bet", msg=f"Unable to place bet... Data: {data}")
                return False
        else:
            await sendmsg2(title = "Failed to place bet", msg=f"Failed to place bet\nStatus Code: {response.status_code}\nData: {response.text}")
            return False
        if 1+1 != 2:
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url, json=payload, headers=headers) as response:
        #         print(f"Response Status: {response.status}")  # Debugging step

        #         if response.status == 200:
        #             response_data = await response.json()
        #             return response_data
        #         else:
        #             error_data = await response.text()
        #             print(f"Failed to place bet. Response: {error_data}")
        #             return None


#         headers = {
#     "accept": "application/json",
#     "accept-language": "en-US,en;q=0.9",
#     "clienttype": "Website",
#     "content-type": "application/json",
#     "origin": "https://sportsbook.draftkings.com",
#     "priority": "u=1, i",
#     "referer": "https://sportsbook.draftkings.com/",
#     "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-site",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
#     "x-client-feature": "betslip",
#     "x-client-name": "web",
#     "x-client-page": "home",
#     "x-client-version": "2509.2.1.11",
#     "x-client-widget-name": "betslip",
#     "x-client-widget-version": "2510.1.1",
#     "Cookie": filtered_cookie_string,

# }
#         payload = json.dumps({
#     "bets": [
#         {
#             "type": "Single",
#             "selectionsMapped": [{"id": eventid}],
#             "stake": stake,
#             "trueOdds": decimal_odds,
#             "displayOdds": f"{american_odds}",
#             "numberOfBets": 1,
#             "isSP": False,
#             "potentialReturns": payout
#         }
#     ],
#     "selections": [
#         {
#             "id": eventid,
#             "trueOdds": decimal_odds,
#             "displayOdds": f"{american_odds}"
#         }
#     ],
#     "selectionsForYourBet": [],
#     "locale": "en-US",
#     "oddsStyle": "american",
#     "autoAcceptMode": "AcceptHigher",
#     "binaryMetaData": {
#         "betSlipAdditionalInformation": {
#             "betSlipId": "88ab13db-8283-4330-a1aa-2516134bd4ce",
#             "betSlipOrder": 1
#         }
#     }
# })

#         async with aiohttp.ClientSession() as session:
#             async with session.post("https://gaming-us-il.draftkings.com/api/wager/v1/placeBets", headers=headers, data=payload) as response:
#                 data = await response.text()
#                 if response.status == 200:
#                     data = await response.json()
#                     status = data['status']
#                     if status == "LiveDelay":
#                         print("Bet placed successfully!")
#                         sendmsg2(title = "Bet placed successfully!", msg=f"Bet: {bet.bet_name}\nOdds: {american_odds}\nStake: ${TotalStake}\nPotential Returns: ${payout}")
#                         return data
#                     else:
#                         sendmsg2(title = "Unable to place bet", msg=f"Unable to place bet... Status code: {status}\nData: {data}")
#                         return data
#                 else:
#                     print("Failed to place bet...")
#                     return data
            pass

    else:
        await sendmsg2(f"Odds don't match\nBet Slip: {american_odds}\nArbitrage: {bet.price}", color=16711680)
        raise Exception(f"Odds don't match")
        return False
    # except Exception as e:
    #     print(f"Error in placebetrequest: {e}")
    #     return False

async def checkbalance(page: Page):
    try:
        # await page.goto("https://sportsbook.draftkings.com/mybets")
        await asyncio.sleep(2)
        balance = await page.query_selector_all('div[data-test-id="user-balance"]')
        if len(balance) == 0:
            return 0.00
        elif len(balance) > 1:
            balance = balance[1]
        balance = await balance.text_content()
        balance = balance.strip()
        balance = balance.replace("$", "").replace(",", "")
        balance = float(balance)
        return balance
    except Exception as e:
        print(f"Error in checkbalance: {e}")
        return 0.00
    
async def checkbets(page: Page):#FIX
    await page.goto("https://sportsbook.draftkings.com/mybets")
    filters = await page.query_selector_all('div[data-test-id="my-bets-status-filters"]')
    if len(filters) == 0:
        return None
    elif len(filters) > 1:
        filters = filters[1]
    await filters.click()
    table = await page.query_selector('sb-lazy-render[data-testid="sb-lazy-render"] > div')
    allbets = await table.query_selector_all('div')
    return len(allbets)

async def clearbets(page: Page):
    try:
        await page.reload()
        waitforremove = await page.wait_for_selector("div.dk-betslip-header__clear-all", timeout=5000)
        await waitforremove.click()
        confirm = await page.wait_for_selector("div.dk-betslip-confirm-clear-all__confirm-button", timeout=5000)
        await confirm.click()
    except:
        pass

async def addtoslip(page: Page, bet: classes.Bet, stake):
    await page.goto(bet.desktop_url)
    # locationrequired = await page.query_selector("div.user-status-banner__content")#UNCOMMENT
    # if locationrequired:
    #     await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
    #     await page.goto("https://sportsbook.draftkings.com/auth")
    #     await asyncio.sleep(5)
    #     return False

    errorbanner = await page.query_selector('div.dk-betslip-error-banner__wrapper')
    if errorbanner:
        errortext = await errorbanner.inner_text()
        if "no longer available" in errortext.lower():
            return False
    loggedin = await checklogin(page)
    if loggedin == False: return False
    try:
        await page.wait_for_selector("div[data-testid='betslip-header-counter']", timeout=7000)
    except:
        print("Bet not available")
        return False
    totalinputs = await page.query_selector_all('input.betslip-wager-box__input')
    if len(totalinputs) != 1: return False
    await page.locator('input.betslip-wager-box__input').clear()
    await page.locator('input.betslip-wager-box__input').type(str(stake))
    
async def placebet(page: Page, stake):
    # await sendmsg2(title = f"DraftKings: Bet was verified | Stake: ${stake}", color=65280)
    # await page.reload()
    # await clearbets(page)
    # return True

    # placebetbutton = await page.query_selector('div.dk-place-bet-button__wrapper')
    # placebetbuttontext = await placebetbutton.inner_text()
    # if "Changes" in placebetbuttontext:
    #     await sendmsg2(f"Odds changed while placing bet! Skipping and cashing out...", color=16711680)
    #     raise Exception("Odds changed while placing bet")
    try:
        await page.locator('div.dk-place-bet-button__wrapper').click()

        confirmbet = await page.wait_for_selector("div.dk-betslip-receipt__header-title", timeout=60000)
        confirmbettext = await confirmbet.text_content()

        if "Bet Placed" in confirmbettext:
            await sendmsg2(title = f"DraftKings: Bet was verified | Stake: ${stake}", color=65280)
            return True
        else:
            await sendmsg2(title = f"DraftKings: Unable To Place Bet | Stake: ${stake}", color=16711680, image_path=await captureimg(page))
            await page.reload()
            await clearbets(page)
            return False
    except Exception as e:
        globals.Log(f"Error 6 in DraftKings: {e}")
        return False

async def newbet(page: Page, bet: classes.Bet):
    await page.goto(bet.desktop_url)
    global activebet
    activebet = bet
    try:
        betslip = None
        try:
            verify = await page.query_selector('a[data-test-id="Verify Account-cta-link"]')
            if verify:
                await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
                await verify.click()
                asyncio.sleep(2)
                return "Unavailable"
        except:
            pass
        locationrequired = await page.query_selector("div.user-status-banner__content")
        if locationrequired:
            await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
            await page.goto("https://sportsbook.draftkings.com/auth")
            await asyncio.sleep(5)
            return "Unavailable"
    
        errorbanner = await page.query_selector('div.dk-betslip-error-banner__wrapper')
        if errorbanner:
            errortext = await errorbanner.inner_text()
            if "no longer available" in errortext.lower():
                return "Unavailable"
        try:
            betslip = await page.wait_for_selector("div[data-testid='betslip-header-counter']", timeout=7000)
        except:
            print("Bet not available")
            return "Unavailable"
        if betslip:
            loggedin = await checklogin(page)
            if loggedin == False: return False
            totalbetele = await page.wait_for_selector("div[data-testid='betslip-header-counter']")
            totalbetct = await totalbetele.text_content()
            while totalbetct == "": 
                totalbetele = await page.wait_for_selector("div[data-testid='betslip-header-counter']")
                totalbetct = await totalbetele.text_content()
                await asyncio.sleep(1)
            totalbetct = totalbetct.strip()
            if totalbetct != "1":
                if totalbetct == "0": return "Unavailable"
                    #await clearbets(page)
                print("DK: Had more than 1 bet! Need to restart")
                return False
                

            placebetbutton = await page.query_selector('div.dk-place-bet-button__wrapper')
            placebetbuttontext = await placebetbutton.inner_text()

            if "Verify" in placebetbuttontext:
                await placebetbutton.click()
                await sendmsg(f"Location must be verified! Skipping this bet...", color=16711680)
                return False
            
            oddshandle = await page.query_selector('.betslip-odds__display-standard')
            odds = await oddshandle.inner_text()
            odds = odds.replace("−", "-")
            odds = int(odds.strip())
            if odds == bet.price:
                #print(f"Odds match: {odds} == {bet.price}")
                return True
            else:
                #await clearbets(page)
                await sendmsg(f"Odds don't match\nBet Slip: {odds}\nArbitrage: {bet.price}", color=16711680)
                return False

    except Exception as e:
        print(f"Error in DraftKings: {e}")
        return False
    
async def checklogin(page: Page):
    try:
        loginbutton = await page.query_selector('a[data-test-id="Log In-cta-link"]')
        if loginbutton:
            await page.goto("https://myaccount.draftkings.com/login?", timeout=30000)
            await asyncio.sleep(2)
            await page.click('button[id="login-submit"]')
            await asyncio.sleep(1)
            avatar = await page.query_selector('div[data-test-id="account-dropdown"]')
            maxct = 0
            while avatar is None:
                if maxct > 10:
                    await sendmsg("Draftkings: Unable to login", title="Login", color=16711680)
                    return
                maxct += 1
                await asyncio.sleep(1)
                avatar = await page.query_selector('div[data-test-id="account-dropdown"]')
            await sendmsg("Draftkings: Logged back in...", title="Login", color=65280)
            return False
    except Exception as e:
        print(f"Error in checklogin Draftkings: {e}")
        return False

async def cashoutlast(page: Page):
    global activebet
    try:
        if activebet is not None:
            with open("cashouts.txt", "a") as file:
                file.write(f"[{datetime.now().strftime('%H:%M:%S')}] DraftKings | {activebet.bet_name}\n")
                activebet = None
            await sendmsg2(title = "DraftKings: Attempting to cash out last bet", color=65280)
        await page.goto("https://sportsbook.draftkings.com/mybets")
        table = await page.wait_for_selector('sb-lazy-render[data-testid="sb-lazy-render"]')
        second_div = await table.wait_for_selector(':scope > div:nth-child(1) > div:nth-child(1)')
        latestbet = await second_div.wait_for_selector(':scope > div:nth-child(1)')
        cashout_button = await latestbet.wait_for_selector('button[data-test-id^="cashout-button"]')
        cashouttext = await cashout_button.inner_text()
        if "Cash Out Suspended" in cashouttext:
            await sendmsg2("DraftKings: Cash Out is suspended, unable to cash out", title="Cash Out", color=16711680, image_path=await captureimg(page))
            return
        await cashout_button.click()
        maxwait = 0
        while "Confirm" not in cashouttext:
            if maxwait > 10:
                await sendmsg2("DraftKings: Cash Out timed out", title="Cash Out", color=16711680, image_path=await captureimg(page))
                return
            maxwait += 1
            cashout_button = await latestbet.wait_for_selector('button[data-test-id^="cashout-button"]')
            cashouttext = await cashout_button.inner_text()
            await asyncio.sleep(0.25)
        await cashout_button.click()
        latestbet = await second_div.wait_for_selector(':scope > div:nth-child(1)')
        gettxt = await latestbet.wait_for_selector('div[data-test-id^="bet-details-status"]')
        cashouttext = await gettxt.inner_text()
        maxwait = 0
        while "CASHED OUT" not in cashouttext:
            if maxwait > 20:
                await sendmsg2(title = "DraftKings: Unable to confirm cashout", color=16711680, image_path=await captureimg(page))
                return
            maxwait += 1
            gettxt = await page.query_selector_all('div[data-test-id="bet-details"]')
            cashouttext = await gettxt[0].inner_text()
            await asyncio.sleep(1)

        getwager = await page.query_selector_all('span[data-test-id^="bet-stake"]')
        getwager = await getwager[0].text_content()
        getwager = getwager.replace("$", "").replace(",", "").replace("Wager: ", "").strip()

        getpaid = await page.query_selector_all('span[data-test-id^="bet-returns"]')
        getpaid = await getpaid[0].text_content()
        getpaid = getpaid.replace("$", "").replace(",", "").replace("Paid: ", "").strip()
        calculatecashout = round(float(getpaid) - float(getwager), 2)

        await sendmsg2(title = f"DraftKings: Cashout was confirmed!", msg=f"**Wager:** ${getwager}\n**Paid:** ${getpaid}\n**Net:** ${calculatecashout}", color=65280)
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
        "username": f"[{globals.instance}] Whale Arb - DraftKings",
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

async def sendmsg(msg = "", title="DraftKings", color=65280, url="", image_path=""):
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
        "username": f"[{globals.instance}] DraftKings Arb",
        "avatar_url": "https://images.crunchbase.com/image/upload/c_pad,f_auto,q_auto:eco,dpr_1/fyz4mydi8ceuovtoaooy"
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
       
