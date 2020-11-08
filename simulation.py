from time import sleep
import sys
import traci
import traci.constants as tc
import numpy as np


class Simulation:
    def __init__(self, simulation_steps, sleep_time, pedestrians, bus_depot_start_edge, bus_depot_end_edge):
        self.simulation_steps = simulation_steps
        self.sleep_time = sleep_time
        self.pedestrians = pedestrians
        self.bus_depot_start_edge = bus_depot_start_edge
        self.bus_depot_end_edge = bus_depot_end_edge

    def run(self):

        """"
        add bus at the starting position
            try to transport all pedestrians at the moment
            as soon as this is not enough
            add another bus

            print score: (composed of number people not transported at the end + the max. number of simultaneous buses

        """

        person_count = 0
        num_buses = int(len(self.pedestrians)/8.0)
        print(num_buses)
        # sort pedestrians according to time
        ped_idx = np.argsort([pedestrian.depart for pedestrian in self.pedestrians])
        pedestrians_sorted = np.array(self.pedestrians)[ped_idx]

        for bus_index in range(num_buses):
            bus_id = f'bus_{bus_index}'
            bus_pedestrians = pedestrians_sorted[bus_index::num_buses]

            # add vehicle
            try:
                traci.vehicle.add(vehID=bus_id, typeID="BUS_L", routeID="", depart=bus_pedestrians[0].depart + 240.0, departPos=0,
                                  departSpeed=0, departLane=0, personCapacity=8)
            except traci.exceptions.TraCIException as err:
                print("TraCIException: {0}".format(err))
            except:
                print("Unexpected error:", sys.exc_info()[0])



            # concatenate all paths of pedestrians
            person_paths = []
            person_depart_times = []
            for person in bus_pedestrians:
                person_count += 1  # number of passengers not transported at the end
                person_path = ((person.edge_from, person.position_from), (person.edge_to, person.position_to))
                person_paths.append(person_path)
                person_depart_times.append(person.depart)

            # set the route for the vehicle
            route = [self.bus_depot_start_edge]
            for (edge_from, position_from), (edge_to, position_to) in person_paths:
                route = route + list(
                    traci.simulation.findRoute(fromEdge=route[-1], toEdge=edge_from).edges)[1:] \
                        + list(traci.simulation.findRoute(fromEdge=edge_from, toEdge=edge_to).edges)[1:]
                traci.vehicle.setRoute(bus_id, route)
                traci.vehicle.setStop(vehID=bus_id, edgeID=edge_from, pos=position_from, laneIndex=0,
                                      duration=500, flags=tc.STOP_DEFAULT)
                traci.vehicle.setStop(vehID=bus_id, edgeID=edge_to, pos=position_to, laneIndex=0,
                                      duration=500, flags=tc.STOP_DEFAULT)

        traci.vehicle.subscribe('bus_0', (tc.VAR_ROAD_ID, tc.VAR_LANEPOSITION, tc.VAR_POSITION, tc.VAR_NEXT_STOPS))
        loss = len(self.pedestrians) - person_count
        print("loss", loss)

        step = 0
        while step <= self.simulation_steps:
            traci.simulationStep()
            if self.sleep_time > 0:
                sleep(self.sleep_time)
            step += 1
            # print(traci.vehicle.getSubscriptionResults('bus_0'))

        traci.close()
