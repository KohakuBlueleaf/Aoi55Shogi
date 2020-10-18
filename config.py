import numpy as np
from BlueNet.Network import Net
from BlueNet.Layer import *
from BlueNet.Activation import GELU,Tanh
from BlueNet.Optimizer import Adam
from BlueNet.Functions import RMS
from BlueNet.setting import _np as cp

rn = cp.random.randn

conv_model = [	
				Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				ResV1([	Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1}),
						Conv({'f_num':128, 'f_size':3, 'pad':1, 'stride':1})]),
				]
conv_net = Net(conv_model, (21,7,5), GELU, Adam, 0.001, 0, 'xaiver', np.float32)
#conv_net.print_size()

policy_model = [Conv({'f_num':32, 'f_size':1, 'pad':0, 'stride':1}),
				Flatten(),
				Dense(1725),
				SoftmaxWithLoss()]
policy_net = Net(policy_model, (128,7,5), GELU, Adam, 0.001, 0, 'xaiver', np.float32)
#policy_net.print_size()

value_model = [	Conv({'f_num':3, 'f_size':1, 'pad':0, 'stride':1}),
				Flatten(),
				Dense(200),
				Dense(1,AF=Tanh),
				]
value_net = Net(value_model, (128,7,5), GELU, Adam, 0.001, 0, 'xaiver', np.float32)
#value_net.print_size()


if __name__=='__main__':
	test = rn(1,21,7,5)
	print(value_net.process(conv_net.process(test)))
