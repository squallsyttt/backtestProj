# -*- coding: utf-8 -*-
"""
Created on Tue May 16 20:43:14 2023

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


def clusterKMeansBase1(corr0,maxNumClusters=6,n_init=10):
    x,silh=((1-corr0.fillna(0))/2.)**.5,pd.Series()# observations matrix
    for init in range(n_init):
        for i in range(2,maxNumClusters+1):
            #kmeans_=KMeans(n_clusters=i,n_jobs=1,n_init=10)
            kmeans_=KMeans(n_clusters=i,n_init=10)
            kmeans_=kmeans_.fit(x)
            silh_=silhouette_samples(x,kmeans_.labels_)
            stat=(silh_.mean()/silh_.std(),silh.mean()/silh.std())
            if np.isnan(stat[1]) or stat[0]>stat[1]:
                silh,kmeans=silh_,kmeans_
    newIdx=np.argsort(kmeans.labels_)
    corr1=corr0.iloc[newIdx] # reorder rows
    corr1=corr1.iloc[:,newIdx] # reorder columns
    clstrs={i:corr0.columns[np.where(kmeans.labels_==i)[0]].tolist() \
        for i in np.unique(kmeans.labels_) } # cluster members
    silh=pd.Series(silh,index=x.index)
    return corr1,clstrs,silh

def optPort(cov, mu = None):
    inv = np.linalg.inv(cov) #The precision matrix: contains information about the partial correlation between variables,
    #  the covariance between pairs i and j, conditioned on all other variables 
    ones = np.ones(shape = (inv.shape[0], 1)) # column vector 1's
    if mu is None: 
        mu = ones
    w = np.dot(inv, mu)
    w /= np.dot(ones.T, w) # def: w = w / sum(w) ~ w is column vector
    
    return w

def calculate_portfolio_var(w,sigma):
    return multi_dot([w.T,sigma,w])

def calculate_risk_contribution(w,sigma):
    vols = sqrt(calculate_portfolio_var(w,sigma))
    MRC = np.dot(sigma,w)/vols
    RC = np.multiply(MRC,w)
    return RC

def risk_budget_objective(x,pars):
    sigma = pars[0]
    x_t = pars[1]
    sig_p = sqrt(calculate_portfolio_var(x,sigma))
    risk_target = np.multiply(sig_p,x_t)
    asset_RC = calculate_risk_contribution(x,sigma)
    error = sum((asset_RC-risk_target)**2)
    return error

def total_weight_constraint(x):
    return np.sum(x)-1.0
def long_only_constraint(x):
    return x

def portfolio_stats(weights,mu,cov):
    
    weights = array(weights)[:,newaxis]
    port_rets =  weights.T @ mu    
    port_vols = sqrt(multi_dot([weights.T, cov, weights])) 
    
    return np.array([port_rets, port_vols, port_rets/port_vols]).flatten()

def cov2corr(cov):
    std = np.sqrt(np.diag(cov)) 
    corr = cov/np.outer(std,std) 
    corr[corr<-1] = -1
    corr[corr>1] = 1
    return corr

def nco_weights(cov,cor,annual_rtns):
    corr1, clstrs, silh = clusterKMeansBase1(cor)
    wIntra = pd.DataFrame(0, index=cov.index, columns=clstrs.keys())
    for i in clstrs:
        initial_wts = len(clstrs[i])*[1./len(clstrs[i])]
        cov_sp = cov.loc[clstrs[i], clstrs[i]]
        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    #bnds = tuple((0.05, 1/cov_sp.shape[0]) for x in range(cov_sp.shape[0]))
        bnds = tuple((0.05, 1) for x in range(cov_sp.shape[0]))
        mu = annual_rtns.loc[clstrs[i]].values
        def min_sharpe_ratio(weights):
            return -portfolio_stats(weights,mu=mu,cov=cov_sp)[2]
        opt_sharpe_denoise = sco.minimize(min_sharpe_ratio, initial_wts, method='SLSQP',tol=1e-10, bounds=bnds,constraints=cons)
        wIntra.loc[clstrs[i], i] =  (opt_sharpe_denoise['x']).flatten()
    #annual_rtn = pd.DataFrame(annual_rtns, index=cov.index)
    #r = wIntra.T @ annual_rtn
    cov2 = wIntra.T.dot(np.dot(cov, wIntra))
    x_t =  (cov2.shape[0])*[1./(cov2.shape[0])]
    sigma = cov2
    w0 = (cov2.shape[0])*[1./(cov2.shape[0])]
    bnds1 = tuple((0, 1) for x in range(sigma.shape[0]))
#bnds1 = tuple((0.,1) for x in range(sigma.shape[0]))
    
    cons = ({'type': 'eq', 'fun': total_weight_constraint},{'type': 'ineq', 'fun': long_only_constraint})
    res= minimize(risk_budget_objective, w0, args=[sigma,x_t], method='SLSQP',constraints=cons,bounds=bnds1,tol=1e-10 ,options={'disp': True})
    weight_final= res['x']
    wInter = pd.Series(weight_final.flatten(), index=cov2.index)
    w_nco = wIntra.mul(wInter, axis=1).sum(axis=1).sort_index()
    w_nco =pd.DataFrame(w_nco,index=w_nco.index)
    w_nco = w_nco.rename(index= str,columns={0:'NCO'})
    w_nco = w_nco.sort_index()
    return w_nco,wIntra,wInter