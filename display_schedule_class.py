from schedule_class import *


class Display_event(Event):
    def display(self):
        block_start = ""  # r"_____________\n" #r'<span style="color:blue">'
        block_end = ""  # r"______________\n" #r'</span>'
        # return block_start + "dfb"+ block_end
        line = block_start + f"*{self.date} {self.time}* \n {self.name}"
        if self.link:  line += f"\n {self.link}"
        if self.comment: line += f"\n{self.comment}"
        return line + block_end

    def display_date_time(self):
        return f"*{self.date} {self.time}"


class Display_busy(Busy):
    def display_all_events(self):
        return self.display_events(self.events)

    def display_today(self):
        return self.display_events(self.get_today())

    def display_tomorrow(self):
        tomorrow = dt.date.today() + dt.timedelta(days=1)
        return self.display_events(self.filter_day(tomorrow))

    def display_events(self, list_events):
        line = ""
        for b in list_events:
            line += b.display() + "\n\n"
        return line
