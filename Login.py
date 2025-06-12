from safetraxMobile import Safetrax

# create a user
implaweee = Safetrax("your user id", "safetrax password")

#login
implaweee.login()

#get the trip details
implaweee.get_trip_details()


chatId = "get your telegram chat id"
botToken = "get your bottoken"

#send the otps via telegram
implaweee.sendBoardingDataToTelegram(chatId,botToken)

