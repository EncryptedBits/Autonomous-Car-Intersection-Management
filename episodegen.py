import sys
import random
import time
import threading
import math

class Infrastructure(object):
	"""
	This class Contains Current Information of intersection
	Variables :
		No_of_Lanes
			No of Lanes are the number of cars can pass at a time from road/2
		Total_road_at_intersection
			Number of road that meet at intersection Generally that is 4 for 2 intersected road
		Update_time_interval
			In seconds
	"""
	No_of_Lanes = 3
	Total_road_at_intersection = 4 
	update_time_interval = 0.01 # Second
	max_cars_comes_at_a_time = 200 # Traffic Density
	const_velocity = 6 # m/s 
	length_of_lane = 3 # mtrs

	def __init__(self):
		self.known_state=[ [ [] for i in range(self.No_of_Lanes) ] for i in range(self.Total_road_at_intersection)]

	def car(self):
		current_position = random.randint(1,self.Total_road_at_intersection)
		current_lane_position = random.randint(1,self.No_of_Lanes)
		destination = random.randint(1,self.Total_road_at_intersection)
		start_time = time.time()
		def delay_time():
			"""Return delay time in seconds"""
			return time.time() - start_time
		def initial_position():
			x = - ((self.No_of_Lanes-current_lane_position)*self.length_of_lane + self.length_of_lane*0.5)
			y = - (self.No_of_Lanes*self.length_of_lane )
			return (x,y)
		def radius():
			rad= - ((self.No_of_Lanes-current_lane_position)*self.length_of_lane + self.length_of_lane*0.5)
			return rad
		def radius_():
			return self.No_of_Lanes*self.length_of_lane - radius()
		def currentPosition(time):
			r = radius() 
			x,y = initial_position()
			ts = self.No_of_Lanes*self.length_of_lane/self.const_velocity
			tr = math.pi*r/(2.0*self.const_velocity)
			if abs(current_position-destination)==2: #Travel straight
				if time < 2*ts:
					y = y + self.const_velocity*time 
				else:
					return False
			elif abs(current_position-destination)==0: #Travel back in same Road
				if time < ts:
					y = y + self.const_velocity*time 
				elif time < ts + tr:
					time = time - ts
					y = r*math.sin(theta)
					x = x + r*math.cos(theta)
				elif time < ts + 2*tr:
					time = time - ts - tr
					y = r - r*math.sin(theta)
					x = r*math.cos(theta)
				elif time < 2*(ts + tr):
					time = time - ts - 2*tr
					x = r
					y = -self.const_velocity*time
				else:
					return False 
			elif current_position%4 < destination: #Travel to right
				r = radius()
				theta = self.const_velocity*time/float(r)
				if time < ts:
					y = y + self.const_velocity*time 
				elif time < ts+tr:
					time = time - ts
					y = r*math.sin(theta)
					x = x + r*math.cos(theta)
				elif time < 2*ts + tr:
					time = time - ts - tr
					y = r
					x = self.const_velocity*time 
				else:
					return False
			elif current_position > destination%4: #Travel to left
				r_= radius_()
				if time < math.pi*r_/(2.0*self.const_velocity): 
					theta = self.const_velocity*time/float(r_)
					x = x - r_*math.cos(theta)
					y = y + r_*math.sin(theta) 
				else:
					return False
			return (x,y)
		def f():
			if delay_time() < 0.01:
				return 15
			elif delay_time() < 0.02:
				return 13
			elif delay_time() < 0.03:
				return 11
			elif delay_time() < 0.3:
				return 9
			elif delay_time() < 0.5:
				return 7
			elif delay_time() < 1:
				return 5
			elif delay_time() < 4:
				return 2
			return 1
		return (current_position,current_lane_position,destination,f,currentPosition)

	def update_known_state(self):
		while True:
			for i in range(random.randrange(self.max_cars_comes_at_a_time)):
				c=self.car()
				self.known_state[c[0]-1][c[1]-1].append(c)
			time.sleep(self.update_time_interval)

	def start(self):
		threading.Thread(target=self.update_known_state).start()


class EpisodeGen(Infrastructure):
	"""Docstring for EpisodeGen
	This class for generating Episode Randomely
	"""
	# def get_state(self):
	# 	state = [[car]*No_of_Lanes for i in range(Total_road_at_intersection)]
	# 	return state
	Active_cars = []
	Threshold   = 0.001 # Used for accedent Distance in mtrs
	learning_rate = 0.2
	discount_factor = 0.2
	policy_values = {}
	learning_table = {}
	def saveinfile(self,filename,data):
		file=open(filename,'a')
		file.write(str(data)+'\n')
		file.close()
	def distance(self,c1,c2):
		return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
	def Accedent_case(self):
		while self.Active_cars:
			for i in range(len(self.Active_cars)):
				for j in range(i,len(self.Active_cars)):
					first_car_position = self.Active_cars[i][4](0)
					second_car_position = self.Active_cars[j][4](0)
					if first_car_position==False:
						self.Active_cars.remove(Active_cars[i])
					if second_car_position==False:
						self.Active_cars.remove(self.Active_cars[j])
					if self.distance(first_car_position,second_car_position)<self.Threshold:
						self.Active_cars=[]
						return True
		return False
	def getReward(self):
		return self.reward
	def action(self,take_action=True):
		act = []
		self.reward=0
		current_state = str(self.get_state())
		for i in range(self.Total_road_at_intersection):
			act.append([])
			for j in range(self.No_of_Lanes):
				if len(self.known_state[i][j]):
					val = random.randrange(2)
					act[i].append(val)
					if take_action and val:
						self.reward=self.reward + self.known_state[i][j][0][3]()
						self.Active_cars.append(self.known_state[i][j].pop(0))
				else:
					act[i].append(0)
		if self.Accedent_case():
			print('Accedent Happened')
			self.reward = self.reward - 31
		next_sate = str(self.get_state())
		if take_action and False:
			#Update Q Value
			act=str(act)
			if self.learning_table.get(current_state,"Not Exist") == "Not Exist":
				self.learning_table[current_state] = {}
			if self.learning_table[current_state].get(act,"Not Exist") == "Not Exist":
				self.learning_table[current_state][act]=0

			if self.learning_table.get(next_state,"Not Exist") == "Not Exist":
				self.learning_table[next_state] = {}
			if self.learning_table[next_state].get(act,"Not Exist") == "Not Exist":
				self.learning_table[next_state][act]=0

			self.learning_table[current_state][act] += self.learning_rate*( self.reward + self.discount_factor*self.learning_table[next_state][act] - self.learning_table[current_state][act])
		return act
	def get_state(self):
		return [[ (self.known_state[i][j][0][2],self.known_state[i][j][0][3]()) if len(self.known_state[i][j]) else 0 for j in range(self.No_of_Lanes)] for i in range(self.Total_road_at_intersection)]

EpisodeG = EpisodeGen() 
EpisodeG.start()
i=0
while True:
	print('Action ',i)
	i+=1
	EpisodeG.saveinfile('result.txt',"%120s   %20s   %5s"%(EpisodeG.get_state(),EpisodeG.action(),EpisodeG.getReward()))
