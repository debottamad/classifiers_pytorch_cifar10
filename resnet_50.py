import torch
import torch.nn as nn
from torch.nn.modules.batchnorm import BatchNorm2d
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

class block(nn.Module):
    def __init__(self,in_channels,out_channels,identity_downsample=None,stride=1):
        super(block,self).__init__()
        self.expansion=4
        self.conv1=nn.Conv2d(in_channels,out_channels,kernel_size=1,stride=1,padding=0)
        self.bn1=nn.BatchNorm2d(out_channels)
        self.conv2=nn.Conv2d(out_channels,out_channels,kernel_size=3,stride=stride,padding=1)
        self.bn2=nn.BatchNorm2d(out_channels)
        self.conv3=nn.Conv2d(out_channels,out_channels*self.expansion,kernel_size=1,stride=1,padding=0)
        self.bn3=BatchNorm2d(out_channels*self.expansion)
        self.relu=nn.ReLU()
        self.identity_downsample=identity_downsample
    
    def forward(self,x):
        identity=x
        x=self.conv1(x)
        x=self.bn1(x)
        x=self.relu(x)
        x=self.conv2(x)
        x=self.bn2(x)
        x=self.relu(x)
        x=self.conv3(x)
        x=self.bn3(x)
        x=self.relu(x)

        if self.identity_downsample is not None:
            identity=self.identity_downsample(identity)
        x+=identity
        x=self.relu(x)
        return x

class Resnet(nn.Module):#layers in resnet 50 [3,4,6,3]
    def __init__(self,block,layers,image_channels,num_classes):
        super(Resnet,self).__init__()
        #initial layers of resnet
        self.in_channels=64
        self.conv1=nn.Conv2d(image_channels,64,kernel_size=7,stride=2,padding=3)
        self.bn1=nn.BatchNorm2d(64)
        self.relu=nn.ReLU()
        self.max1=nn.MaxPool2d(kernel_size=3,stride=2,padding=1)
        self.layer1=self.make_layer(block,layers[0],out_channels=64,stride=1)
        self.layer2=self.make_layer(block,layers[1],out_channels=128,stride=2)
        self.layer3=self.make_layer(block,layers[2],out_channels=256,stride=2)
        self.layer4=self.make_layer(block,layers[3],out_channels=512,stride=2)
        self.avgpool=nn.AdaptiveAvgPool2d(1,1)
        self.fc1=nn.Linear(512*4,num_classes)
        self.softmx=nn.Softmax()

    def forward(self,x):
        x=self.conv1(x)
        x=self.bn1(x)
        x=self.relu(x)
        x=self.max1(x)
        x=self.layer1(x)
        x=self.layer2(x)
        x=self.layer3(x)
        x=self.layer4(x)
        x=self.avgpool(x)
        x=self.fc1(x)
        x=self.softmx(x)

    def make_layer(self,block,num_residual_block,out_channels,stride):
        identity_downsample=None
        layers=[]
        if stride != 1 or self.in_channels != out_channels*4:
            identity_downsample=nn.Sequential(nn.Conv2d(self.in_channels,out_channels*4,kernel_size=1,stride=stride)),nn.BatchNorm2d(out_channels*4)

        layers.append(block(self.in_channels,out_channels,identity_downsample,stride))
        self.in_channels=out_channels*4

        for i in range(num_residual_block-1):
            layers.append(block(self.in_channels,out_channels))
       
        return nn.Sequential(*layers)