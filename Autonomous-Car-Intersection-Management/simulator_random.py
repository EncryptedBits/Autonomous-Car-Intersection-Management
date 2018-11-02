# CODE VERSION 5.0

import tkinter
import math
import time
import random
import threading
import os
import sys
from PIL import Image,ImageTk

if sys.version_info[0]!=3:
	print('\n\n    USE VERSION : Python 3.x\n')
	exit(0)

Number_of_roads     = 2
Number_of_lanes     = 2
Width_of_lane       = 20
canvas_width        = 800
canvas_height       = 500
Accedent_threshold  = 15
gui_refresh_rate    = 1   # ms
SHOW_GUI            = True

## START TRAFFIC MANAGE
INVERSE_TRAFFIC     = 50   # inverser traffic is inverse praposnal of Traffic (min value = 1,Maximum traffic),(max value = No Limit,Minimum Traffic)
CAR_TIME_DELAY      = 10   # time delay is a time dalay for car (max=100) that comes on lane.
## END TRAFFIC MANAGE

REWARD = {
	'reached_to_destination': 30,
	'accedent':-20,
	'delay': lambda x:100 - x,
}

math.sign = lambda x: -1 if x<0 else 1
def _rotate(point,angle):
	return [point[0]*math.cos(angle)-point[1]*math.sin(angle) , point[1]*math.cos(angle)+point[0]*math.sin(angle)]

def _shift(point,shift_axis=None,x_shift=canvas_width/2,y_shift=canvas_height/2):
	if shift_axis=='x':
		return point + x_shift
	elif shift_axis=='y':
		return point + y_shift
	return [point[0]+x_shift,point[0]+y_shift]

def _inboundry(point):
	expand_by = 15
	if (point[0] > -canvas_width/2 - expand_by) and (point[1] > -canvas_height/2 - expand_by) and (point[0] < canvas_width/2 + expand_by) and (point[1] < canvas_height/2 + expand_by) : 
		return True
	return False

class Infrastructure(object):
	"""
		Contain All requried information about infrastructure
	"""
	def __init__(self):
		# VARIABLES
		self.Number_of_roads = Number_of_roads
		self.Number_of_lanes = Number_of_lanes
		self.Width_of_lane   = Width_of_lane
		self.canvas_width    = canvas_width
		self.canvas_height   = canvas_height
		# END VARIABLES
		self.cars = [[ [] for i in range(self.Number_of_lanes) ]for i in range(2*self.Number_of_roads)]
		self.active_cars_in_infrastructure = [ [ [] for i in range(self.Number_of_lanes) ] for i in range(self.Number_of_roads*2) ]
		self.cars_reached_to_destination = [[ [] for i in range(self.Number_of_lanes) ] for i in range(self.Number_of_roads*2) ]
		self.signal_radius = self.Width_of_lane*self.Number_of_lanes*4
		self.stop_radius = self.Width_of_lane*(self.Number_of_lanes+1)
		self.number_of_cars_reached_to_destination = 0
		self.number_of_cars_generated = 0
		self.Accedent_threshold = Accedent_threshold
		self.total_delay_time = 0
		self.number_of_cars_reached_to_active = 0
		self.total_collisions = -1
		self.stepwise_rewards = []
		self.active_state_number = 0 # Changes with each action take ... 
	
	def get_state(self):
		state = [ [ False for i in range(self.Number_of_lanes) ] for i in range(self.Number_of_roads*2)]
		for i in range(len(self.cars)):
			for j in range(len(self.cars[i])):
				if len(self.cars[i][j]) > 0 and self.cars[i][j][0].color=='green':
					state[i][j]=(self.cars[i][j].final_position,self.cars[i][j].delay_time)
		return state

	def pick_all_possible_actions(self):
		state = self.get_state()

	def pick_action(self):
		"""
			Pick Action
				1. Create Action Variable with all false
				2. For each car stop intersection give them choice to start(True/False)
				3. Return Action
		"""
		is_cars_at_interface = False 
		action = [ [ False for i in range(self.Number_of_lanes) ] for i in range(self.Number_of_roads*2)]
		for i in range(len(self.cars)):
			for j in range(len(self.cars[i])):
				if len(self.cars[i][j]) > 0 and self.cars[i][j][0].color=='green':
					action[i][j]=random.choice([False,True])
					is_cars_at_interface = True
		return action,is_cars_at_interface

	def take_action(self,action):
		"""
			Take Action
				1. Taking action as input(from Pick action)
				2. Append all cars with allowd in interface to Active cars list
		"""
		delay_reward = 0
		for i in range(len(action)):
			for j in range(len(action[i])):
				if action[i][j]:
					self.cars[i][j][0].initial_position = self.cars[i][j][0].position[:]
					# Calculate delay time
					self.cars[i][j][0].delay_time =time.clock() - self.cars[i][j][0].delay_time
					self.total_delay_time += self.cars[i][j][0].delay_time
					delay_reward += REWARD['delay'](self.cars[i][j][0].delay_time)
					self.number_of_cars_reached_to_active+=1
					# Move car to active state
					self.cars[i][j][0].action_number = self.active_state_number
					self.active_cars_in_infrastructure[i][j].append(self.cars[i][j].pop(0))
		
		self.active_state_number += 1
		self.stepwise_rewards.append(delay_reward)		
	
	def get_reward(self):
		if len(self.stepwise_rewards) > 0:
			return self.stepwise_rewards[-1]
		return 0

	def check_accedent(self):
		accedent = False
		remove_accedent_cars = False
		f=[]
		for i1 in range(len(self.active_cars_in_infrastructure)):
			for j1 in range(len(self.active_cars_in_infrastructure[i1])):
				for k1 in range(len(self.active_cars_in_infrastructure[i1][j1])):
					first_car = self.active_cars_in_infrastructure[i1][j1][k1]
					faccedent = False
					for i2 in range(len(self.active_cars_in_infrastructure)):
						for j2 in range(len(self.active_cars_in_infrastructure[i2])):
							for k2 in range(len(self.active_cars_in_infrastructure[i2][j2])):
								if i1!=i2 or j1!=j2 or k1!=k2:
									second_car = self.active_cars_in_infrastructure[i2][j2][k2]
									if (first_car.position[0]-second_car.position[0])**2 + (first_car.position[1]-second_car.position[1])**2 < self.Accedent_threshold**2:
										faccedent = True
										accedent = True
										if first_car.color != 'yellow' and  second_car.color !='yellow':
											self.stepwise_rewards[max(first_car.action_number,second_car.action_number)] += REWARD['accedent']
										elif first_car.color != 'yellow':
											self.stepwise_rewards[first_car.action_number] += REWARD['accedent']
										elif second_car.color != 'yellow':
											self.stepwise_rewards[second_car.action_number] += REWARD['accedent']

										if first_car.color != 'yellow':
											first_car.color = 'yellow'
											self.total_collisions +=1
										if second_car.color != 'yellow':
											second_car.color = 'yellow'
											self.total_collisions +=1
										if remove_accedent_cars:
											if (i2,j2,second_car) not in f:
												f.append((i2,j2,second_car))
					if remove_accedent_cars and faccedent:
						if (i1,j1,first_car) not in f:
							f.append((i1,j1,first_car))
		if remove_accedent_cars:
			for i,j,c in f:
				self.active_cars_in_infrastructure[i][j].remove(c)

		return accedent
class car():
	"""
		Car
			Contain all specific information about car
	"""
	def __init__(self,current_position,current_lane_position):
		"""
			Initialize all important variables for car
		"""
		# INT (start from 1 to total number of lanes)
		self.current_lane_position = current_lane_position
		# INT (start from 1 to total number of roads at intersection)
		self.current_position = current_position
		self.final_position = random.randint(1,Number_of_roads*2)
		# self.final_position = random.choice([4,1])

		angle = 180*self.current_position/Number_of_roads
		theta = math.atan(canvas_height/canvas_width)
		# This variable help to move in intersection (Active cars in intersection)
		self.inf_step_after = 0
		self.color = 'red'
		if (angle <= theta and angle>=0) or ((angle<=180+theta) and (angle>=180-theta)) or ((angle<=360) and (angle>=360-theta)):
			angle = math.radians(angle)
			self.position = [math.sign(math.sin(angle))*canvas_width/2 + (Width_of_lane*self.current_lane_position- Width_of_lane/2)*math.sin(angle),math.sign(math.sin(angle))*(2*math.tan(angle))/canvas_width + (Width_of_lane*self.current_lane_position- Width_of_lane/2)*math.cos(angle)]
		else:
			angle = math.radians(angle)
			self.position = [math.sign(-math.sin(angle))*canvas_height/(2*math.tan(angle)) + (Width_of_lane*self.current_lane_position- Width_of_lane/2)*math.sin(angle),math.sign(math.sin(angle))*canvas_height/2 + (Width_of_lane*self.current_lane_position- Width_of_lane/2)*math.cos(angle)] # 2*math.tan(angle)/canvas_width - canvas_width/2
		# This radius for car from center of intersection
		self.cradius = Width_of_lane*self.current_lane_position - Width_of_lane/2
		self.speed = 5
		self.first_rotate = False
		self.delay_time = 0
	def update_position(self,car_before=None):
		"""
			Update car position 
				(Only in straight path 
				depend on current_position)
		"""
		angle = math.radians(-180*self.current_position/Number_of_roads)
		if car_before:
			if ((car_before.position[0]- self.position[0])**2 + (car_before.position[1] - self.position[1])**2)**0.5 < Width_of_lane: 	
				return
		self.position[0]=self.position[0]+self.speed*math.cos(angle)
		self.position[1]=self.position[1]+self.speed*math.sin(angle)
	def update_position_infra(self):
		"""
			Update Position in curve motion in interface (Active cars)
			This only implemented for two roads (Number_of_roads = 2)
		"""
		if abs(self.final_position - self.current_position) == 2: 
			# Moving Straight
			self.update_position()
		elif self.final_position == self.current_position: 
			# Coming back to same road
			position = _rotate(self.position,(self.current_position-1)*math.pi/2)
			if position[1] < 0:
				radius = self.cradius
				theta = self.speed/radius
				theta = theta * self.inf_step_after
				self.inf_step_after += 1
				initial_position = _rotate(self.initial_position,math.pi/2*(self.current_position-1))
				self.position[0] = initial_position[0] - radius*(1-math.cos(theta))
				self.position[1] = initial_position[1] - radius*math.sin(theta)
				self.position    = _rotate(self.position,-math.pi/2*(self.current_position-1))	
				self.first_rotate = True
			elif not self.first_rotate:
				self.update_position()
				self.initial_position = self.position[:]
			else:
				# angle = math.radians(-180*self.current_position/Number_of_roads)
				# self.position[0]=self.position[0]-self.speed*math.cos(angle)
				# self.position[1]=self.position[1]+self.speed*math.sin(angle)
				self.current_position = (self.final_position+2)%4
				if self.current_position == 0 :
					self.current_position = 4
		elif (self.current_position==1 and self.final_position == 4) or (self.current_position==4 and self.final_position == 3) or (self.current_position==3 and self.final_position == 2) or (self.current_position==2 and self.final_position == 1): 
			# Move Left
			position = _rotate(self.position,(self.current_position-1)*math.pi/2)
			if position[1] < 0 and position[0]>0:
				radius = self.cradius
				theta = self.speed/radius
				theta = theta * self.inf_step_after
				self.inf_step_after += 1
				initial_position = _rotate(self.initial_position,math.pi/2*(self.current_position-1))
				self.position[0] = initial_position[0] - radius*(1-math.cos(theta))
				self.position[1] = initial_position[1] - radius*math.sin(theta)
				self.position    = _rotate(self.position,-math.pi/2*(self.current_position-1))	
				self.first_rotate = True
			elif not self.first_rotate:
				self.update_position()
				self.initial_position = self.position[:]
			else:
				self.current_position = (self.final_position+2)%4
				if self.current_position == 0 :
					self.current_position = 4
				# angle = math.radians(-180*self.current_position/Number_of_roads+90)
				# self.position[0]=self.position[0]-self.speed*math.cos(angle)
				# self.position[1]=self.position[1]-self.speed*math.sin(angle)
		else: 
			# Move Right
			stop_radius = Width_of_lane*(Number_of_lanes+1) - Width_of_lane/4
			radius = stop_radius - self.cradius
			theta = self.speed/radius
			theta = theta * self.inf_step_after
			self.inf_step_after += 1
			initial_position = _rotate(self.initial_position,math.pi/2*(self.current_position-1))
			self.position[0] = initial_position[0] + radius*(1-math.cos(theta))
			self.position[1] = initial_position[1] - radius*math.sin(theta)
			self.position    = _rotate(self.position,-math.pi/2*(self.current_position-1))

	def set_initial_position(self,last_car):
		"""
			Update initial position if car is already there
		"""
		angle = math.radians(-180*self.current_position/Number_of_roads)
		if abs(last_car.position[0]*math.cos(angle)) >= abs(self.position[0]*math.cos(angle)) or abs(last_car.position[1]*math.sin(angle)) >= abs(self.position[1]*math.sin(angle)): 
			self.position[0]=last_car.position[0]-Width_of_lane*math.cos(angle)
			self.position[1]=last_car.position[1]-Width_of_lane*math.sin(angle)

class Simulator(tkinter.Frame,Infrastructure):
	"""
		It's GUI Simulator for Cars
		Inherit the properties of Infrastructure
	"""
	def __init__(self, *args, **kwargs):
		"""
			initialize some GUI Variables
		"""
		tkinter.Frame.__init__(self, *args, **kwargs)
		Infrastructure.__init__(self)
		self.show_gui = SHOW_GUI
		if self.show_gui:
			self.canvas = tkinter.Canvas(width=self.canvas_width, height=self.canvas_height)
			self.canvas.pack(side="top", fill=tkinter.BOTH, expand=True)
			self.draw_background()
			self.draw_roads()
			self.draw_tower()
		self.terminate = False
		self.start_stat = True
	def __del__(self):
		print('   Simulator Closed !')
	def draw_tower(self):
		"""
			Take image as input and draw at center of intersection of road
			(Act Signal)
		"""
		self.signal_image = ImageTk.PhotoImage(file='signal4.png')
		self.canvas.create_image(375, 220, image = self.signal_image, anchor=tkinter.NW)

	def draw_background(self):
		"""
			It's green background side of road
			(Gesture from Grass Image)
		"""
		self.image = ImageTk.PhotoImage(file='grass-texture1.jpg')
		self.canvas.create_image(0, 0, image = self.image, anchor=tkinter.NW)

	def draw_car(self,position,color='red'):
		"""
			Draw Car
			car is a square with ...
			width  = Width_of_lane/2
			height = Width_of_lane/2 
		"""
		if _inboundry(position):
			self.canvas.create_rectangle(	_shift(position[0]-self.Width_of_lane/4,'x'), 
											_shift(position[1]-self.Width_of_lane/4,'y'), 
											_shift(position[0]+self.Width_of_lane/4,'x'), 
											_shift(position[1]+self.Width_of_lane/4,'y'), fill=color, outline = 'grey', tags='car_gui')
	def draw_cars(self):
		"""
			Draw All Cars with it's update position ...
			(Function call at each Time Frame)
			(This function also pick _action and call that action to get new position of cars)
		"""
		_action,is_cars_at_interface = self.pick_action()
		if is_cars_at_interface:
			self.take_action(_action)
		# Modify cars in cars_reached_to_destination
		for i in range(len(self.cars_reached_to_destination)):
			for j in range(len(self.cars_reached_to_destination[i])):
				f=False
				for k in range(len(self.cars_reached_to_destination[i][j])):
					c = self.cars_reached_to_destination[i][j][k]
					car_before = None
					if k>0:
						car_before = self.cars_reached_to_destination[i][j][k-1]
					c.update_position(car_before)
					if k==0 and (c.position[0]+self.canvas_width/2>self.canvas_width or c.position[0]+self.canvas_width/2<0 or c.position[1]+self.canvas_height/2>self.canvas_height or c.position[1]+self.canvas_height/2<0):
						f=True
					else:
						# if (c.position[0]**2+c.position[1]**2)**0.5 < stop_radius:
						if (c.position[0]**2+c.position[1]**2)**0.5 < self.signal_radius:
							color='blue'
						else:
							color='red'
						c.color = color
						if self.show_gui:
							self.draw_car(c.position,color)
				if f:
					self.cars_reached_to_destination[i][j].pop(0)
		
		# Modify cars in active_cars_in_infrastructure
		for i in range(len(self.active_cars_in_infrastructure)):
			for j in range(len(self.active_cars_in_infrastructure[i])):
				f=[]
				for k in range(len(self.active_cars_in_infrastructure[i][j])):
					c=self.active_cars_in_infrastructure[i][j][k]
					c.update_position_infra()
					self.check_accedent()
					if c.position[0]>=self.stop_radius or c.position[0]<=-self.stop_radius or c.position[1]>=self.stop_radius or c.position[1] <= -self.stop_radius:
						f.append((i,j,c))
					if self.show_gui:
						self.draw_car(c.position,color=c.color)
				if f:
					for i,j,c in f:
						c.current_position = (c.final_position+2)%4
						if c.current_position == 0 :
							c.current_position = 4
						self.number_of_cars_reached_to_destination+=1
						self.stepwise_rewards[c.action_number] += REWARD['reached_to_destination']
						self.cars_reached_to_destination[c.current_position-1][j].append(c)	
						self.active_cars_in_infrastructure[i][j].remove(c)

		# Modify cars in cars
		for i in range(len(self.cars)):
			for j in range(len(self.cars[i])):
				# f=False
				for k in range(len(self.cars[i][j])):
					c = self.cars[i][j][k]
					car_before = None
					if k>0:
						car_before = self.cars[i][j][k-1]
					if c.color != 'green':
						c.update_position(car_before)
					# if k==0 and (c.position[0]+self.canvas_width/2>self.canvas_width or c.position[0]+self.canvas_width/2<0 or c.position[1]+self.canvas_height/2>self.canvas_height or c.position[1]+self.canvas_height/2<0):
					# 	f=True
					# else:
					# if (c.position[0]**2+c.position[1]**2)**0.5 < stop_radius:
					if c.position[0]<self.stop_radius and c.position[0]>-self.stop_radius and c.position[1]<self.stop_radius and c.position[1] > -self.stop_radius:
						color="green"
						c.delay_time = time.clock() # Set stop time here
					elif (c.position[0]**2+c.position[1]**2)**0.5 < self.signal_radius:
						color='blue'
					else:
						color='red'
					c.color = color
					if self.show_gui:
						self.draw_car(c.position,color)
				# if f:
				# 	self.cars[i][j].pop(0)
	def printInfo(self):
		"""
			Print Updated infromation about ...
		"""
		os.system('clear')
		print('   LANE INFORMATION')
		print('------------------------------------------------------------------')
		total_cars = 0
		for i in range(len(self.cars)):
			total_cars_lane=0
			for j in range(len(self.cars[i])):
				total_cars_lane+=len(self.cars[i][j])
			print('   Cars in ROAD',i+1,'                   :',total_cars_lane)
			total_cars += total_cars_lane
		print('   TOTAL CARS COMING                 :',total_cars)
		total_cars = 0
		for i in range(len(self.active_cars_in_infrastructure)):
			total_cars_lane=0
			for j in range(len(self.active_cars_in_infrastructure[i])):
				total_cars_lane+=len(self.active_cars_in_infrastructure[i][j])
			total_cars += total_cars_lane
		print('   TOTAL ACTIVE CARS                 :',total_cars)
		print('   TOTAL CARS REACHED TO DESTINATION :',self.number_of_cars_reached_to_destination)
		print('   TOTAL CARS GENERATED              :',self.number_of_cars_generated)
		print('   TOTAL DELAY TIME                  :',self.total_delay_time,'sec')
		if self.number_of_cars_reached_to_active:
			print('   AVERAGE DELAY TIME                :', self.total_delay_time/self.number_of_cars_reached_to_active,'sec')
		else:
			print('   AVERAGE DELAY TIME                :', None)
		if self.total_collisions>0:
			print('   TOTAL COLLISIONS                  :', self.total_collisions)
		else:
			print('   TOTAL COLLISIONS                  :', None)
		print('   CURRENT STATE                     :', self.active_state_number)
		print('------------------------------------------------------------------')


	def creates_car(self,current_position,current_lane_position):
		"""
			Generate single car for given current_position and current_lane_position
		"""
		self.number_of_cars_generated += 1 
		cr = car(current_position,current_lane_position)
		try:
			last_car = self.cars[cr.current_position-1][cr.current_lane_position-1][-1]
			cr.set_initial_position(last_car)
			self.cars[cr.current_position-1][cr.current_lane_position-1].append(cr)				
		except Exception as ex:
			self.cars[cr.current_position-1][cr.current_lane_position-1].append(cr)

	def creates_cars(self,current_position,current_lane_position,time_delay=10,inverse_traffic = 100):
		"""
			Create Cars
			(this function create cars at timestep or not randomly)
		"""
		while True and not self.terminate:
			time.sleep(random.randint(1,inverse_traffic)/100)
			if random.randint(0,abs(int((100-time_delay)))/10) == 0:
				self.creates_car(current_position,current_lane_position)

	def draw_roads(self,angle=0):
		"""
			Draw Roads
		"""
		for i in range(self.Number_of_roads):
			angle = 180*i/self.Number_of_roads
			angle = math.radians(angle)
			# SEPARATORS COLOR
			self.canvas.create_line(	_shift( self.canvas_width*math.cos(angle) ,'x'),
										_shift( self.canvas_height*math.sin(angle),'y'),
										_shift(-self.canvas_width*math.cos(angle) ,'x'),
										_shift(-self.canvas_height*math.sin(angle),'y'), fill="#333", width=self.Number_of_lanes*self.Width_of_lane*2)
		
		for i in range(self.Number_of_roads):
			angle = 180*i/self.Number_of_roads
			angle = math.radians(angle)
			# LEFT ROAD
			for i in range(self.Number_of_lanes):
				self.canvas.create_line(	_shift( self.canvas_width*math.cos(angle)  + (self.Width_of_lane*i - self.Width_of_lane*self.Number_of_lanes - 5 + self.Width_of_lane/2 + i)*math.sin(angle),'x'),
											_shift( self.canvas_height*math.sin(angle) - (self.Width_of_lane*i - self.Width_of_lane*self.Number_of_lanes - 5 + self.Width_of_lane/2 + i)*math.cos(angle),'y'),
											_shift(-self.canvas_width*math.cos(angle)  + (self.Width_of_lane*i - self.Width_of_lane*self.Number_of_lanes - 5 + self.Width_of_lane/2 + i)*math.sin(angle),'x'),
											_shift(-self.canvas_height*math.sin(angle) - (self.Width_of_lane*i - self.Width_of_lane*self.Number_of_lanes - 5 + self.Width_of_lane/2 + i)*math.cos(angle),'y'),
											fill="black", width=self.Width_of_lane)
			# RIGHT ROAD
			for i in range(self.Number_of_lanes):
				self.canvas.create_line(	_shift( self.canvas_width*math.cos(angle)  + (self.Width_of_lane*(i+1) - self.Width_of_lane/2 + i)*math.sin(angle),'x'),
											_shift( self.canvas_height*math.sin(angle) - (self.Width_of_lane*(i+1) - self.Width_of_lane/2 + i)*math.cos(angle),'y'),
											_shift(-self.canvas_width*math.cos(angle)  + (self.Width_of_lane*(i+1) - self.Width_of_lane/2 + i)*math.sin(angle),'x'),
											_shift(-self.canvas_height*math.sin(angle) - (self.Width_of_lane*(i+1) - self.Width_of_lane/2 + i)*math.cos(angle),'y'),
											fill="black", width=self.Width_of_lane)
		
		for i in range(self.Number_of_roads):
			angle = 180*i/self.Number_of_roads
			angle = math.radians(angle)	
			# Middle Separator
			self.canvas.create_line(	_shift( self.canvas_width*math.cos(angle) ,'x'),
										_shift( self.canvas_height*math.sin(angle),'y'),
										_shift(-self.canvas_width*math.cos(angle) ,'x'),
										_shift(-self.canvas_height*math.sin(angle),'y'), fill="#a09999", width=2)
	def show_stop_line(self):
		self.canvas.create_rectangle(	_shift(-self.stop_radius,'x'), 
										_shift(-self.stop_radius,'y'), 
										_shift(self.stop_radius,'x'), 
										_shift(self.stop_radius,'y'), outline = 'yellow')
		stop_radius = self.stop_radius - Width_of_lane/4
		self.canvas.create_rectangle(	_shift(-stop_radius,'x'), 
										_shift(-stop_radius,'y'), 
										_shift(stop_radius,'x'), 
										_shift(stop_radius,'y'), outline = 'red')
	def start(self):
		if self.show_gui:
			self.canvas.delete('car_gui')
			# self.draw_roads()
			# self.draw_tower()
		self.draw_cars()
		# self.show_stop_line()
		self.printInfo()
	def close(self):
		self.terminate = True
	def run(self):
		self.start()
		# Frame Rate MAX = 1
		self.after(gui_refresh_rate, self.run)

if __name__ == "__main__":
	"""
		Automated Cars at interface using Reinforcement Learning ...
	"""

	root = tkinter.Tk()
	root.title('AV Simulator 1.0')
	simulator=Simulator(root)
	if simulator.show_gui:
		simulator.pack(side="top", fill="both", expand=True)
	simulator.run()
	time_delay = CAR_TIME_DELAY
	inverse_traffic = INVERSE_TRAFFIC
	for i in range(Number_of_roads*2):
		if True:
			for j in range(Number_of_lanes):
				threading.Thread(target=simulator.creates_cars,args=(i+1,j+1,time_delay,inverse_traffic)).start()
			# break

	try:
		if SHOW_GUI:
			root.mainloop()
	except:
		print('\n\n   Code Exited Forecefully ...\n      Next Time simply try with closing GUI ! insted of [ctrl + C].\n      From Preventing Data Loss.\n')
		simulator.close()
		exit(0)
	try:
		if not SHOW_GUI:
			while True:
				time.sleep(gui_refresh_rate/1000)
				simulator.start()
	except:
		pass
	simulator.close()
	if simulator.total_collisions > 0:
		print('   ACCIDENT PROBABILITY              :',simulator.total_collisions/simulator.number_of_cars_generated)
		print('------------------------------------------------------------------')
	print('\n   Program Exit Success !')
