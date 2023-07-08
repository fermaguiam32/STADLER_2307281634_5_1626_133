#!/usr/bin/env python3

import pandas as pd

from objects import Task, Resource

class Test:

	def __init__(self, instanceName, maxTime, nIter, distCrit, betaMin, betaMax, distCand, betaMin2, betaMax2, seed, project):
		self.instanceName = instanceName
		self.maxTime = int(maxTime)
		self.nIter = int(nIter)
		self.distCrit = distCrit
		self.betaMin = float(betaMin)
		self.betaMax = float(betaMax)
		self.distCand = distCand
		self.betaMin2 = float(betaMin2)
		self.betaMax2 = float(betaMax2)
		self.seed = int(seed)
		self.TYPE_CRITERIA = 0
		self.TYPE_CANDIDATE = 1
		self.project = int(project)

class Inputs:

	def __init__(self, name, nTasks, nResources, tasks, resources):
		self.name = name
		self.nTasks = nTasks
		self.nResources = nResources
		self.tasks = tasks
		self.resources = resources

def readTests(fileName):
	tests = []
	with open("../tests/" + fileName) as f:
		for line in f:
			tokens = line.split("\t")
			if '#' not in tokens[0]:
				test = Test(*tokens)
				tests.append(test)
	return tests

def readInputs(instanceName):
	# Read tasks and resources into DataFrames
	tasks_df = pd.read_excel("../inputs/" + instanceName + ".xlsx", sheet_name="Tasks", dtype={"ID" : str, "Predecessors" : str, "Successors" : str}, na_filter=False)
	resources_df = pd.read_excel("../inputs/" + instanceName + ".xlsx", sheet_name="Resources")

	# Create list of task objects
	tasks = []
	for i, row in tasks_df.iterrows():
		predecessors = {}
		successors = {}
		resources = {}

		for pred in row['Predecessors'].split(";"):
			if pred:
				fc_index = pred.find("FC")
				cc_index = pred.find("CC")
				if fc_index != -1:
					label = pred[:fc_index]
					pred_id = tasks_df.loc[tasks_df["ID"] == label].index[0]
					predecessors[pred_id] = int(pred[fc_index + 3:])
				elif cc_index != -1:
					label = pred[:cc_index]
					pred_id = tasks_df.loc[tasks_df["ID"] == label].index[0]
					predecessors[pred_id] = -int(pred[cc_index + 3:])
				else:
					pred_id = tasks_df.loc[tasks_df["ID"] == pred].index[0]
					predecessors[pred_id] = 0

		for succ in row['Successors'].split(";"):
			if succ:
				fc_index = succ.find("FC")
				cc_index = succ.find("CC")
				if fc_index != -1:
					label = succ[:fc_index]
					succ_id = tasks_df.loc[tasks_df["ID"] == label].index[0]
					successors[succ_id] = int(succ[fc_index + 3:])
				elif cc_index != -1:
					label = succ[:cc_index]
					succ_id = tasks_df.loc[tasks_df["ID"] == label].index[0]
					successors[succ_id] = -int(succ[cc_index + 3:])
				else:
					succ_id = tasks_df.loc[tasks_df["ID"] == succ].index[0]
					successors[succ_id] = 0

		for j, res in enumerate(row[6 : len(tasks_df.columns)]):
			if res:
				resources[j] = float(res)

		task = Task(i, row['ID'], row['Name'], row['Duration'], predecessors, successors, resources)
		tasks.append(task)

	# Create list of resource objects
	resources = []
	for i, row in resources_df.iterrows():
		resource = Resource(i, row['ID'], row['Name'], row['Type'], row['Units'])
		resources.append(resource)

	inputs = Inputs(instanceName, len(tasks), len(resources), tasks, resources)
	return inputs

def readInputsPatterson(instanceName):
	lines = open("../inputs/" + instanceName, "r").readlines()

	n_jobs = int(lines[5].split()[-1])
	_ = int(lines[6].split()[-1])
	n_resources = int(lines[8].split()[-2])
	R = list(range(n_resources))

	# Create list of task objects
	tasks = []
	for i in range(n_jobs):
		predecessors = {}
		successors = {}
		resources = {}

		parts = list(map(int, lines[18 + i].split()))
		name = parts[0]

		# Successors
		for j in parts[3:]:
			successors[j-1] = 0

		parts = list(map(int, lines[18 + n_jobs + 4 + i].split()))
		duration = parts[2]
		for r in R:
			if parts[3 + r] > 0:
				resources[r] = parts[3 + r]

		task = Task(i, name, name, duration, predecessors, successors, resources)
		tasks.append(task)

	# Predecessors
	for task in tasks:
		predecessors = {}
		for other_task in tasks:
			if task.id in other_task.successors:
				predecessors[other_task.id] = 0
		task.predecessors = predecessors

	# Create list of resource objects
	resources = []
	parts = list(map(int, lines[18 + n_jobs + 4 + n_jobs + 3].split()))
	for r in R:
		resource = Resource(r, r, r, 'HC', parts[r])
		resources.append(resource)

	inputs = Inputs(instanceName, len(tasks), len(resources), tasks, resources)
	return inputs
