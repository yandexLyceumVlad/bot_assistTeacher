import datetime as dt
import json



class Event:
    week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    count_event = 0

    def encode_time(t):
        temp = dt.datetime.strftime(t, "%H:%M").split(":")
        return int(temp[0]) * 60 + int(temp[1])

    def duration_to_string(d):
        return str(d // 60) + ":" + str(d % 60)

    def time_interval(t1, t2):
        #print(t1.time, t2.time)
        t1_ = Event.encode_time(t1.time) + t1.duration
        t2_ = Event.encode_time(t2.time)
        return max(0, t2_ - t1_)

    def __init__(self, name, date, time, duration = 60, link="", comment="", period=[]):
        self.name = name
        self.date = date
        self.time = time
        self.link = link
        #Event.count_event += 1
        #self.id = Event.count_event
        self.duration = duration
        self.period = period
        self.comment = comment

    def __str__(self):
        return str(self.__dict__)


    def __eq__(self,y):
        if self.name == y.name \
                and self.date == y.date \
                and self.link == y.link and \
                self.time == y.time:
            return  True
        return False


class Busy:
    def __init__(self):
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def filter_day(self, day):
        rez = []
        for e in self.events:
            #date_busy = dt.datetime.strftime(e.date, '%d.%m.%Y').date()
            date_busy = e.date
#            date_user = day.toPyDate()
            date_user = day
            if date_busy == date_user:
                rez.append(e)
        #rez.sort(key=(lambda x: Event.encode_time(x.time)))
        rez.sort(key=(lambda x: x.time))
        return rez

    def replace(self, e1, e2):
        try:
            ind = self.find_event(e1)
            self.events[ind] = e2
        except:
            print("не заменилось")

    def find_event(self, ev):
        for ind, e in enumerate(self.events):
            if e == ev:
                return ind
        return None

    def del_event(self, event):
        # ind = self.find_event()
        # if ind is not None:
        #     self.events.
        try:
            self.events.remove(event)
            #self.save()
        except:
            print("не удалилось")

    def get_today(self, day=None):
        if day is None:
            day = dt.date.today()
        temp_events = self.filter_day(day)
        return temp_events

    def encode_json(self):
        return [i.__dict__ for i in self.events]

    def all(self):
        return self.events

    def save(self):
        try:
            with open("calendar.json", "w", encoding="utf-8") as file:
                #json.dump(self, file, default=encode_json)
                json.dump(self.encode_json(), file)
        except:
            print("Не удалось записать в файл")

    def load(self):
        try:
            with open("calendar.json", "r", encoding="utf-8") as file:
                #json.dump(self, file, default=encode_json)
                temp = json.load(file)
                self.events = [Event(t['name'], t['date'], t['time'], t['duration'], t['link'], t['comment'], t['period']) for t in temp]
                #print(temp)
        except:
            print("Не удалось считать из файла")

    def __str__(self):
        return "\nВсе события:\n"+"\n".join([str(e) for e in self.events])
