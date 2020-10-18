from pickle import dump,load
from copy import copy,deepcopy
from time import time,sleep
from random import shuffle,randint

import numpy as np
from numpy.random import choice
from numpy import log,sqrt
from pandas import Series

from multiprocessing import *
from minishogi import *
import sys



class mctsNode:
	def __init__(self, state, parent=None):
		self.state = copy(state)
		self.untried = state.situation()[2]
		self.parent = parent
		self.children = {}
		self.is_end = len(self.untried)==0
		
		if self.is_end:
			self.Q = self.state.situation()[1]
			self.N = 1
		else:
			self.Q=0
			self.N=0
	
	def weight(self, c_param=1):
		if self.N:
			w = -self.Q/self.N + c_param*sqrt(log(self.parent.N)/self.N)
		else:
			w = 0.0
		
		return w
	
	@staticmethod
	def get_random_action(available):
		action_num = len(available)
		action_id = choice(range(action_num))
		
		return available[action_id]
	
	def select(self, c_param=1.414):
		weights = [child.weight(c_param) for child in self.children.values()]
		action = Series(data = weights, index=self.children.keys()).idxmax()
		next_node = self.children[action]
		
		return action, next_node
	
	def expand(self):
		action = self.untried.pop()
		cur_pl = self.state.pl
		
		next_board = copy(self.state.Board)
		next_board.move(action, self.state.pl)
		
		next_player = 1-self.state.pl
		
		state = State(next_board, next_player)
		child_node = mctsNode(state,self)
		self.children[action] = child_node

		return child_node
	
	def update(self, winner):
		self.N += 1
		opponent = 1-self.state.pl
		
		if winner==self.state.pl:
			self.Q += 1
		elif winner==opponent:
			self.Q -= 1
		
		if self.parent!=None:
			self.parent.update(winner)
	
	def rollout(self):
		a = copy(self.state.Board)
		if a.is_end()!=0:
			return 1 if a.is_end()==1 else 0
		player = self.state.pl
		
		T0 = time()
		while True:
			move = a.available(player, all=False, random=True)
			if move==None:
				break
			a.move(move, player)
			
			player = not player
		
		winner = a.is_end()
		return (-1,1,0)[winner]
	
	def is_full_expand(self):
		return not len(self.untried)
	
	def is_root_node(self):
		return self.parent

def play_rollout(node):
	return node.rollout()
	
class MCTS:
	def __init__(self):
		self.root = None
		self.cur_node = None
		
	def simulation(self, count=50):
		for _ in range(count):
			print(f'{_+1}/{count}',end='\r')
			leaf_node = self.simulation_policy()
			winner = leaf_node.rollout()
			leaf_node.update(winner)
	
	def simulation_policy(self):
		cur_node = self.cur_node
		while True:
			is_over, _, _ = cur_node.state.situation()
			if is_over:
				break
			
			if cur_node.is_full_expand():
				_, cur_node = cur_node.select()
			else:
				return cur_node.expand()
		leaf_node = cur_node
		return leaf_node
	
	def take_action(self, cur_state, s=10000):
		if not self.root:
			self.root = mctsNode(cur_state, None)
			self.cur_node = self.root
		else:
			for child_node in self.cur_node.children.values():
				if child_node.state == cur_state:
					self.cur_node = child_node
					break
		
		if cur_state==self.root.state:
			self.cur_node = self.root
		
		if self.cur_node.is_end:
			return None
			
		self.simulation(s)
		action, next_node = self.cur_node.select(0.0)
		self.cur_node = next_node
		return action
	
	def next_state(self, cur_state):
		if self.cur_node.state==cur_state:
			return 
		while not self.cur_node.is_full_expand():
			new = self.cur_node.expand()
			winner = new.rollout()
			new.update(winner)

		for child_node in self.cur_node.children.values():
			if child_node.state == cur_state:
				self.cur_node = child_node
				return
		
	
	def end_play(self,winner):
		self.cur_node.update(winner)
		self.cur_node = self.root #回到最初棋局

def MCTSplay(player=MCTS(),s=100,savepath='./mcts',pl=1,human=False, h_first=0):
	a = miniShogi(deepcopy(initial_board))
	print(a)
	
	his = 0
	while True:
		if human:
			if pl==h_first:
				if a.is_end():
					break
				while True:
					x,y = [int(i) for i in input("輸入棋步:").strip().split()]
					move = x*a.x+y
					if move not in a.available(pl):
						print("不合法的棋步")
					else:
						break
			else:
				move = player.take_action(State(a,pl),s)
		else:
			move = player.take_action(State(a,pl),s)
		print('第{:2}手: '.format(his+1), end='')
		a.print_step(move,pl)
		a.move(move, pl)
		print(a)
		
		end,winner = a.is_end()
		if end:
			break
		
		player.next_state(State(a,pl))
		pl = 1-pl
		his += 1
	
	player.end_play((-1,1,0)[winner])
	print('對局結束')
	if savepath and player.root.N<5000000:
		with open(savepath, 'wb') as f:
			dump(player,f)

if __name__=='__main__':
	try:
		with open('./Aoi5五將棋.mcts', 'rb') as f:
			player = load(f)
	except FileNotFoundError:
		player = MCTS()
		
	for j in range(1000):
		#i = int(input('選擇先手後手(1,先手 0,後手):').strip())
		#if i=='':
		#	break
		MCTSplay(player,1000,savepath='./Aoi5五將棋.mcts',human=False,h_first=1)
