import safetraxUtils
import requester
import urls
import time


class Safetrax:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.fullname = None
        self.nonce = None
        self.cnonce = None
        self.request = None
        self.dbName = "safetraxOpentxt"
        self.version = "1.0"
        self.requester = requester.Requesters()
        self.authToken = None
        self.userData = None
        self.employeeId = None
        self.oAuthHeaders = None  # headers to get the access token
        self.authHeaders = None  # headers that include the access token
        self.otp = None
        self.allOTPs = None
        self.boardingData = []

    def login(self):
        try:
            employeeData = safetraxUtils.getEmployeeDataFromJSON(self.username)
            self.authToken = employeeData['authToken']
            self.employeeId = employeeData['employeeId']
            self.fullname = employeeData['fullname']
            self.userData = employeeData['employeeData']
            self.oAuthHeaders = safetraxUtils.getOAuthHeader(
                self.dbName, self.authToken
            )

        except FileNotFoundError or e:
            print("Not able to find the token file generating new file")
            # get the authtoken
            self.__token_request(urls.ACCESS_TOKEN_URL)
            # write the details
            safetraxUtils.writeTokenIntoFile(self.username, self.authToken,self.employeeId,self.fullname,self.userData)
            print(f"[+] {self.username} details added successfully ")

    def __oauth_request(self, url):
        url = url if url else urls.NONCE_URL
        headers = {
            "Host": "opentext.safetrax.in",
            "Accept": "application/json",
            "User-Agent": "Commuter/7 CFNetwork/3826.500.131 Darwin/24.5.0",
            "Accept-Language": "en-IN,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
        }

        response = self.requester.get(url, headers)
        if type(response) != dict:
            self.nonce = safetraxUtils.getNonce(response.headers)
            self.cnonce = safetraxUtils.getCnonce(self.dbName)
            self.request = safetraxUtils.getRequest(
                self.username, self.dbName, self.password, self.cnonce, self.nonce
            )
            self.authHeaders = safetraxUtils.getAuthHeader(
                self.username,
                self.nonce,
                self.cnonce,
                self.dbName,
                self.version,
                self.request,
            )
        else:
            raise response["error"]

    def __token_request(self, url):
        if self.nonce == None and self.cnonce == None and self.request == None:
            self.__oauth_request(url)
        headers = self.authHeaders
        response = self.requester.post(url, headers=headers)
        if type(response) != dict:
            self.authToken = safetraxUtils.getAuthToken(response)
            self.userData = safetraxUtils.getUserData(response)
            self.employeeId = safetraxUtils.getEmployeeId(self.userData)
            self.fullname = safetraxUtils.getEmployeeFullName(self.userData)
            self.oAuthHeaders = safetraxUtils.getOAuthHeader(
                self.dbName, self.authToken
            )
            self.userDumpableData = response.text

        else:
            raise response["error"]

    def get_trip_details(self,employeeOnly=False):
        url = urls.GET_TRIP_URL
        payload = {
            "employees._employeeId": self.employeeId,
            "startTime": {"$lte": round(time.time()) * 1000 + 86400000, "$gte": round(time.time()) * 1000 - 86400000 },
        }
        headers = self.oAuthHeaders
        response = self.requester.post(url, headers=headers, payload=payload)
        if type(response) != dict:
            self.boardingData = safetraxUtils.getBoardingData(self.fullname, response, employeeOnly)
            return self.boardingData
        else:
            raise response["error"]
    
    def sendBoardingDataToTelegram(self,chatId,botToken):
        url = urls.TELEGRAM_SEND_MESSAGE_URL.format(botToken)
        payload = (
            f"chat_id={chatId}&"+
            f"text={safetraxUtils.parseBoardingDataForTelegram(self.boardingData)}&"+
            f"parse_mode=html"
        )
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = self.requester.get(url, headers=headers, payload=payload)

        print(response.text)
