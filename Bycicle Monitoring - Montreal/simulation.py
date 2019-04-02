"""Assignment 1 - Simulation

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto


=== Module Description ===

This file contains the Simulation class, which is the main class for your
bike-share simulation.

At the bottom of the file, there is a sample_simulation function that you
can use to try running the simulation at any time.
"""
import csv
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple

from bikeshare import Ride, Station
from container import PriorityQueue
from visualizer import Visualizer

# Datetime format to parse the ride data
DATETIME_FORMAT = '%Y-%m-%d %H:%M'


class Simulation:
    """Runs the core of the simulation through time.

    === Attributes ===
    all_rides:
        A list of all the rides in this simulation.
        Note that not all rides might be used, depending on the timeframe
        when the simulation is run.
    all_stations:
        A dictionary containing all the stations in this simulation.
    visualizer:
        A helper class for visualizing the simulation.
    active_rides:
        A list of all the rides in this simulation that are in progress.
    ride_pq:
        priorityquete of rides which are going to happen between simulation
        time.
    """
    all_stations: Dict[str, Station]
    all_rides: List[Ride]
    visualizer: Visualizer
    active_rides: List[Ride]
    rides_pq: PriorityQueue

    def __init__(self, station_file: str, ride_file: str) -> None:
        """Initialize this simulation with the given configuration settings.
        """
        self.all_stations = create_stations(station_file)
        self.all_rides = create_rides(ride_file, self.all_stations)
        self.active_rides = []
        self.rides_pq = PriorityQueue()
        self.visualizer = Visualizer()

    def run(self, start: datetime, end: datetime) -> None:
        """Run the simulation from <start> to <end>.
        """
        step = timedelta(minutes=1)  # Each iteration spans one minute of time
        for ride in self.all_rides:
            if start <= ride.start_time <= end:
                self.rides_pq.add(RideStartEvent(self, ride.start_time, ride))
            if (ride.start_time < start) and (ride.end_time >= start):
                ride.stats_decider = 0
                self.rides_pq.add(RideStartEvent(self, ride.start_time, ride))

        current = start  # current = current time of the simulation
        for ride in self.all_rides:
            # to add the rides which has been started before the simulation's
            # time and hasn't finished yet
            if ride.start_time < start < ride.end_time:
                self.active_rides.append(ride)
        while current <= end:
            self._update_active_rides_fast(current)
            self.visualizer.render_drawables(list(self.all_stations.values()) +
                                             list(self.active_rides), current)

            if current != start:
                # because 8:00 to 8:00 doens't include any doration
                self.availibility_checker(int(step.total_seconds()))
            # to calculate the low_availibility and low_unoccupied of each
            # station
            current += step

        # Leave this code at the very bottom of this method.
        # It will keep the visualization window open until you close
        # it by pressing the 'X'.
        while True:
            if self.visualizer.handle_window_events():
                return  # Stop the simulation

    def availibility_checker(self, duration: int) -> None:
        """ It changes the amount of low_availibility and low occupied amount
        of each station by the amount of duration( which in this case duration
        is always 60 seconds)"""
        for station in self.all_stations.values():
            if station.num_bikes <= 5:
                station.low_availability += duration
            if station.capacity - station.num_bikes <= 5:
                station.low_unoccupied += duration

    def _update_active_rides(self, time: datetime) -> None:
        """Update this simulation's list of active rides for the given time.

        REQUIRED IMPLEMENTATION NOTES:
        -   Loop through `self.all_rides` and compare each Ride's start and
            end times with <time>.

            If <time> is between the ride's start and end times (inclusive),
            then add the ride to self.active_rides if it isn't already in
            that list.

            Otherwise, remove the ride from self.active_rides if it is in
            that list.

        -   This means that if a ride started before the simulation's time
            period but ends during or after the simulation's time period,
            it should still be added to self.active_rides.

        - *** we use the attribiute'ride.allowance' to avoid adding the rides
                that couldn't happen at their start time due to the shortage of
                bikes in their station, at the other time between their start
                and end time.
        """
        for ride in self.all_rides:
            if ride.start_time <= time <= ride.end_time and\
                            ride not in self.active_rides and\
                            ride.allowance == 1:
                if ride.start.num_bikes < 1:
                    ride.allowance = 0  # therefor if the statoin that ride
                    # start from it doesn't have enought bikes when the start
                    # time arrives, the ride won't happen anymore( because of
                    # the change of the ride.allowace)
                else:
                    ride.start.num_bikes -= 1
                    ride.start.start_from += 1
                    ride.allowance = 0
                    self.active_rides.append(ride)
            if (not ride.start_time <= time <= ride.end_time) and\
                    (ride in self.active_rides):
                if ride.end.capacity >= ride.end.num_bikes + 1:
                    ride.end.num_bikes += 1
                    ride.end.end_in += 1
                # we're going to remove the bike at its endtime anyway but
                # if its station doesn't have enough spots it won't count for
                # the statistics.
                self.active_rides.remove(ride)

    def calculate_statistics(self) -> Dict[str, Tuple[str, float]]:
        """Return a dictionary containing statistics for this simulation.

        The returned dictionary has exactly four keys, corresponding
        to the four statistics tracked for each station:
          - 'max_start'
          - 'max_end'
          - 'max_time_low_availability'
          - 'max_time_low_unoccupied'

        The corresponding value of each key is a tuple of two elements,
        where the first element is the name (NOT id) of the station that has
        the maximum value of the quantity specified by that key,
        and the second element is the value of that quantity.

        For example, the value corresponding to key 'max_start' should be the
        name of the station with the most number of rides started at that
        station, and the number of rides that started at that station.
        """
        max_start: Station
        # The station which has maximum rides that start from it.
        max_end: Station
        # The statoin which has maximun rides that end in it.
        mtla: Station
        # The station which has the maximum time of low availibilty.
        mtlu: Station
        # The station which has the maximun time of low unoccupied.
        first_loop = True
        # using first_loop variable to give value to the
        #  {max_start, max_endd, mtla, mtlu} when the loop operates for the
        # first time, unless none of the if statements will occure.(cause the
        # variables don't have specific value)
        for station in self.all_stations.values():
            if first_loop is True:
                max_start = max_end = mtla = mtlu = station
                first_loop = False
            max_start = bigger(max_start, station, max_start.start_from,
                               station.start_from)

            max_end = bigger(max_end, station, max_end.end_in, station.end_in)

            mtla = bigger(mtla, station, mtla.low_availability,
                          station.low_availability)

            mtlu = bigger(mtlu, station, mtlu.low_unoccupied,
                          station.low_unoccupied)
        return {
            'max_start': (max_start.name, max_start.start_from),
            'max_end': (max_end.name, max_end.end_in),
            'max_time_low_availability': (mtla.name, mtla.low_availability),
            'max_time_low_unoccupied': (mtlu.name, mtlu.low_unoccupied)
        }

    def _update_active_rides_fast(self, time: datetime) -> None:
        """Update this simulation's list of active rides for the given time.

        REQUIRED IMPLEMENTATION NOTES:
        -   see Task 5 of the assignment handout
        """
        let = 0  # using let instead of syntax break, because when the first
        # event of our pq has not been occured because of the time, since our
        # pq has been sorted base on the event's time, therefore there is no
        # need to check other event so we do not need to check the others events
        # so we change the let to 1 to come out of the loop.
        while (self.rides_pq.is_empty() is False) and (let == 0):
            event = self.rides_pq.remove()
            if event.time > time:
                self.rides_pq.add(event)
                let = 1
            if time >= event.time:
                endevent = event.process()
                while endevent != []:
                    # because if our event is an EndRideEvent then its return's
                    # list is empty and there is no consequence event.
                    consequence_event = endevent.pop()
                    self.rides_pq.add(consequence_event)


def create_stations(stations_file: str) -> Dict[str, 'Station']:
    """Return the stations described in the given JSON data file.

    Each key in the returned dictionary is a station id,
    and each value is the corresponding Station object.
    Note that you need to call Station(...) to create these objects!

    Precondition: stations_file matches the format specified in the
                  assignment handout.

    This function should be called *before* _read_rides because the
    rides CSV file refers to station ids.
    """
    # Read in raw data using the json library.
    with open(stations_file) as file:
        raw_stations = json.load(file)

    stations = {}
    for s in raw_stations['stations']:
        # Extract the relevant fields from the raw station JSON.
        # s is a dictionary with the keys 'n', 's', 'la', 'lo', 'da', and 'ba'
        # as described in the assignment handout.
        # NOTE: all of the corresponding values are strings, and so you need
        # to convert some of them to numbers explicitly using int() or float().
        id_number = s['n']
        name = s['s']
#       print(id_number)
        capacity = (s['da'] + s['ba'])
        current = s['da']
        x = float(s['lo'])
        y = float(s['la'])
        stations[id_number] = Station((x, y), capacity, current, name)
    return stations


def create_rides(rides_file: str,
                 stations: Dict[str, 'Station']) -> List['Ride']:
    """Return the rides described in the given CSV file.

    Lookup the station ids contained in the rides file in <stations>
    to access the corresponding Station objects.

    Ignore any ride whose start or end station is not present in <stations>.

    Precondition: rides_file matches the format specified in the
                  assignment handout.
    """
    rides = []
    with open(rides_file) as file:
        for line in csv.reader(file):
            # line is a list of strings, following the format described
            # in the assignment handout.
            #
            # Convert between a string and a datetime object
            # using the function datetime.strptime and the DATETIME_FORMAT
            # constant we defined above. Example:
            # >>> datetime.strptime('2017-06-01 8:00', DATETIME_FORMAT)
            # datetime.datetime(2017, 6, 1, 8, 0)

            # To add the rides which only starts and ends in appropriate station
            if (line[1] in stations.keys()) and (line[3]) in stations.keys():

                start_stationid = stations[(line[1])]
                end_stationid = stations[(line[3])]
                start_datetime = datetime.strptime(line[0], DATETIME_FORMAT)
                end_datetime = datetime.strptime(line[2], DATETIME_FORMAT)
                rides.append(Ride(start_stationid, end_stationid,
                                  (start_datetime, end_datetime)))

    return rides


class Event:
    """An event in the bike share simulation.

    Events are ordered by their timestamp.
    === Attributes ===
    simultion:
        the simulation which the events are related to it
    time:
        the time which the event is going to happen

    """
    simulation: 'Simulation'
    time: datetime

    def __init__(self, simulation: 'Simulation', time: datetime) -> None:
        """Initialize a new event."""
        self.simulation = simulation
        self.time = time

    def __lt__(self, other: 'Event') -> bool:
        """Return whether this event is less than <other>.

        Events are ordered by their timestamp.
        """
        return self.time < other.time

    def process(self) -> List['Event']:
        """Process this event by updating the state of the simulation.

        Return a list of new events spawned by this event.
        """
        raise NotImplementedError


class RideStartEvent(Event):
    """An event corresponding to the start of a ride.
        the ride that happen on the specific time
        === (local)Attributes ===
        ride:
            the ride which the event is about it"""
    ride: 'Ride'

    def __init__(self, simulation: 'Simulation', time: datetime, ride: 'Ride'):
        """initialize a new RideStartEvent"""
        Event.__init__(self, simulation, time)
        self.ride = ride

    def process(self) -> List['Event']:
        """process the RideStartEvent by updating the statistics of the
         simulation.
        Return a list of new events spawned by this event.(which for
        this assignment particulary is only the RideEndEvent"""

        if (self.ride.start.num_bikes >= 1) and (self.ride.stats_decider == 1):
            self.ride.start.num_bikes -= 1
            self.ride.start.start_from += 1
            self.simulation.active_rides.append(self.ride)
            # we don't need to append it because since it's start time is
            # between start and end time of the simulation it has been
            # appended once to active_rides in the begining of the run

        return [RideEndEvent(self.simulation, self.ride.end_time, self.ride)]


class RideEndEvent(Event):
    """An event corresponding to the end of a ride.
    === (local)Attributes ===
        ride:
            the ride which the event is about it"""
    ride: 'Ride'

    def __init__(self, simulation: 'Simulation', time: datetime, ride: 'Ride'):
        """initialize a new RideEndEvent"""
        Event.__init__(self, simulation, time)
        self.ride = ride

    def process(self) -> List['Event']:
        """process the RideEndEvent by updating the statistics of the
                 simulation.
         Return a list of new events spawned by this event. which for this
         assignment is nothing therefore it returns a empty list"""
        if self.ride.end.capacity >= self.ride.end.num_bikes + 1:
            self.ride.end.num_bikes += 1
            self.ride.end.end_in += 1
        self.simulation.active_rides.remove(self.ride)  # it's out of if because
        # we need to remove the ride fraom active rides on their end time anyway

        return []


def sample_simulation() -> Dict[str, Tuple[str, float]]:
    """Run a sample simulation. For testing purposes only."""
    sim = Simulation('stations.json', 'sample_rides.csv')
    sim.run(datetime(2017, 6, 1, 8, 0, 0),
            datetime(2017, 6, 1, 9, 0, 0))
    return sim.calculate_statistics()


def alphasort(first: str, second: str) -> str:

    """Return the name which comes first
        alphabetically

    >>> print(alphasort('ababa','zaza'))
    ababa
    >>> print(alphasort('sepehr','john'))
    john
    >>> print(alphasort('hjh','aaa'))
    aaa
    >>> print(alphasort('aaaaaaa','aaaa'))
    aaaa
    >>> print(alphasort('12kii','sds'))
    12kii
    >>> print(alphasort('Berry','Evans'))
    Berry

        Return the shorter one if all the letters are same
    """
    for i in range(0, min(len(str(first)), len(str(second)))):
        if first[i] < second[i]:
            return first
        elif second[i] < first[i]:
            return second
    if len(str(first)) < (len(str(second))):
        return first
    else:
        return second


def bigger(station1: 'Station', station2: 'Station', number1: int,
           number2: int)-> 'Station':
    """ This function get 2 station with a correspanding attribute of each of
    them as an integer numbers and return the station with higher value of that
    attribute.
    If they were tie, it returns the station which it's name comes first in
    alphabetically order"""

    if number1 > number2:
        return station1

    if number1 < number2:
        return station2

    if number1 == number2:
        if station1.name == alphasort(station1.name, station2.name):
            return station1
        else:
            return station2


if __name__ == '__main__':
    # Uncomment these lines when you want to check your work using python_ta!
    import python_ta
    python_ta.check_all(config={
        'allowed-io': ['create_stations', 'create_rides'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'typing',
            'csv', 'datetime', 'json',
            'bikeshare', 'container', 'visualizer'
        ]
    })
    print(sample_simulation())
