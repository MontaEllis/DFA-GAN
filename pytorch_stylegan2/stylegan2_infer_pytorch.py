import torch
from torchvision import utils
import sys
import os
sys.path.append(os.getcwd()+'/pytorch_stylegan2')
from stylegan2_model import Generator,Discriminator
from tqdm import tqdm
from torch.nn import functional as F
from hparams import hparams as hp



class infer_face():
    
    def __init__(self,weight_path):
        
        self.device = "cuda"
        self.weight_path = weight_path


        self.num_truncation_mean = 4096

        self.truncation = 0.5

        self.checkpoint = torch.load(self.weight_path)

        self.g_ema = Generator(256, 512, 8, channel_multiplier=2).to(self.device)
        self.g_ema.load_state_dict(self.checkpoint["g_ema"])
        self.g_ema.eval()
        for parm in self.g_ema.parameters():
            parm.requires_grad = False


        self.discriminator = Discriminator(256, channel_multiplier=2).to(self.device)
        self.discriminator.load_state_dict(self.checkpoint["d"])


        if self.truncation < 1:
            with torch.no_grad():
                self.mean_latent = self.g_ema.mean_latent(self.num_truncation_mean)
        else:
            self.mean_latent = None

    

    def random_init_w(self):
        sample_z = torch.randn(1, 512, device=self.device)
        w = self.g_ema.get_latent(sample_z)

        # with torch.no_grad():
        #     _, w = self.g_ema([sample_z], truncation=0.5, return_latents=True,truncation_latent=self.mean_latent)
        return w[0]

    def g_nonsaturating_loss(self,fake_pred):
        loss = F.softplus(-fake_pred).mean()

        return loss


    
    def generate_from_synthesis(self, w, direction):
        if direction is not None:
            if torch.is_tensor(direction):
                pass
            else:
                direction = torch.Tensor(direction).float().cuda()
            latent_code = (w + direction)
        else:
            latent_code = w

        sample, _ = self.g_ema(
                [latent_code], truncation=0.5, input_is_latent=True, truncation_latent=self.mean_latent
            )
 
        return sample

    def disc(self,img):

        fake_pred = self.discriminator(img)
        loss = self.g_nonsaturating_loss(fake_pred)
        # print(fake_pred)
        return loss

