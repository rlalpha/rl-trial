# A VAE in RNN

import torch
import torch.nn as nn
import torch.nn.functional as F

########Definition of the architecture of our encoder and decoder model with all the assisting functions

class VAE(nn.Module):
	def __init__(self, num_latent, state_size, filter_size=[3, 3, 3], channels=[1, 4, 20, 20]):
		super().__init__()
		
		#So here we will first define layers for encoder network
		self.encoder = nn.Sequential(nn.Conv2d(channels[0], channels[1], filter_size[0], padding=1),
									 nn.MaxPool2d(2, 2),
									 nn.BatchNorm2d(channels[1]),
									 nn.Conv2d(channels[1], channels[2], filter_size[1], padding=1),
									 nn.MaxPool2d(2, 2),
									 nn.BatchNorm2d(channels[2]),
									 nn.Conv2d(channels[2], channels[3], filter_size[2], padding=1))
		
		#These two layers are for getting logvar and mean
		encoder_out_size = state_size / 4
		self.fc1_in_shape = [-1, channels[3], encoder_out_size, encoder_out_size]
		self.fc1_in_size = channels[3] * filter_size[2] * encoder_out_size
		fc2_in_size = fc1_in_size / 3
		fc2_out_size = fc2_in_size / 2
		self.fc1 = nn.Linear(fc1_in_size, fc2_in_size)
		self.fc2 = nn.Linear(fc2_in_size, fc2_out_size)
		self.mean = nn.Linear(fc2_out_size, num_latent)
		self.var = nn.Linear(fc2_out_size, num_latent)
		
		#######The decoder part
		#This is the first layer for the decoder part
		self.expand = nn.Linear(num_latent, fc2_out_size)
		self.fc3 = nn.Linear(fc2_out_size, fc2_in_size)
		self.fc4 = nn.Linear(fc2_in_size, fc1_in_size)
		self.decoder = nn.Sequential(nn.ConvTranspose2d(channels[3], channels[2], 3, padding=1),
									 nn.BatchNorm2d(channels[2]),
									 nn.ConvTranspose2d(channels[2], channels[1], 8),
									 nn.BatchNorm2d(channels[1]),
									 nn.ConvTranspose2d(channels[1], channels[0], 15))
		
	def enc_func(self, x):
		#here we will be returning the logvar(log variance) and mean of our network
		x = self.encoder(x)
		x = x.view([-1, self.fc1_in_size])
		x = F.dropout2d(self.fc1(x), 0.5)
		x = self.fc2(x)
		
		mean = self.mean(x)
		logvar = self.var(x)
		return mean, logvar
	
	def dec_func(self, z):
		#here z is the latent variable state
		z = self.expand(z)
		z = F.dropout2d(self.fc3(z), 0.5)
		z = self.fc4(z)
		z = z.view(self.fc1_in_shape)
		
		out = self.decoder(z)
		out = F.sigmoid(out)
		return out
	
	def get_hidden(self, mean, logvar):
		if self.training:
			std = torch.exp(0.5*logvar)   #So as to get std
			noise = torch.randn_like(mean)   #So as to get the noise of standard distribution
			return noise.mul(std).add_(mean)
		else:
			return mean
	
	def forward(self, x):
		mean, logvar = self.enc_func(x)
		z = self.get_hidden(mean, logvar)
		out = self.dec_func(z)
		return out, mean, logvar

#######This is the custom loss function defined for VAE
### You can even refere to: https://github.com/pytorch/examples/pull/226 

def VAE_loss(out, target, mean, logvar):
	category1 = nn.BCELoss()
	bce_loss = category1(out, target)
	
	#We will scale the following losses with this factor
	scaling_factor = out.shape[0]*out.shape[1]*out.shape[2]*out.shape[3]
	
	####Now we are gonna define the KL divergence loss
	# 0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
	kl_loss = -0.5 * torch.sum(1 + logvar - mean**2 - torch.exp(logvar))
	kl_loss /= scaling_factor
	
	return bce_loss + kl_loss

######The function which we will call for training our model

def train(trainloader, iters, model, device, optimizer, print_every):
	counter = 0
	for i in range(iters):
		model.train()
		model.to(device)
		for images, _ in trainloader:
			images = images.to(device)
			optimizer.zero_grad()
			out, mean, logvar = model(images)
			loss = VAE_loss(out, images, mean, logvar)
			loss.backward()
			optimizer.step()
			
		if(counter % print_every == 0):
			model.eval()
			n = 10  # figure with 20x20 digits
			digit_size = 28
			figure = np.zeros((digit_size * n, digit_size * n))

			# Construct grid of latent variable values
			grid_x = norm.ppf(np.linspace(0.05, 0.95, n))
			grid_y = norm.ppf(np.linspace(0.05, 0.95, n))

			counter = 0
			# decode for each square in the grid
			for i, yi in enumerate(grid_x):
				for j, xi in enumerate(grid_y):
					digit = out[counter].squeeze().cpu().detach().numpy()
					figure[i * digit_size: (i + 1) * digit_size,
						   j * digit_size: (j + 1) * digit_size] = digit
					counter += 1

			plt.figure(figsize=(10, 10))
			plt.imshow(figure, cmap='bone')
			plt.show()  

		counter += 1