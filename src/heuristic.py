#!/usr/bin/env python3

import sys
from numpy import isfinite
import pandas as pd
import glob
from inputs import readTests, readInputs
from objects import Solution	

import numpy as np
# Para las permutaciones
from itertools import permutations

# Para el tiempo
import time



# ITERATED LOCAL SEARCH
def ILS(inputs, test, rng):
	print("\nILS")

	# Sum tasks fungible resources usage
	resources_sum = {resource.id: 0 for resource in inputs.resources if resource.type == "Fisico"}
	for task in inputs.tasks:
		for resource_id, units in task.resources.items():
			if resource_id in resources_sum:
				resources_sum[resource_id] += units

	# Check the availability of the fungible resources
	resources_availability = {resource.id: resource.units for resource in inputs.resources}
	for resource_id, units in resources_sum.items():
		if resources_availability[resource_id] < units:
			sys.exit(f"[ERROR]: Insufficient units of resource {resource_id}")
	
	solution = TORA_Heuristic(inputs, rng)
	print("\nILS_solution=")#,solution.tasks)
	return solution



# Topological Ordering and Resource Allocation (TORA) heuristic.
def TORA_Heuristic(inputs, rng):
	print("\nTORA_HEURISTIC")
	# solution = Solution()

	# Topologically sort the tasks
	sorted_tasks = topological_sort(inputs.tasks, inputs)
   
	# print("SORTED_TASKS",sorted_tasks)

	##################### ¿ NO ES NECESARIO ? #########################
	solution = sorted_tasks_timming_loop(sorted_tasks, inputs)
	# base_solution = solution

	solution = local_search(solution, sorted_tasks, inputs, rng)

	# solution = sorted_tasks_timming_loop(sorted_tasks, resources_availability, resources_used, inputs)
	
	print("\nTORA_solution=")#,solution.tasks)
	return solution


def topological_sort(tasks, inputs):
	print("\nTOPOLOGICAL_SORT")
	in_degree = {task.id: len(task.predecessors) for task in tasks}
	queue = [task for task in tasks if in_degree[task.id] == 0]
	sorted_tasks = []

	while queue:
		task = queue.pop(0)
		sorted_tasks.append(task)

		for successor_id, _ in task.successors.items():
			in_degree[successor_id] -= 1
			if in_degree[successor_id] == 0:
				successor = inputs.tasks[successor_id]
				queue.append(successor)

	# Check if there are still tasks remaining in in_degree
	if any(in_degree.values()):
		raise ValueError("The input graph contains a cycle")

	print("\nTopological_sort_sorted_tasks=")#,sorted_tasks)
	return sorted_tasks



def local_search(solution, sorted_tasks, inputs, rng):
	print("\nLOCAL_SEARCH(SOLUTION,...):")
	new_solution = solution
	# solutions_found = 0
	best_sorted_tasks = sorted_tasks.copy()  # Copiar la lista inicial de sorted_tasks

	successors_db = pd.read_excel("Successors_All.xlsx")
	new_sorted_tasks = best_sorted_tasks.copy()
	
	unoptimized_tasks = rng.choice(solution.tasks, inputs.nTasks, replace = False)
	# Bucle con una iteración por cada tarea
	for unoptimized_task in unoptimized_tasks:
		i = solution.tasks.index(unoptimized_task)
		
		# Crear una nueva lista de tareas que modificar en la iteración
		new_sorted_tasks = solution.tasks.copy()
		
		acceptedUnimprovements = 0
		
		# Bucle para hacer, si es posible, el ShiftToLeft
		for prev_sorted_tasks in range(i, 0, -1):	
			print("\t\t\t",i)
			val1 = new_sorted_tasks[prev_sorted_tasks - 1].label
			val2 = new_sorted_tasks[prev_sorted_tasks].label
			val1_p = new_sorted_tasks[prev_sorted_tasks - 1].project
			val2_p = new_sorted_tasks[prev_sorted_tasks].project


			print("¿[P{:s},T{:s}] <> [P{:s},T{:s}]?\n".format(str(val1_p), str(val1), str(val2_p), str(val2)))

			# Filtrar los casos en los que task no aparezca en los sucesores de la fila en la que el "ID" sea igual a prev_sorted_tasks - 1
			# print(new_sorted_tasks[prev_sorted_tasks - 1].id)
			val1_successors = successors_db.loc[successors_db["ID"] == new_sorted_tasks[prev_sorted_tasks - 1].id, "Successors"].values[0]
			
			if str(new_sorted_tasks[prev_sorted_tasks].id) not in val1_successors.split():
				print("\t\t\t\t\t\t\t\t\tBestSolution?")
				# Intercambiar las tareas si cumple la condición
				aux = new_sorted_tasks[prev_sorted_tasks]
				new_sorted_tasks[prev_sorted_tasks] = new_sorted_tasks[prev_sorted_tasks - 1]
				new_sorted_tasks[prev_sorted_tasks - 1] = aux

				# Ejecutar el algoritmo TORA actualizado con la nueva lista de tareas
				new_solution = sorted_tasks_timming_loop(new_sorted_tasks, inputs)
				print("new_solution.cost= ",new_solution.cost)

				print("solution.cost= ",solution.cost) 
				if new_solution.cost < solution.cost:
					print("\t\t\t\t\t\t\t\t\t\t\tBestSolution!")
					solution = new_solution
					# solutions_found += 1
					# optimizing = True
					acceptedUnimprovements = 0
				else:
					if acceptedUnimprovements < 2:#len(new_sorted_tasks):
						acceptedUnimprovements += 1
					else:
						# for _ in range (acceptedUnimprovements-1, 0, -1):
						acceptedUnimprovements -= 1
						i -= 1
						# Intercambiar las tareas si cumple la condición
						aux = new_sorted_tasks[prev_sorted_tasks]
						new_sorted_tasks[prev_sorted_tasks] = new_sorted_tasks[prev_sorted_tasks - 1]
						new_sorted_tasks[prev_sorted_tasks - 1] = aux
			else:
				break
			print("\t\t\t\t\t",solution.cost)
			print("\t\t\t\t\t\t",new_solution.cost)
			print("\t\t\t\t\t\t\t\t",acceptedUnimprovements)

		# Verificar si se ha encontrado una mejor solución en la iteración actual
		if new_solution.cost < solution.cost:
			solution = new_solution
			# solutions_found += 1
		# else:
		# 	break
	# reps = reps + 1
	return solution






def sorted_tasks_timming_loop(sorted_tasks, inputs):
	print("\nSORTED_TASKS_TIMMING_LOOP")
	solution = Solution()
	# current_tasks_times = {}
	# print(sorted_tasks)
	# print(len(sorted_tasks))

	# Initialize dictionary to keep track of resources used by each task
	resources_availability = {resource.id: resource.units for resource in inputs.resources}
	resources_used = {task.id: set() for task in inputs.tasks}

	# Loop over the tasks in topological order
	for task in sorted_tasks:
		# Calculate earliest start time for task considering predecessor dependencies
		earliest_start_time = 0
		for pred_id, extra_time in task.predecessors.items():
			pred_task = inputs.tasks[pred_id]
			if extra_time >= 0:
				# Add extra time to the ending time of predecessor
				earliest_start_time = max(earliest_start_time, pred_task.finish_time + extra_time)
			else:
				# Add extra time to the starting time of predecessor
				earliest_start_time = max(earliest_start_time, pred_task.start_time + abs(extra_time))
		

		# Refine earliest start time for task considering resource availability
		for resource_id, units in task.resources.items():
			if resources_availability[resource_id] < units:
				resource = inputs.resources[resource_id]
				# Sort assigned tasks to resource by finish time
				assigned_tasks = [inputs.tasks[task_id] for task_id, _ in resource.assigned_tasks.items()]
				assigned_tasks.sort(key=lambda t: t.finish_time)
				# Iterate assigned tasks and update resources
				while assigned_tasks and resources_availability[resource_id] < units:
					assigned_task = assigned_tasks.pop(0)
					# Release non-fungible resources used by task
					for rel_resource_id in resources_used[assigned_task.id]:
						rel_resource = inputs.resources[rel_resource_id]
						# Update resources assigned tasks
						rel_units = rel_resource.assigned_tasks[assigned_task.id]
						resources_availability[rel_resource_id] += rel_units
						del rel_resource.assigned_tasks[assigned_task.id]
					# Reset resources used by task
					resources_used[assigned_task.id] = set()
				# Update earliest start time considering task ending time
				earliest_start_time = max(earliest_start_time, assigned_task.finish_time)

		# Update finish time of task
		task.start_time = earliest_start_time
		task.finish_time = earliest_start_time + task.duration
		# Assign resources to task
		for resource_id, units in task.resources.items():
			resources_availability[resource_id] -= units
			resource = inputs.resources[resource_id]
			if resource.type == "HC":
				resource.assigned_tasks[task.id] = units
				resources_used[task.id].add(resource_id)
		# Add task to project schedule
		solution.tasks.append(task)
		solution.tasks_times[task.id] = (task.start_time, task.finish_time)

		solution.cost = max(solution.cost, task.finish_time)
		solution.start_time = task.start_time
	return solution



def printSolution(solution):
	print("\nPRINT_SOLUTION")
	for task in solution.tasks:
		# Start time:{self.start_time}\tEnd time:{self.finish_time#####################
		tupla = solution.tasks_times[task.id]
		print("{:s}, t({:d}-{:d})".format(str(task), tupla[0], tupla[1]))
	print("Cost: {:.2f}".format(solution.cost))
	print("Time: {:.2f}\n".format(solution.time))
	# print(solution.tasks)



if __name__ == "__main__":
	print("MAIN")
	# Read tests from the file
	tests = readTests("test2run2.txt")

	for test in tests:
		# Read inputs for the test inputs
		inputs = readInputs(test.instanceName)
		rng = np.random.default_rng(test.seed)
		
		# Calculate solution for the given scenario
		# solution = TORA_Heuristic(inputs, test)
		solution = ILS(inputs, test, rng)
		
		#print("OBD {:s}".format(test.instanceName))
		printSolution(solution)