from datetime import datetime,timedelta
import fitparse

# stores record fields and throws error if any required fields are missing
class RecordData:
    def __init__(self, message: fitparse.DataMessage):
        # timestamp stored in utc
        self.timestamp: datetime.DateTime = message.get_value("timestamp")
        self.distance: float              = message.get_value("distance")
        self.enhanced_speed: float        = message.get_value("enhanced_speed")
        self.speed: float                 = message.get_value("speed")
        self.heart_rate: int              = message.get_value("heart_rate")
        self.cadence: int                 = message.get_value("cadence")
        self.fractional_cadence: float    = message.get_value("fractional_cadence")

        # sometimes missing 
        self.enhanced_altitude: float     = message.get_value("enhanced_altitude")
        self.altitude: float              = message.get_value("altitude")
        self.position_long: int           = message.get_value("position_long")
        self.position_lat: int            = message.get_value("position_lat")

        # check required fields are present
        if any(v is None for v in [self.timestamp, self.distance, self.enhanced_speed, 
                                   self.speed, self.heart_rate, self.cadence, self.fractional_cadence]):
            raise ValueError(f"message is missing required fields: {[i for i in vars(self).keys() if vars(self)[i] is None]}")

        self._message = message

    def __repr__(self):
        # omit the private message variable
        data_string = str({k:v for k,v in vars(self).items() if k!="_message"})[1:-1]
        return f"<RecordData: {data_string}>"


# lap record data where error thrown if any required fields are missing
class LapData:
    def __init__(self, message: fitparse.DataMessage):
        # timings - note datetimes stored in utc
        self.timestamp: datetime.DateTime  = message.get_value("timestamp")
        self.start_time: datetime.DateTime = message.get_value("start_time")
        self.total_elapsed_time: float     = message.get_value("total_elapsed_time")
        self.total_timer_time: float       = message.get_value("total_timer_time")

        # positions and distance
        self.start_position_lat: int  = message.get_value("start_position_lat") # sometimes missing
        self.start_position_long: int = message.get_value("start_position_long") # sometimes missing
        self.total_distance: float    = message.get_value("total_distance")
        self.total_ascent: int        = message.get_value("total_ascent") # sometimes missing
        self.total_descent: int       = message.get_value("total_descent") # sometimes missing

        # body metrics
        self.total_strides: int            = message.get_value("total_strides")
        self.total_calories: int           = message.get_value("total_calories")
        self.enhanced_avg_speed: float     = message.get_value("enhanced_avg_speed")
        self.avg_speed: float              = message.get_value("avg_speed")
        self.enhanced_max_speed: float     = message.get_value("enhanced_max_speed")
        self.max_speed: float              = message.get_value("max_speed")
        self.avg_heart_rate: float         = message.get_value("avg_heart_rate")
        self.max_heart_rate: int           = message.get_value("max_heart_rate")
        self.avg_running_cadence: int      = message.get_value("avg_running_cadence") 
        self.max_running_cadence: int      = message.get_value("max_running_cadence")
        self.avg_fractional_cadence: float = message.get_value("avg_fractional_cadence")
        self.max_fractional_cadence: float = message.get_value("max_fractional_cadence")

        # check required fields present
        required_fields = [vars(self)[i] for i in vars(self).keys() if i not in ["start_position_lat", "start_position_long","total_ascent","total_descent"]]
        if any(v is None for v in required_fields):
            raise ValueError(f"message is missing required fields: {[i for i in vars(self).keys() if vars(self)[i] is None]}")

        self._message = message

    def __repr__(self):
        # omit the private message variable
        data_string = str({k:v for k,v in vars(self).items() if k!="_message"})[1:-1]
        return f"<LapData: {data_string}>"

    def summarise(self) -> str:
        # TODO: here we should deal with units https://github.com/hgrecco/pint
        
        distance = round(self.total_distance/1000,2)
        duration = timedelta(seconds=round(self.total_timer_time))
        pace = timedelta(seconds=round(1000/self.enhanced_avg_speed))

        out = f"""start time: {self.start_time} 
end time: {self.timestamp}
duration: {duration}
distance: {distance}km
pace: {pace}/km
calories: {self.total_calories}kCal
average hr: {self.avg_heart_rate}bpm
max hr: {self.max_heart_rate}bpm
cadence: {self.avg_running_cadence * 2}spm
"""
        return out


# stores the important fields for a session entry, and
# throws error if any of the fields are not present
class SessionData(LapData):
    def __init__(self, message: fitparse.DataMessage):
        super().__init__(message)

        self.total_training_effect = message.get_value("total_training_effect")
        self.total_anaerobic_training_effect = message.get_value("total_anaerobic_training_effect")

        if self.total_training_effect is None or self.total_anaerobic_training_effect is None:
            raise ValueError(f"message is missing required fields: {[i for i in vars(self).keys() if vars(self)[i] is None]}")

    def __repr__(self):
        # omit the private message variable
        data_string = str({k:v for k,v in vars(self).items() if k!="_message"})[1:-1]
        return f"<SessionData: {data_string}>"

    def summarise(self) -> str:
        out = f"""aerobic training effect: {self.total_training_effect}/5
anaerobic training effect: {self.total_anaerobic_training_effect}/5
"""
        return super().summarise() + out


# monitoring data
class MonitoringData():
    def __init__(self):
        pass