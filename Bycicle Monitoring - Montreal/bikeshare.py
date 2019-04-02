"""Assignment 1 - Bike-share objects

=== CSC148 Fall 2017 ===
Diane Horton and David Liu
Department of Computer Science,
University of Toronto


=== Module Description ===

This file contains the Station and Ride classes, which store the data for the
objects in this simulation.

There is also an abstract Drawable class that is the superclass for both
Station and Ride. It enables the simulation to visualize these objects in
a graphical window.
"""
from datetime import datetime
from typing import Tuple


# Sprite files
STATION_SPRITE = 'stationsprite.png'
RIDE_SPRITE = 'bikesprite.png'


class Drawable:
    """A base class for objects that the graphical renderer can be drawn.

    === Public Attributes ===
    sprite:
        The filename of the image to be drawn for this object.
    """
    sprite: str

    def __init__(self, sprite_file: str) -> None:
        """Initialize this drawable object with the given sprite file.
        """
        self.sprite = sprite_file

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this object at the given time.
        """
        raise NotImplementedError


class Station(Drawable):
    """A Bixi station.

    === Public Attributes ===
    capacity:
        the total number of bikes the station can store
    location:
        the location of the station in long/lat coordinates
        **UPDATED**: make sure the first coordinate is the longitude,
        and the second coordinate is the latitude.
    name: str
        name of the station
    num_bikes: int
        current number of bikes at the station
    start_from: int
        number of the rides which started from the station
    end_in: int
        number of the rides which finished in the station
    low availability: int
        The total amount of time during the simulation, in seconds,
        that the station spent with at most five bikes available
    low unoccupied: int
        The total amount of time during the simulation, in seconds,
         that the station spent with at most five unoccupied spots



    === Representation Invariants ===
    - 0 <= num_bikes <= capacity
    """
    name: str
    location: Tuple[float, float]
    capacity: int
    num_bikes: int
    start_from: int
    end_in: int
    low_availability: int
    low_unoccupied: int

    def __init__(self, pos: Tuple[float, float], cap: int,
                 num_bikes: int, name: str) -> None:
        """Initialize a new station.

        Precondition: 0 <= num_bikes <= cap
        """
        self.location = pos
        self.capacity = cap
        self.num_bikes = num_bikes
        self.name = name
        self.start_from = self.end_in = 0
        self.low_unoccupied = 0
        self.low_availability = 0
        Drawable.__init__(self, STATION_SPRITE)

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this station for the given time.

        Note that the station's location does *not* change over time.
        The <time> parameter is included only because we should not change
        the header of an overridden method.
        """
        return self.location


class Ride(Drawable):
    """A ride using a Bixi bike.

    === Attributes ===
    start:
        the station where this ride starts
    end:
        the station where this ride ends
    start_time:
        the time this ride starts
    end_time:
        the time this ride ends
    allowance:
        we use and change this attribute when we're updating active rides via
        _uptade_active_rides
        It's either 1 or 0
            if it's 1 = ride can happens
            if it's 0 = ride can't happen(because for instance at the
            start time its station doesn't have enough bikes,...)
    stats_decider:
        we use and change this attribute where we're updating active rides via
        _uptae_active_rides_fast
        it's either 1 or 0:
            if it's 1: it counts for any statistics.(both start_from and end_in)
            if it's 0: it happen for the rides which starts before the
            simulations start time therefore it doesn't count for the start_from
            station statics but if it end within the simulation time, it will
            count for end_in statics.
    === Representation Invariants ===
    - start_time < end_time
    """
    start: Station
    end: Station
    start_time: datetime
    end_time: datetime
    allowance: int

    def __init__(self, start: Station, end: Station,
                 times: Tuple[datetime, datetime]) -> None:
        """Initialize a ride object with the given start and end information.
        """
        self.start, self.end = start, end
        self.allowance = 1
        self.start_time, self.end_time = times[0], times[1]
        Drawable.__init__(self, RIDE_SPRITE)
        self.stats_decider = 1

    def get_position(self, time: datetime) -> Tuple[float, float]:
        """Return the (long, lat) position of this ride for the given time.

        A ride travels in a straight line between its start and end stations
        at a constant speed.
        """
        duration = self.end_time - self.start_time
        duration = duration.total_seconds()
        # total time that the ride takes to reach its end from the start
        x_distance = self.end.location[0] - self.start.location[0]
        y_distance = self.end.location[1] - self.start.location[1]
#       distance = sqrt((x_distance ** 2) + (y_distance ** 2))
        speed_x = x_distance / duration
        # speed of the bike base on x-axis
        speed_y = y_distance / duration
        # speed of the bike base on y-axis
        time_passed = time - self.start_time
        time_passed = time_passed.total_seconds()
        # the time that has been passed since the ride has been started(seconds)
        return (self.start.location[0] + speed_x * time_passed,
                self.start.location[1] + speed_y * time_passed)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'typing',
            'datetime'
        ],
        'max-attributes': 15
    })
