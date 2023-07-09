#!/usr/bin/env python3

import sys

from inputs import readTests, readInputs
from objects import Solution

def topological_sort(tasks):
	# Create a dictionary to store the number of incoming edges for each task
	in_degree = {task.id: len(task.predecessors) for task in tasks}
	# Initialize the queue with the tasks that have no incoming edges
	queue = [task for task in tasks if in_degree[task.id] == 0]
	# Perform topological sorting
	sorted_tasks = []
	# while queue is not empty
	while queue:
		# Get the next task in the queue and add it to the sorted list
		task = queue.pop(0)
		sorted_tasks.append(task)
		# Decrement the incoming edge count for each successor of task
		for successor_id, _ in task.successors.items():
			in_degree[successor_id] -= 1
			# If the successor has no more incoming edges, add it to the queue
			if in_degree[successor_id] == 0:
				successor = inputs.tasks[successor_id]
				queue.append(successor)
	return sorted_tasks

"""
Topological Ordering and Resource Allocation (TORA) heuristic.
"""
def TORA_Heuristic(inputs, test):
	solution = Solution()

	# Initialize resources availability
	resources_availability = {resource.id: resource.units for resource in inputs.resources}

	# Initialize dictionary to keep track of resources used by each task
	resources_used = {task.id: set() for task in inputs.tasks}

	# Sum tasks fungible resources usage
	resources_sum = {resource.id: 0 for resource in inputs.resources if resource.type == "Fisico"}
	for task in inputs.tasks:
		for resource_id, units in task.resources.items():
			if resource_id in resources_sum:
				resources_sum[resource_id] += units

	# Check the availability of the fungible resources
	for resource_id, units in resources_sum.items():
		if resources_availability[resource_id] < units:
			sys.exit(f"[ERROR]: Insufficient units of resource {resource_id}")

	# Topologically sort the tasks. A topological sort is an algorithm that takes a directed
	# graph and returns a linear ordering of its vertices (nodes) such that, for every
	# directed edge (u, v) from vertex u to vertex v, u comes before v in the ordering
	sorted_tasks = topological_sort(inputs.tasks)

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
				while resources_availability[resource_id] < units:
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

	solution.cost = task.finish_time
	return solution

def printSolution(solution):
	print("{:s}".format("\n".join(str(task) for task in solution.tasks)))
	print("Cost: {:.2f}".format(solution.cost))
	print("Time: {:.2f}\n".format(solution.time))

if __name__ == "__main__":
	# Read tests from the file
	tests = readTests("test2run2.txt")

	for test in tests:
		# Read inputs for the test inputs
		inputs = readInputs(test.instanceName)

		# Calculate solution for the given scenario
		solution = TORA_Heuristic(inputs, test)
		print("OBD {:s}".format(test.instanceName))
		printSolution(solution)
