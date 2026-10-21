import time


class AlertManager:

    def __init__(self, cooldown_seconds=10):

        self.cooldown_seconds = cooldown_seconds

        self.last_alert_time = {}


    def should_alert(self, hazard):

        current_time = time.time()

        last_time = self.last_alert_time.get(hazard, 0)

        if current_time - last_time >= self.cooldown_seconds:

            self.last_alert_time[hazard] = current_time

            return True

        return False