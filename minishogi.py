from copy import copy,deepcopy
from time import time,sleep
from random import choice,shuffle,randint
from multiprocessing import Pool
import sys



def get_str(s, limit=6):
	'''
	自製format用來限制長度並判斷全半形
	'''
	s = str(s)
	res = ''
	amount = 0
	for i in s:
		amount += 1 if ord(i)<10000 else 2
		if amount>limit:
			amount -= 1 if ord(i)<10000 else 2
			break
		res += i
	
	res = ' '*(limit-amount) + res
	return res

initial_board = [[ 0,  0,  0,  0,  0],
				[ -5, -4, -2, -3,-10],
				[  0,  0,  0,  0, -1],
				[  0,  0,  0,  0,  0],
				[  1,  0,  0,  0,  0],
				[ 10,  3,  2,  4,  5],
				[  0,  0,  0,  0,  0]]

F = False
T = True
nums = ('','一','二','三','四','五')
cnums = {i:j for i,j in zip(nums,range(10))}
position = tuple((i,j) for i in range(1,6) for j in range(5))

s = range(1,5)
all_steps = [(-i, 0, F) for i in s]+\
			[( 0, i, F) for i in s]+\
			[( i, 0, F) for i in s]+\
			[( 0,-i, F) for i in s]+\
			[(-i,-i, F) for i in s]+\
			[(-i, i, F) for i in s]+\
			[( i, i, F) for i in s]+\
			[( i,-i, F) for i in s]

all_steps += [(i[0],i[1],T) for i in all_steps]
all_steps = tuple(all_steps)

routes = [[],1,2,3,4,5,6,7,8,9,10,11]
routes[1] = (0,)
routes[2] = (0,16,20,24,28)
routes[3] = (0,4,8,12,16,20)
routes[4] = (19,23,27,31)
routes[5] = (3,7,11,15)
routes[6] = routes[7] = (0,4,8,12,16,20)
routes[8] = (0,4,8,12,19,23,27,31)
routes[9] = (16,20,24,28,3,7,11,15)
routes[10] = (0,4,8,12,16,20,24,28)
routes = tuple(routes)

chesses = ('','步','銀','金','角','飛','成步','成銀','馬','龍','王')
up_map = (0,6,7,0,8,9,1,2,4,5)
chess_map = {}
for i in range(10):
	chess_map[chesses[i]] = i

pl_icon = ('▽','△')
value_table = [0,1,8,9,18,20,7,8,20,22,0]

class miniShogi:
	def __init__(self, board=eval(str(initial_board))):
		self.board = board
		self.complexity = 1725
		self.his = {}
	
	def __copy__(self):
		return miniShogi(eval(str(self.board)))
	
	#印出盤面 
	#Linux跟Windows的terminal的格式不同 
	#linux要將get_str函數的ord(s)<改成10000 windows要9000
	def __str__(self):
		a,b,c,d,e = self.board[0]
		out = '┌──────'+'┬──────'*4+'┐'
		spliter = '\n├──────'+'┼──────'*4+'┤'
		
		out += '\n│ 步:{:2}│ 銀:{:2}│ 金:{:2}│ 角:{:2}│ 飛:{:2}│'\
				.format(a,b,c,d,e)
		out += spliter*2+'\n│'
		
		for i in self.board[1:6]:
			for j in range(5):
				if i[j]>0:
					now = get_str('△'+chesses[abs(i[j])])
				elif i[j]<0:
					now = get_str('▽'+chesses[abs(i[j])])
				else:
					now = '      '
				out += '{}│'.format(now)
			out += spliter+'\n│'
		out = out[:-2]
		
		a,b,c,d,e = self.board[-1]
		out += spliter
		out += '\n│ 步:{:2}│ 銀:{:2}│ 金:{:2}│ 角:{:2}│ 飛:{:2}│'\
				.format(a,b,c,d,e)
		out += '\n└──────'+'┴──────'*4+'┘'
		return out
		
	#移動
	def move(self,s, pl):
		pos,move = s//69, s%69
		x,y = pos//5+1, pos%5
		self_c = -1 if pl else 0
		
		if move>63: 			#打入
			chess = move-63
			self.board[self_c][chess-1]-=1
			self.board[x][y] = chess*(1 if pl else -1)
		else:					#一般操作
			m = all_steps[move]
			r, c, up = m
			if not pl:r = -r
						
			nx,ny = x+r, y+c
			origin = self.board[x][y]
			on = abs(self.board[nx][ny])
			self.board[x][y], self.board[nx][ny] = 0, origin
			
			if on and on!=10:
				if on<6:
					self.board[self_c][on-1] += 1
				else:
					self.board[self_c][up_map[on]-1] += 1
			
			if up:
				self.board[nx][ny] = up_map[abs(origin)]
				if not pl:
					self.board[nx][ny] *= -1
		
		self.his[str(self.board)] = self.his.get(str(self.board),0)+1
	
	def total(self):
		count = {}
		for i,j in position:
			now = self.board[i][j]
			count[abs(now)] = count.get(abs(now),0)+1
		
		return count
	
	def available(self,player, all=True, random=False):
		doable = []						#可行棋步
		self_c = -1 if player else 0	#持駒所在行數
		own = self.board[self_c]		#持駒
		
		for i,j in position:			#遍歷棋盤
			now = self.board[i][j]		#現在的棋子
			n = abs(now)				#(正為先手負為後手)
			now_pos = ((i-1)*5+j)*69	#可行棋步為一維array儲存 故計算出這個位置的棋步起始位置
			
			if now==0:					#打入
				#步/香（不能打在最後一排)
				if (i>1 and player) or (i<5 and not player):
					if own[0]>0:		
						pawn2 = False	#二步偵測
						for r in range(1,6):
							if r==i:continue
							k = self.board[r][j]
							if abs(k)==1 and (k>0)==player:
								pawn2 = True
								break
								
						if not pawn2:	#打步詰偵測(前方是否為王將 是的話有沒有造成將死)
							if self.board[i+(-1 if player else 1)][j]==(-10 if player else 14): 
								temp = copy(self)
								temp.move(now_pos+64, player)
								if temp.available(not player,all=False)!=None:
									doable.append(now_pos+64)
							else:
								doable.append(now_pos+64)

				#金銀飛角
				for i in range(1,5):
					if own[i]>0:
						doable.append(now_pos+64+i)
			
			#自己的棋
			elif (now>0)==player:				#棋子是現在的玩家的
				for s in routes[n]:				#遍歷可行走法並判斷合法與否
					x, y, _ = all_steps[s]		#讀取走法的x變化及y變化
					x *= (1 if player else -1)	#如果是後手要上下顛倒
					
					if s%4==0:					#步銀金王
						now_x, now_y = x+i, y+j	#移動之後的位置
						next = now_x+x			#下下步的X位置
						
						#超過範圍
						if not (1<=now_x<=5 and 0<=now_y<=4):
							continue

						#偵測目標位置是否已經有棋 如果有則判斷是否為敵方
						on = self.board[now_x][now_y]
						if not on or (on>0)!=player:
							#強制升變（下下步超出範圍)
							if n<2 and (1>next or next>5):
								doable.append(now_pos+s+32)
								continue
							
							#升變判斷(步銀角飛)
							#從移動後停在敵陣或從移動起點在敵陣都能升變
							if player:	#先手的升變判斷
								if (now_x==1 or i==1) and n<6 and n!=3:
									doable.append(now_pos+s+32)
							else:		#後手的升變判斷
								if (now_x==5 or i==5) and n<6 and n!=3:
									doable.append(now_pos+s+32)
							doable.append(now_pos+s)

					else:						#角飛龍馬
						#方向
						x_d = y_d = 0
						if x: x_d = 1 if x>0 else -1
						if y: y_d = 1 if y>0 else -1
						
						#從動一格開始找
						step = s-4
						now_x, now_y = i,j
						for k in range(1,5):
							step += 1
							now_x += x_d; now_y += y_d
							
							#超出範圍
							if not (0<now_x<6 and -1<now_y<5):
								break
							else:
								on = self.board[now_x][now_y]
							
								#移動位置沒有棋或棋子為敵方的
								if not on or (on<0)==player:
									if player:	#先手的升變判斷
										if (now_x==1 or i==1) and n<6:
											doable.append(now_pos+step+32)
									else:		#後手的升變判斷
										if (now_x==5 or i==5) and n<6:
											doable.append(now_pos+step+32)
										
									doable.append(now_pos+step)
									if on:		#棋子為敵方的在吃了之後停下
										break
								else:
									break
		
		if random:
			shuffle(doable)
		
		chosen = []						#expand的所有子節點(概念上)
		while True:						#過濾自殺棋步
			move = None
			while doable:
				move = doable.pop()		#選擇檢查棋步
				temp = copy(self)		#複製一個自己
				temp.move(move,player)	#移動選擇棋步
				
				#檢查是否被對方將軍
				if temp.is_checkmate(1-player)==False and temp.get_repeat()<2:
					break
				else:
					move = None
			
			#沒有多的可行棋步
			if move==None:
				break
			else:
				if all:
					chosen.append(move)
				else:
					return move
		if all:
			return chosen
		else:
			return None
	
	def get_repeat(self):
		return self.his.get(str(self.board),0)
	
	def is_end(self):
		first = self.available(1,all=False)
		second = self.available(0,all=False)
		
		if first==None:					#先手無路可走
			return 2
		elif second==None:				#後手無路可走
			return 1
		
		board = str(self.board)			#同一盤面出現四次:千日手
		if board in self.his and self.his[board]>=4:
			if self.is_checkmate(1):	#先手連續王手的千日手 後手勝
				return 2
			elif self.is_checkmate(0):	#後手連續王手的千日手 先手勝
				return 1
			else:						#千日手 平手
				return 0
				
		return 0
	
	#利用available的算法偵測有沒有on包含14(王)
	def is_checkmate(self,pl):
		checkmate = False
		
		for i,j in position:
			now = self.board[i][j]
			if now and (now>0)==pl:
				for s in routes[abs(now)]:
					x, y, _ = all_steps[s]
					x = x if pl else -x
					
					if s%4==0:	#步銀金王
						now_x, now_y = i+x, j+y
						if not (0<now_x<6 and -1<now_y<5):
							continue
						on = self.board[now_x][now_y]
						if abs(on)==10 and (on<0)==pl:
							return True
					
					else:#香角飛龍馬
						#方向
						x_d = y_d = 0
						if x: x_d = 1 if x>0 else -1
						if y: y_d = 1 if y>0 else -1
						
						#從動一格開始找
						for k in range(1,5):
							now_x, now_y = k*x_d+i, k*y_d+j
							
							if now_x<1 or now_x>5 or now_y<0 or now_y>4:
								break
							else:
								on = self.board[now_x][now_y]
							
								if abs(on)==10 and (on<0)==pl:
									return True
								if on:
									break
		return False

	#利用available的算法偵測有沒有其他可以到達目標位置的棋步
	#用來判斷棋譜的左右上直寄引
	def is_same(self,pl,pos,chess):
		same = []
		avai = routes[abs(chess)]
		
		for i,j in position:
			now = self.board[i][j]
			if now==chess:
				for s in avai:
					x, y, _ = all_steps[s]
					x = x if pl else -x
					
					if s%4==0:	#步銀金王
						now_x, now_y = i+x, j+y
						if (now_x,now_y)==pos:
							same.append((j+1,i))
					
					else:#香角飛龍馬
						#方向
						x_d = y_d = 0
						if x: x_d = 1 if x>0 else -1
						if y: y_d = 1 if y>0 else -1
						
						#從動一格開始找
						for k in range(1,5):
							now_x, now_y = k*x_d+i, k*y_d+j
							
							if now_x<1 or now_x>5 or now_y<0 or now_y>4:
								break
							else:
								on = self.board[now_x][now_y]

								if (now_x,now_y)==pos:
									same.append((j+1,i))
								if on:
									break
		return same
		
	#印出棋步
	@staticmethod	
	def get_info(pl,target, move, other):
		x,y = target
		m_x,m_y = move
		d_x,d_y = m_x<x,m_y<y
		
		if m_x==x:
			if d_y == pl:
				return '引'
			else:
				return '直'
		elif m_y==y:
			horizon = True
			for i in other:
				if i[1]==y:
					horizon = False
					break
			
			if horizon:
				return '寄'
			else:
				return '右' if d_x==pl else '左'
		else:
			tag = d_x
			side_only = True
			for i in other:
				if i[0]<x==tag:
					side_only=False
					break
			
			if side_only:
				return '右' if d_x==pl else '左'
			else:
				if y==m_y:
					return '右寄' if d_x==pl else '左寄'
				elif d_x==pl:
					return '右引' if d_y==pl else '右上'
				elif d_x!=pl:
					return '左引' if d_y==pl else '左上'
	
	def print_step(self,s,first,end='\n',p=True):
		pos,move = divmod(s,69)
		x,y = position[pos]
		
		da = move>63
		if da:
			chess = chesses[move-63]
			out = '{}{}{}{}打'.format(pl_icon[first], 5-y, nums[x], chess)
		else:
			m = all_steps[move]
			if not first:
				m = (-m[0],m[1],m[2])
			c = m[2]
			
			chess = chesses[abs(self.board[x][y])]
			pos = (5-(y+m[1]),x+m[0])
			
			info = ''
			same = self.is_same(first, (pos[1],y+m[1]), self.board[x][y])
			if len(same)>1:
				same.remove((y+1,x))
				info = self.get_info(first,(pos[0],pos[1]),(5-y,x),same)
			
			x,y = pos[0], nums[pos[1]]
			out ='{}{}{}{}{}{}'.format(pl_icon[first], x, y, chess, info, '成'if c else '')
		
		if p:
			print(out, end=end)
		return out

empty = [[[0]*5 for i in range(7)] for i in range(21)]
class State:
	def __init__(self, board, pl):
		self.pl = pl
		self.Board = copy(board)
	
	def __str__(self):
		return self.Board.__str__()
	
	def __eq__(self,other):
		return self.pl==other.pl and self.Board.board==other.Board.board
	
	def encode(self):
		output = eval(str(empty))
		
		for i in range(7):
			for j in range(5):
				now = self.Board.board[i][j]
				output[now+10][i][j] = 1
		
		return output
		
	def situation(self):
		actions = self.Board.available(self.pl)
		if actions:
			return False, None, actions
		else:
			return True, 1-self.pl, []
	
	def get_next(self,move):
		temp = copy(self.Board)
		temp.move(move, self.pl)
		new = State(temp, 1-self.pl)
		
		return new
	def __copy__(self):
		return State(copy(self.Board), self.pl)

def random_play(x):	
	a = miniShogi()
	player = 1
	his = 1
	
	T0 = time()
	while True:
		move = a.available(player, False, True)
		if move==None:
			break
		
		#print('\n第{:2}手: '.format(his+1), end='')
		#a.print_step(move,player)
		a.move(move, player)
		#print(a)
		
		his += 1
		player = not player
	T1 = time()
	
	return 1-player
	print('Total Move: {}'.format(his))
	print('Total Cost: {}s'.format(str(T1-T0)[:5]))
	print('Each Cost : {}us'.format(str((T1-T0)/his*1000000)[:5]))
	print('Winner    : {}'.format('先手' if not player else '後手'))
	

if __name__ =='__main__':
	pool = Pool(50)
	amount = 10000
	data = pool.map(random_play, range(amount))
	print('局數:{} 先手獲勝次數:{}'.format(len(data), sum(data)))
	pool.close()
	pool.join()
	
