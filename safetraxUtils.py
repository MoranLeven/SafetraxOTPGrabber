import re
import time
import hashlib
import json
from urllib.parse import quote
from datetime import datetime

def getNonce(headers):
    wwwAuthen = headers.get("WWW-Authenticate")
    wwwAuthenDict = dict(re.findall(r'(\w+)="([^"]+)"', wwwAuthen))
    return wwwAuthenDict["oauth_nonce"]


def getCnonce(dbName):
    return digest(f"{time.time() * 1000}{dbName}")


def getRequest(username, dbname, password, cnonce, nonce):
    return digest(f"{digest(f'{username}:{dbname}:{password}:{cnonce}')}:{nonce}")


def digest(s):
    try:
        md5 = hashlib.md5()
        md5.update(s.encode())
        digest_bytes = md5.digest()
        hex_str = "".join(["{:02x}".format(b & 0xFF) for b in digest_bytes])
        return hex_str
    except Exception:
        raise Exception("Cannot encode credentials")


def getAuthHeader(username, nonce, cnonce, realm, version, request):
    headers = {
        "Host": "opentext.safetrax.in",
        "Connection": "keep-alive",
        "Accept": "application/json",
        "User-Agent": "Commuter/7 CFNetwork/3826.500.131 Darwin/24.5.0",
        "Accept-Language": "en-IN,en;q=0.9",
        "Content-Type": "application/json; charset=UTF-8",
    }
    authorization = (
        f"OAuth oauth_username={username},"
        + f"oauth_nonce={nonce},"
        + f"oauth_cnonce={cnonce},"
        + f"oauth_realm={realm},"
        + f"oauth_version={version},"
        + f"oauth_request={request}"
    )
    headers["Authorization"] = authorization
    return headers


def getOAuthHeader(dbname, authToken):
    headers = {
        "Host": "opentext.safetrax.in",
        "Connection": "keep-alive",
        "Accept": "application/json",
        "User-Agent": "Commuter/7 CFNetwork/3826.500.131 Darwin/24.5.0",
        "Accept-Language": "en-IN,en;q=0.9",
        "Content-Type": "application/json; charset=UTF-8",
    }
    authorization = f"OAuth oauth_realm={dbname},oauth_token={authToken}"
    headers["Authorization"] = authorization
    return headers


def getAuthToken(response):
    parsedResponse = json.loads(response.text)
    return parsedResponse["accessToken"]


def getUserData(response):
    return json.loads(response.text)


def getEmployeeId(userData):
    return userData["userInfo"]["_referenceId"]["$oid"]


def getEmployeeDataFromJSON(name):
    try:
        with open(f"{name}_data.json","r") as rawFileData:
            parseFileData = json.loads(rawFileData.read())
            return parseFileData
    except:
        raise FileNotFoundError


def writeTokenIntoFile(filename, authToken, employeeId, fullname, employeeData):
    employeeDataDict = {
        "authToken": authToken,
        "employeeId": employeeId,
        "fullname": fullname,
        "employeeData": employeeData,
    }

    writeTokenFile = open(f"{filename}_data.json", "w")
    writeTokenFile.write(json.dumps(employeeDataDict))
    writeTokenFile.close()


def getEmployeeFullName(userdata):
    return userdata["userInfo"]["fullName"]


def parseBoardingDataForTelegram(boardingData):
    otpMorningMessage = ""
    otpEveningMessage = ""
    eveningDate = 0
    morningDate = 0
    for rosterData in boardingData['roosterBoardingData']:
        if "eveningRosterOTPs" == rosterData:
            eveningDate = boardingData['roosterBoardingData']['eveningRosterDate']
            for employeeOTPData in boardingData['roosterBoardingData'][rosterData]:
                otpEveningMessage += f"{employeeOTPData['Name']} :: <code>{employeeOTPData['OTP']}</code> \n"
        elif "morningRoosterOTPs" == rosterData:
            morningDate = boardingData['roosterBoardingData']['morningRosterDate']
            for employeeOTPData in boardingData['roosterBoardingData'][rosterData]:
                otpMorningMessage += f"{employeeOTPData['Name']} :: <code>{employeeOTPData['OTP']}</code> \n"
    
    finalMessage = f'''
    
    {"🚕Login Boarding..." + morningDate.strftime("%d-%m-%Y") if otpMorningMessage else ""}
{otpMorningMessage}
    
{"👋Logout Boarding..." + eveningDate.strftime("%d-%m-%Y") if otpEveningMessage else ""}
{otpEveningMessage}
    
    '''
    
    return quote(finalMessage)


def getBoardingData(username, response, onlyEmployeeBoardingData=False):

    employeeName = username
    rawData = response.text
    tripParsedData = json.loads(rawData)
    morningOTP = None
    morningOTPSecondary = None
    eveningOTP = None
    eveningOTPSecondary = None

    morningRoosterOTPs = []
    eveningRosterOTPs = []
    morningRosterDate = 0
    eveningRosterDate = 0
    # get the otps
    for trip in tripParsedData:
        tripEmployees = trip["employees"]
        for employeeData in tripEmployees:
            if employeeData["travelFor"] == "login":
                if not morningRosterDate:
                    morningRosterDate = datetime.fromtimestamp(trip['scheduleDate']//1000)
                
                morningRoosterOTPs.append(
                    {
                        "Name": employeeData["fullName"],
                        "OTP": employeeData["pin"],
                        "SecondarOTP": employeeData["secondaryPin"],
                    }
                )
                if employeeData["fullName"] == employeeName:
                    morningOTP = employeeData["pin"]
                    morningOTPSecondary = employeeData["secondaryPin"]
            elif employeeData["travelFor"] == "logout":
                if not eveningRosterDate:
                    eveningRosterDate = datetime.fromtimestamp(trip['scheduleDate']//1000)
                eveningRosterOTPs.append(
                    {
                        "Name": employeeData["fullName"],
                        "OTP": employeeData["pin"],
                        "SecondarOTP": employeeData["secondaryPin"],
                    }
                )
                if employeeData["fullName"] == employeeName:
                    eveningOTP = employeeData["pin"]
                    eveningOTPSecondary = employeeData["secondaryPin"]

    boardingData = {"employeeBoardingData": {}, "roosterBoardingData": {}}

    # add the user data first
    if morningOTP:
        boardingData["employeeBoardingData"]["morningOTP"] = morningOTP

    if morningOTPSecondary:
        boardingData["employeeBoardingData"][
            "morningSecondaryOTP"
        ] = morningOTPSecondary

    if eveningOTP:
        boardingData["employeeBoardingData"]["eveningOTP"] = eveningOTP

    if eveningOTPSecondary:
        boardingData["employeeBoardingData"][
            "eveningSecondaryOTP"
        ] = eveningOTPSecondary

    # add the roster data now

    if morningRoosterOTPs:
        boardingData["roosterBoardingData"]["morningRoosterOTPs"] = morningRoosterOTPs
        boardingData['roosterBoardingData']['morningRosterDate'] = morningRosterDate
        

    if eveningRosterOTPs:
        boardingData["roosterBoardingData"]["eveningRosterOTPs"] = eveningRosterOTPs
        boardingData['roosterBoardingData']['eveningRosterDate'] = eveningRosterDate

    return (
        boardingData["employeeBoardingData"]
        if onlyEmployeeBoardingData
        else boardingData
    )
