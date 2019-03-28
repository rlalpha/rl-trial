
from vae import vae_module
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt

def use_vae():
	IMAGE_SIZE = 88
	x = []

	def resize(img, size):
		return cv2.resize(img, size, interpolation=cv2.INTER_AREA)

	def rgb2gray(img):
		return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	def img_transform(img):
		gray_image = rgb2gray(img)
		matrix = resize(gray_image, size=(IMAGE_SIZE, IMAGE_SIZE))
		matrix = matrix / 255.0
		return matrix.reshape(1, matrix.shape[0], matrix.shape[1]).astype(np.float32)

	def draw_function(l):
		nonlocal x
		x.append(l)
		plt.plot(x, 'b-')
		plt.title('loss')
		# plt.show('VAE Loss')
		plt.savefig('VAE_Loss.png')
		print(l)

	img_size = IMAGE_SIZE**2
	num_latent = 1024

	vae = vae_module(num_latent, img_size, img_transform)
	vae.train(26, 5, draw_function)

	vae.save()

use_vae()