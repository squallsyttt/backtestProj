# -*- coding: utf-8 -*-
"""
Created on Mon May 15 10:16:27 2023

@author: 61721
"""

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from scipy.optimize import minimize
from scipy.linalg import block_diag
from numpy import *
from numpy.linalg import multi_dot
from sklearn.model_selection import learning_curve,GridSearchCV
from sklearn.model_selection import LeaveOneOut
from scipy.linalg import eigh, cholesky
from scipy.stats import norm
import scipy.optimize as sco

import tushare as ts
pro = ts.pro_api('7e33b6a3e2bad955cd087c9e5a6e69ad34dc797daee4ff6de9cb08f7')

import time
import os

from scipy.cluster.hierarchy import dendrogram
from scipy.cluster.hierarchy import set_link_color_palette
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples
import matplotlib.pylab as plt
import matplotlib
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False


### calculate cov to corr or corr to cov
def cov2corr(cov):
    std = np.sqrt(np.diag(cov)) 
    corr = cov/np.outer(std,std) 
    corr[corr<-1] = -1
    corr[corr>1] = 1
    return corr

def corr2cov(corr, std): 
    cov=corr*np.outer(std,std) 
    return cov

### PCA get eigenvalue
def getPCA(matrix): #corr matrix
    eVal, eVec = np.linalg.eig(matrix) #complex Hermitian (conjugate symmetric) or a real symmetric matrix.
    indices = eVal.argsort()[::-1] #arguments for sorting eval desc
    eVal,eVec = eVal[indices],eVec[:,indices]
    eVal = np.diagflat(eVal) # identity matrix with eigenvalues as diagonal
    return eVal,eVec

###GridSearch find bWidth
def findOptimalBWidth(eigenvalues):
    bandwidths = 10 ** np.linspace(-1, 1, 100)
    grid = GridSearchCV(KernelDensity(kernel='gaussian'),
                        {'bandwidth': bandwidths},
                        cv=LeaveOneOut())
    grid.fit(eigenvalues[:, None]);
    return grid.best_params_

### denoise use random matrix
def mpPDF(var,q,pts):
    eMin,eMax = var*(1-(1./q)**.5)**2, var*(1+(1./q)**.5)**2
    eVal = np.linspace(eMin, eMax, pts)
    pdf = q/(2*np.pi*var*eVal)*((eMax-eVal)*(eVal-eMin))**.5
    pdf = pd.Series(pdf, index=eVal)
    return pdf

def fitKDE(obs, bWidth, kernel='gaussian', x=None):
    #Fit kernel to a series of obs, and derive the prob of obs
    # x is the array of values on which the fit KDE will be evaluated
    #print(len(obs.shape) == 1)
    if len(obs.shape) == 1: obs = obs.reshape(-1,1)
    kde = KernelDensity(kernel = kernel, bandwidth = bWidth).fit(obs)
    #print(x is None)
    if x is None: x = np.unique(obs).reshape(-1,1)
    #print(len(x.shape))
    if len(x.shape) == 1: x = x.reshape(-1,1)
    logProb = kde.score_samples(x) # log(density)
    pdf = pd.Series(np.exp(logProb), index=x.flatten())
    return pdf

def errPDFs(var, eVal, q, bWidth, pts=1000):
    var = var[0]
    pdf0 = mpPDF(var, q, pts) #theoretical pdf
    pdf1 = fitKDE(eVal, bWidth, x=pdf0.index.values) #empirical pdf
    sse = np.sum((pdf1-pdf0)**2)
    #print("sse:"+str(sse))
    return sse 

def findMaxEval(eVal, q, bWidth):
    out = minimize(lambda *x: errPDFs(*x), x0=np.array(0.5), args=(eVal, q, bWidth), bounds=((1E-5, 1-1E-5),))
    print("found errPDFs"+str(out['x'][0]))
    if out['success']: var = out['x'][0]
    else: var=1
    eMax = var*(1+(1./q)**.5)**2
    return eMax, var

###calculate denoise corr
def denoisedCorr(eVal,eVec,nFacts):
# Remove noise from corr by fixing random eigenvalues
    eVal_=np.diag(eVal).copy()
    eVal_[nFacts:]=eVal_[nFacts:].sum()/float(eVal_.shape[0]-nFacts)
    eVal_=np.diag(eVal_)
    corr1=np.dot(eVec,eVal_).dot(eVec.T)
    corr1=cov2corr(corr1)
    return corr1

def cal_corr(data,start,end):
    df = data[start:end]
    riskfree = 0.02
    
    excess_returns = df.pct_change().fillna(0) - riskfree/252
    
    annual_rtn = excess_returns.mean()*252
    
    annual_rtns = array(excess_returns.mean()*252)[:,newaxis]
    
    annual_vols = (excess_returns.std()*sqrt(252))[:,newaxis]
    
    cov = excess_returns.cov()*252
    corr = cov2corr(cov)
    eigenvalues,eigenvectors = getPCA(corr)
    
    bWidth = findOptimalBWidth(np.diag(eigenvalues))['bandwidth']
    T = excess_returns.shape[0]
    N = float(excess_returns.shape[1])
    q = T/N
    var=1
    pts = int(N)
    eMAX0, var0 = findMaxEval(np.diag(eigenvalues), q, bWidth)
    nFacts0 = eigenvalues.shape[0]-np.diag(eigenvalues)[::-1].searchsorted(eMAX0)
    corr_denoise = denoisedCorr(eigenvalues,eigenvectors,nFacts0)
    cor_denoise2 = pd.DataFrame(corr_denoise,columns = corr.columns, index = corr.index)
    cov_denoise = corr2cov(corr_denoise, annual_vols)
    cov_denoised = pd.DataFrame(cov_denoise,columns = corr.columns, index = corr.index)
    return cor_denoise2,cov_denoised,annual_rtn


# df_1 = pd.read_csv('C:\\jupyter_work\\port_mana\\FOF_20221208.csv',encoding='gbk',index_col=0)
# df_1.index = pd.to_datetime(df_1.index)

# start = '2021-8-31'
# end = '2023-5-12'
# cor = cal_corr(df_1,start,end)[0]