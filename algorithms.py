"""CSC148 Assignment 1 - Algorithms

=== CSC148 Fall 2018 ===
Department of Computer Science,
University of Toronto

=== Module Description ===

This file contains two sets of algorithms: ones for generating new arrivals to
the simulation, and ones for making decisions about how elevators should move.

As with other files, you may not change any of the public behaviour (attributes,
methods) given in the starter code, but you can definitely add new attributes
and methods to complete your work here.

See the 'Arrival generation algorithms' and 'Elevator moving algorithsm'
sections of the assignment handout for a complete description of each algorithm
you are expected to implement in this file.
"""
import csv
from enum import Enum
import random
from typing import Dict, List, Optional

from entities import Person, Elevator


###############################################################################
# Arrival generation algorithms
###############################################################################
class ArrivalGenerator:
    """An algorithm for specifying arrivals at each round of the simulation.

    === Attributes ===
    max_floor: The maximum floor number for the building.
               Generated people should not have a starting or target floor
               beyond this floor.
    num_people: The number of people to generate, or None if this is left
                up to the algorithm itself.

    === Representation Invariants ===
    max_floor >= 2
    num_people is None or num_people >= 0
    """
    max_floor: int
    num_people: Optional[int]

    def __init__(self, max_floor: int, num_people: Optional[int]) -> None:
        """Initialize a new ArrivalGenerator.

        Preconditions:
            max_floor >= 2
            num_people is None or num_people >= 0
        """
        self.max_floor = max_floor
        self.num_people = num_people

    def generate(self, round_num: int) -> Dict[int, List[Person]]:
        """Return the new arrivals for the simulation at the given round.

        The returned dictionary maps floor number to the people who
        arrived starting at that floor.

        You can choose whether to include floors where no people arrived.
        """
        raise NotImplementedError


class RandomArrivals(ArrivalGenerator):
    """Generate a fixed number of random people each round.

    Generate 0 people if self.num_people is None.

    For our testing purposes, this class *must* have the same initializer header
    as ArrivalGenerator. So if you choose to to override the initializer, make
    sure to keep the header the same!

    Hint: look up the 'sample' function from random.
    """

    def generate(self, round_num: int) -> Dict[int, List[Person]]:
        res = {}
        for i in range(1, self.max_floor + 1):
            res[i] = []
        for i in range(self.num_people):
            start = random.randint(1, self.max_floor)
            target = random.randint(1, self.max_floor)
            while start == target:
                start = random.randint(1, self.max_floor)
            res[start].append(Person(start, target))
        return res


class FileArrivals(ArrivalGenerator):
    """Generate arrivals from a CSV file.
    """
    arrival_dict: Dict[int, List]
    max_floor: int

    def __init__(self, max_floor: int, filename: str) -> None:
        """Initialize a new FileArrivals algorithm from the given file.

        The num_people attribute of every FileArrivals instance is set to None,
        since the number of arrivals depends on the given file.

        Precondition:
            <filename> refers to a valid CSV file, following the specified
            format and restrictions from the assignment handout.
        """
        ArrivalGenerator.__init__(self, max_floor, None)
        self.arrival_dict = {}
        self.max_floor = max_floor
        with open(filename) as csvfile:
            reader = csv.reader(csvfile)
            for line in reader:
                num_lst = []
                for str1 in line:
                    num_lst.append(int(str1))
                num_round = num_lst.pop(0)
                self.arrival_dict[num_round] = num_lst

    def generate(self, round_num: int) -> Dict[int, List[Person]]:
        """Generate a Dict in which each floor index is corresponding to a list
        of person that arrived at this floor with the given file.
        """
        res = {}
        for floor in range(1, self.max_floor + 1):
            res[floor] = []
        round_arrival = self.arrival_dict.get(round_num, [])
        for people in range(int(len(round_arrival)/2)):
            start = round_arrival[people*2]
            target = round_arrival[people*2+1]
            res[start] = res.get(start, []) + [Person(start, target)]
        return res


###############################################################################
# Elevator moving algorithms
###############################################################################
class Direction(Enum):
    """
    The following defines the possible directions an elevator can move.
    This is output by the simulation's algorithms.

    The possible values you'll use in your Python code are:
        Direction.UP, Direction.DOWN, Direction.STAY
    """
    UP = 1
    STAY = 0
    DOWN = -1


class MovingAlgorithm:
    """An algorithm to make decisions for moving an elevator at each round.
    """
    def move_elevators(self,
                       elevators: List[Elevator],
                       waiting: Dict[int, List[Person]],
                       max_floor: int) -> List[Direction]:
        """Return a list of directions for each elevator to move to.

        As input, this method receives the list of elevators in the simulation,
        a dictionary mapping floor number to a list of people waiting on
        that floor, and the maximum floor number in the simulation.

        Note that each returned direction should be valid:
            - An elevator at Floor 1 cannot move down.
            - An elevator at the top floor cannot move up.
        """
        raise NotImplementedError


class RandomAlgorithm(MovingAlgorithm):
    """A moving algorithm that picks a random direction for each elevator.
    """
    def move_elevators(self,
                       elevators: List[Elevator],
                       waiting: Dict[int, List[Person]],
                       max_floor: int) -> List[Direction]:
        """Return a list of directions for each elevator to move to according to
        the RandomAlgorithm."""
        res = []
        for elevator in elevators:
            if elevator.location == 1:
                rdm = random.randint(0, 1)
            elif elevator.location == max_floor:
                rdm = random.randint(-1, 0)
            else:
                rdm = random.randint(-1, 1)
            if rdm == 1:
                res.append(Direction.UP)
            elif rdm == 0:
                res.append(Direction.STAY)
            else:
                res.append(Direction.DOWN)
        return res


class PushyPassenger(MovingAlgorithm):
    """A moving algorithm that preferences the first passenger on each elevator.

    If the elevator is empty, it moves towards the *lowest* floor that has at
    least one person waiting, or stays still if there are no people waiting.

    If the elevator isn't empty, it moves towards the target floor of the
    *first* passenger who boarded the elevator.
    """
    def move_elevators(self,
                       elevators: List[Elevator],
                       waiting: Dict[int, List[Person]],
                       max_floor: int) -> List[Direction]:
        """Return a list of directions for each elevator to move to according to
        the PushyPassenger algorithm."""
        res = []
        lowest = find_lowest(waiting, max_floor)

        for elevator in elevators:
            if len(elevator.passengers) == 0:
                if lowest == 0:
                    res.append(Direction.STAY)
                elif elevator.location > lowest:
                    res.append(Direction.DOWN)
                else:
                    res.append(Direction.UP)
            else:
                first_passenger = elevator.passengers[0]
                if first_passenger.target > elevator.location:
                    res.append(Direction.UP)
                elif first_passenger.target < elevator.location:
                    res.append(Direction.DOWN)
        return res


class ShortSighted(MovingAlgorithm):
    """A moving algorithm that preferences the closest possible choice.

    If the elevator is empty, it moves towards the *closest* floor that has at
    least one person waiting, or stays still if there are no people waiting.

    If the elevator isn't empty, it moves towards the closest target floor of
    all passengers who are on the elevator.

    In this case, the order in which people boarded does *not* matter.
    """

    def move_elevators(self,
                       elevators: List[Elevator],
                       waiting: Dict[int, List[Person]],
                       max_floor: int) -> List[Direction]:
        """Return a list of directions for each elevator to move to according to
                the ShortSighted algorithm."""
        res = []
        # Get waiting floors
        waiting_floor = []
        for floor in waiting:
            if len(waiting[floor]) != 0:
                waiting_floor.append(floor)
        for elevator in elevators:
            if len(elevator.passengers) == 0:
                if len(waiting_floor) == 0:
                    res.append(Direction.STAY)
                else:
                    closest = _find_closest(elevator.location, waiting_floor)
                    if closest < elevator.location:
                        res.append(Direction.DOWN)
                    if closest > elevator.location:
                        res.append(Direction.UP)
            else:
                target_floor = []
                for passenger in elevator.passengers:
                    # Get a list of target floors of all the passengers in the
                    # elevator.
                    target_floor.append(passenger.target)
                closest = _find_closest(elevator.location, target_floor)
                if closest < elevator.location:
                    res.append(Direction.DOWN)
                if closest > elevator.location:
                    res.append(Direction.UP)
        return res


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-io': ['__init__'],
        'extra-imports': ['entities', 'random', 'csv', 'enum'],
        'max-nested-blocks': 4,
        'disable': ['R0201']
    })


def find_lowest(waiting: Dict[int, List[Person]], max_floor: int) -> int:
    """find the lowest floor that has people waiting for elevators.
    """
    lowest = 0
    floor = 1
    while lowest == 0 and floor <= max_floor:
        if len(waiting[floor]) > 0:
            lowest = floor
        floor += 1
    return lowest


def _find_closest(current, floor_has_people) -> int:
    """find the closest floor with people waiting to the floor this elevator is
    at.
    """
    floor_has_people.sort()
    minimum = None
    distance = None
    for floor in floor_has_people:
        if minimum is None:
            minimum = floor
            distance = abs(current - floor)
        else:
            temp = abs(current - floor)
            if temp < distance:
                minimum = floor
                distance = temp
    return minimum
