#!/usr/bin/env python3

import pandas as pd
import glob

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
	# Inicializo el contador de tareas a #0 antes de contar ninguna tarea
	project_id = 0
	# Defino la ruta de acceso a los EXCELs que leer
	ruta = '../inputs/STADLER Loc Type *.xlsx'
	# Leo todos los EXCELs que cumplan la condición del nombre
	archivos = glob.glob(ruta)
	# Inicializo una lista vacía
	dfs = []
	# En cada repetición dada por un nuevo EXCEL, incremento project_id en #1
	project_id = project_id + 1
	for archivo in archivos:
		df = pd.read_excel(archivo, dtype={"ID": str, "Predecessors": str, "Successors": str, "Project": str}, na_filter=False)
		df["Project"] = project_id
		# df.rename({'col 0': 'X'}, axis=1)
		dfs.append(df)
		project_id = project_id + 1


	tasks_df = pd.concat(dfs, ignore_index=True)

	tasks_df.to_excel("tasks.xlsx")

	# print("\n\n\n\n\nSuccessors_df=\n",successors_df, "\n\n\n\n")

	inputs_list = []

	resources_df = pd.read_excel("../inputs/STADLER_Resources.xlsx", sheet_name="Resources")

	# Create list of task objects
	tasks = []

	for i, row in tasks_df.iterrows():
		predecessors = {}
		successors = {}
		resources = {}

		for pred in str(row['Predecessors']).split(";"):
			if pred:
				fc_index = pred.find("FC")
				cc_index = pred.find("CC")
				if fc_index != -1:
					label = pred[:fc_index]
					pred_id = tasks_df.loc[(tasks_df["ID"] == label) & (tasks_df["Project"] == row["Project"])].index[0]
					predecessors[pred_id] = int(pred[fc_index + 3:])
				elif cc_index != -1:
					label = pred[:cc_index]
					pred_id = tasks_df.loc[(tasks_df["ID"] == label) & (tasks_df["Project"] == row["Project"])].index[0]
					predecessors[pred_id] = -int(pred[cc_index + 3:])
				else:
					pred_id = tasks_df.loc[(tasks_df["ID"] == pred) & (tasks_df["Project"] == row["Project"])].index[0]
					predecessors[pred_id] = 0

		for succ in row['Successors'].split(";"):
			if succ:
				fc_index = succ.find("FC")
				cc_index = succ.find("CC")
				if fc_index != -1:
					label = succ[:fc_index]
					succ_id = tasks_df.loc[(tasks_df["ID"] == label) & (tasks_df["Project"] == row["Project"])].index[0]
					successors[succ_id] = int(succ[fc_index + 3:])
				elif cc_index != -1:
					label = succ[:cc_index]
					succ_id = tasks_df.loc[(tasks_df["ID"] == label) & (tasks_df["Project"] == row["Project"])].index[0]
					successors[succ_id] = -int(succ[cc_index + 3:])
				else:
					# tasks_df.to_excel("tasks_df_2.xlsx")
					succ_id = tasks_df.loc[(tasks_df["ID"] == succ) & (tasks_df["Project"] == row["Project"])].index[0]
					successors[succ_id] = 0

		for j, res in enumerate(row[6 : len(tasks_df.columns) - 1]):
			if res:
				resources[j] = float(res)

		task = Task(i, row['ID'], row['Name'], row['Duration'], predecessors, successors, resources, row["Project"])
		tasks.append(task)
		sorted_tasks = pd.DataFrame(tasks)
		sorted_tasks.to_excel("auto_sorted_tasks.xlsx")

	# Create list of resource objects
	resources = []
	for i, row in resources_df.iterrows():
		resource = Resource(i, row['ID'], row['Name'], row['Type'], row['Units'])
		resources.append(resource)



	successors_df = pd.DataFrame()
	# successors_df["ID"] = tasks_df["ID"]
	
	# Reemplazar los caracteres específicos en la columna deseada
	successors_df['Successors'] = tasks_df['Successors'].str.replace('CF', '')
	successors_df['Successors'] = successors_df['Successors'].str.replace('FF', '')
	successors_df['Successors'] = successors_df['Successors'].str.replace('FC', '')
	successors_df['Successors'] = successors_df['Successors'].str.replace('CC', '')
	successors_df['Successors'] = successors_df['Successors'].str.replace(';', ' ')


	# Quitar los incrementos "+NN" de cada fila	
	# Obtener la columna "Successors" como una lista
	successors_column = successors_df["Successors"].tolist()
	# Recortar los textos hasta el signo '+'
	recortados = [texto.split('+')[0] if '+' in texto else texto for texto in successors_column]
	# Actualizar la columna "Successors" con los textos recortados
	successors_df["Successors"] = recortados
	# successors_df.to_excel('Successors_1.xlsx', index=False)


	# Conjunto para almacenar los sucesores visitados

	# Iterar sobre cada tarea y obtener los sucesores indirectos posteriores
	dfs = []
	for task in tasks:
		visited = set()
		get_all_successors(tasks, task, visited)
		visited.remove(task.id)
		string = " "
		for v in visited:
			string += str(v) + " "
		df = pd.DataFrame({"ID": task.id, "Successors" : string}, index=[0])
		dfs.append(df)
		
	successors_df = pd.concat(dfs)
	# Imprimir el DataFrame resultante
	# # # # # # # # # print("\n\n\nsuccessors_df=\n",successors_df)

	successors_set = set(successors_df['Successors'])
	# print("\n\n\nSuccessors_set=",successors_set)
	
	successors_df.to_excel('Successors_All.xlsx', index=False)



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


# Función recursiva para obtener los sucesores indirectos posteriores
def get_all_successors(tasks, task, visited):
    if task.id in visited:
        return

    visited.add(task.id)
    if task.successors:
        for successor_id, _ in task.successors.items():
            successor = tasks[successor_id]
            get_all_successors(tasks, successor, visited)
