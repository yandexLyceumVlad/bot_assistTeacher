import datetime

#print(datetime.datetime.strptime("11:50", "%H:%M").time())

when_alarm = (datetime.datetime.strptime("03.03.2022 10:50", "%d.%m.%Y %H:%M") - datetime.datetime.now()).total_seconds()
print(when_alarm)