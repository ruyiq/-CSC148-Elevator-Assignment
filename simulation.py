"""CSC148 Assignment 1 - Simulation

=== CSC148 Fall 2018 ===
Department of Computer Science,
University of Toronto

=== Module description ===
This contains the main Simulation class that is actually responsible for
creating and running the simulation. You'll also find the function `sample_run`
here at the bottom of the file, which you can use as a starting point to run
your simulation on a small configuration.

Note that we have provided a fairly comprehensive list of attributes for
Simulation already. You may add your own *private* attributes, but should not
remove any of the existing attributes.
"""
# You may import more things from these modules (e.g., additional types from
# typing), but you may not import from any other modules.
from typing import Dict, List, Any

import algorithms
from entities import Person, Elevator
from visualizer import Visualizer


class Simulation:
    """The main simulation class.

    === Attributes ===
    arrival_generator: the algorithm used to generate new arrivals.
    elevators: a list of the elevators in the simulation.
    moving_algorithm: the algorithm used to decide how to move elevators.
    num_floors: the number of floors.
    visualizer: the Pygame visualizer used to visualize this simulation.
    waiting: a dictionary of people waiting for an elevator.
             (keys are floor numbers, values are the list of waiting people)
    all_finished: a list of all passengers reached their target floor in
                  this simulation.

    === Representation invariants ===
    num_floors >= 2
    num_elevators >= 1
    """
    arrival_generator: algorithms.ArrivalGenerator
    elevators: List[Elevator]
    moving_algorithm: algorithms.MovingAlgorithm
    num_floors: int
    visualizer: Visualizer
    waiting: Dict[int, List[Person]]
    all_finished: List[Person]

    def __init__(self,
                 config: Dict[str, Any]) -> None:
        """Initialize a new simulation using the given configuration."""

        self.num_floors = config['num_floors']
        self.elevators = []
        for _ in range(config['num_elevators']):
            self.elevators.append(Elevator(config['elevator_capacity']))
        self.moving_algorithm = (config['moving_algorithm'])
        self.arrival_generator = (config['arrival_generator'])
        self.waiting = {}
        for floor in range(1, self.num_floors + 1):
            self.waiting[floor] = []
        self.all_finished = []
        self.visualizer = Visualizer(self.elevators,
                                     self.num_floors,
                                     config['visualize'])

    ############################################################################
    # Handle rounds of simulation.
    ############################################################################
    def run(self, num_rounds: int) -> Dict[str, Any]:
        """Run the simulation for the given number of rounds.

        Return a set of statistics for this simulation run, as specified in the
        assignment handout.

        Precondition: num_rounds >= 1.

        Note: each run of the simulation starts from the same initial state
        (no people, all elevators are empty and start at floor 1).
        """
        for i in range(num_rounds):

            self.visualizer.render_header(i)

            # Stage 1: generate new arrivals
            self._generate_arrivals(i)

            # Stage 2: leave elevators
            self._handle_leaving()

            # Stage 3: board elevators
            self._handle_boarding()

            # Stage 4: move the elevators using the moving algorithm
            self._move_elevators()

            for floor in range(1, self.num_floors + 1):
                for person in self.waiting[floor]:
                    person.wait_time += 1
            for elevator in self.elevators:
                for passenger in elevator.passengers:
                    passenger.wait_time += 1

            # Pause for 1 second
            self.visualizer.wait(1)

        return self._calculate_stats(num_rounds)

    def _generate_arrivals(self, round_num: int) -> None:
        """Generate and visualize new arrivals."""
        new_arrival = self.arrival_generator.generate(round_num)
        for floor in range(1, self.num_floors + 1):
            self.waiting[floor] = self.waiting[floor] + \
                                  new_arrival.get(floor, [])
        self.visualizer.show_arrivals(new_arrival)

    def _handle_leaving(self) -> None:
        """Handle people leaving elevators."""
        for elevator in self.elevators:
            remove_lst = []
            for passenger in elevator.passengers:
                if passenger.target == elevator.location:
                    self.all_finished.append(passenger)
                    self.visualizer.show_disembarking(passenger, elevator)
                    remove_lst.append(passenger)
            for passenger in remove_lst:
                elevator.passengers.remove(passenger)

    def _handle_boarding(self) -> None:
        """Handle boarding of people and visualize."""
        for elevator in self.elevators:
            has_people = len(self.waiting[elevator.location]) > 0
            while elevator.fullness() < 1 and has_people:
                first_waiting = self.waiting[elevator.location][0]
                self.visualizer.show_boarding(first_waiting, elevator)
                elevator.passengers.append(first_waiting)
                self.waiting[elevator.location].pop(0)
                has_people = len(self.waiting[elevator.location]) > 0

    def _move_elevators(self) -> None:
        """Move the elevators in this simulation.

        Use this simulation's moving algorithm to move the elevators.
        """
        round_move = self.moving_algorithm.move_elevators(self.elevators,
                                                          self.waiting,
                                                          self.num_floors)
        for elevator in range(len(round_move)):
            self.elevators[elevator].location += round_move[elevator].value
        self.visualizer.show_elevator_moves(self.elevators, round_move)

    ############################################################################
    # Statistics calculations
    ############################################################################
    def _calculate_stats(self, num_rounds: int) -> Dict[str, int]:
        """Report the statistics for the current run of this simulation.
        """
        wait_time_lst = []
        total = 0
        for passenger in self.all_finished:
            wait_time_lst.append(passenger.wait_time)
            total += passenger.wait_time
        if len(self.all_finished) > 0:
            avg = int(total / len(self.all_finished))
        elif len(self.all_finished) == 0:
            avg = -1
        waiting = 0
        for floor in range(1, self.num_floors + 1):
            waiting += len(self.waiting[floor])
        num_passengers = len(self.all_finished) + waiting
        for elevator in self.elevators:
            num_passengers += len(elevator.passengers)
        if len(wait_time_lst) == 0:
            wait_time_lst.append(-1)
        return {
            'num_iterations': num_rounds,
            'total_people': num_passengers,
            'people_completed': len(self.all_finished),
            'max_time': max(wait_time_lst),
            'min_time': min(wait_time_lst),
            'avg_time': avg
        }


def sample_run() -> Dict[str, int]:
    """Run a sample simulation, and return the simulation statistics."""
    config = {
        'num_floors': 6,
        'num_elevators': 6,
        'elevator_capacity': 3,
        'num_people_per_round': 2,
        # Random arrival generator with 6 max floors and 2 arrivals per round.
        'arrival_generator': algorithms.FileArrivals(6, 'sample_arrivals.csv'),
        'moving_algorithm': algorithms.RandomAlgorithm(),
        'visualize': True
    }

    sim = Simulation(config)
    stats = sim.run(8)
    return stats


if __name__ == '__main__':
    # Uncomment this line to run our sample simulation (and print the
    # statistics generated by the simulation).
    print(sample_run())

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['entities', 'visualizer', 'algorithms', 'time'],
        'max-nested-blocks': 4
    })
