import pandas as pd
#for entering and working with data

import numpy as np


import sys
from numpy import linalg as la
import gurobipy as gp

from gurobipy import*


data = pd.read_csv(r"sample.csv", encoding="latin1")
tmpl = pd.read_csv(r"template.csv", encoding="latin1")

data = data.fillna(0)
tmpl = tmpl.fillna(0)

data = data.values
tmpl = tmpl.values  

final=[]

T = list(range(1,45))
    #I = { 30, 60, 120, 180, 240, 300, 360 }
    
I = { 30, 60, 120, 180, 240, 300, 360 }
    
x = {
     (i, t) : 0
     for i in I for t in T
    }
    
for i in I:
    for t in T: 
        if t < np.size(tmpl,0):
            if i == 30:
                x[i,t] = int(tmpl[t-1,0])
            else:
                x[i,t] = int(tmpl[t-1,int(i/60)])


#L1 = 50
#L2 = 4
#L3 = 3
#L4 = 2
#L5 = 1

slot = 15
                
for count in range(np.size(data,0)):
#for count in range(12,13):
    count_y=0
    count_z=0
    count_w=0
    count_beta=0
    count_asg=0
    
    P = {i : 0
         for i in I
         }

    for i in I:
        if i == 30:
            P[i] = data[count,0]
        else:
            P[i] = data[count, int(i/60)]
    #print(P)

    # parameters
    #L1 = 200
    #LL = 100
    #L2 = 2
    #L3 = 4


    # Start building chemo model 
    Chemo = gp.Model("Chemo Scheduling")

    aux_idx_y = {
           (i,ii,t,j) for i in I for ii in I for t in T for j in range(int(x[ii,t])) if i <= ii
        }

    y = Chemo.addVars(aux_idx_y, vtype=GRB.BINARY, name='y')

    aux_idx_z = {
        (i,ii,t,j) for i in I for ii in I for t in T for j in range(int(x[ii,t])) if i > ii
        }

    aux_idx_w = {
        (i,iii,t,j) for i in I for iii in I for t in T for j in range(int(x[iii,t])) if i > iii
        }
   
    aux_idx_v = {
            (i,ii,iii,t,j1,j2) for i in I for ii in I for iii in I for t in T
            for j1 in range(int(x[ii,t])) for j2 in range(int(x[iii,t+ii/slot]))
            if ii < i and iii < i and ii + iii >= i and t + ((ii+iii)/slot) in T
        }
   
    
    aux_idx_b = {
            (i,iii,ii,t,j) for i in I for iii in I for ii in I for t in T for j in range(int(x[ii,t]))
            if i < ii and iii < ii and ii >= i + iii
        }
    b = Chemo.addVars(aux_idx_b, vtype=GRB.BINARY, name='beta')

    z = Chemo.addVars(aux_idx_z, vtype=GRB.BINARY, name='z')

    w = Chemo.addVars(aux_idx_w, vtype=GRB.BINARY, name='w')

    v = Chemo.addVars(aux_idx_v, vtype=GRB.INTEGER, lb = 0, name='v')

    u = Chemo.addVars(I, T, vtype=GRB.INTEGER, lb = 0, name='u')

    q = Chemo.addVars(I, vtype=GRB.INTEGER, lb = 0, name='q')

    a = Chemo.addVars(I, vtype=GRB.INTEGER, lb = 0, name='a')

    cons1 = Chemo.addConstrs(
        v[i,ii,iii,t,j1,j2] <= z[i,ii,t,j1] for (i,ii,iii,t,j1,j2) in aux_idx_v
        )

    cons2 = Chemo.addConstrs(
        v[i,ii,iii,t,j1,j2] <= w[i,iii,t + int(ii/slot),j2] for (i,ii,iii,t,j1,j2) in aux_idx_v
        )

    cons3 = Chemo.addConstrs(
        v[i,ii,iii,t,j1,j2] >= z[i,ii,t,j1] + w[i,iii,t + int(ii/slot),j2] - 1 for (i,ii,iii,t,j1,j2) in aux_idx_v
        )

    cons4 = Chemo.addConstrs(
        v.sum(i,ii,'*',t,j1,'*') <= 1 for (i,ii,t,j1) in aux_idx_z
        )
   
    for ii in I:
        for t in T:
            for j in range(int(x[ii,t])):
                expr = LinExpr(0.0)
                for i in I:
                    for iii in I:
                        if (i,iii,ii,t,j) in aux_idx_b:
                            expr = expr + b[i,iii,ii,t,j]
                Chemo.addConstr(expr <= 1)
            
    for i in I:
        for iii in I:
            for t in T:
                if (iii,t) in x:
                    for j2 in range(x[iii,t]):
                        if (i,iii,t,j2) in aux_idx_w:
                            print(i,iii,t,j2)
                            expr = LinExpr(0.0)
                            for ii in I:
                                if (ii,t-int(ii/slot)) in x:
                                    for j1 in range(x[ii,t-int(ii/slot)]):
                                        if (i,ii,iii,t-int(ii/slot),j1,j2) in aux_idx_v:
                                            expr = expr + v[i,ii,iii,t-int(ii/slot),j1,j2]
                            Chemo.addConstr(expr <= 1)

    cons6 = Chemo.addConstrs(
        y.sum('*',ii,t,j) + z.sum('*',ii,t,j) + w.sum('*',ii,t,j) + 0.5*b.sum('*','*',ii,t,j) <= 1
                   for ii in I for t in T for j in range(x[ii,t])
        )

    cons7 = Chemo.addConstrs(
        u[i,t] == y.sum(i,'*',t,'*') + v.sum(i,'*','*',t,'*','*') + b.sum(i,'*','*',t,'*') + b.sum('*',i,'*',t,'*')
        for i in I for t in T
        )

    cons8 = Chemo.addConstrs(
        q[i] >= P[i] - u.sum(i,'*') for i in I
        )

    cons9 = Chemo.addConstrs(
        a[i] == u.sum(i,'*') for i in I
        )

    L1 = 50
    L2 = 4
    L3 = 1
    L4 = 2
    L5 = 3

    objective = L1*q.sum('*') + L2*u.sum('*','*')
    for t in T:
        for ii in I:
            for i in I:
                if i < ii:
                    for j in range(x[ii,t]):
                        objective += L3*y[i,ii,t,j]
                        
    objective += L4*v.sum('*','*','*','*','*','*')
    objective += L4*(z.sum('*','*','*','*') + w.sum('*','*','*','*')) 
    objective += L5*b.sum('*','*','*','*','*')

    Chemo.setObjective(objective, GRB.MINIMIZE)
    Chemo.optimize()


    
    if Chemo.status == GRB.OPTIMAL:
        
        build_in_val=[]
    
        print('\nCost: %g' % Chemo.objVal)
        print('\nStart:')
        build_in_val.append('\nCost: %g' % Chemo.objVal)
        build_in_val.append('\nStart:')
        
        xu = Chemo.getAttr('x', u)
        qu = Chemo.getAttr('x', q)
        yu = Chemo.getAttr('x', y)
        zu = Chemo.getAttr('x', z)
        wu = Chemo.getAttr('x', w)
        bu = Chemo.getAttr('x', b)
        vu = Chemo.getAttr('x', v)
        au = Chemo.getAttr('x', a)

        txt_out=[]
        
       
        print('print u it')
        txt_out.append('print u it')
        for i in I:
            for t in T:
                if u[i,t].x > 0.0001:
                    print('%s %s %g' % (i, t, xu[i,t]))
                    txt_out.append('%d %d %d' % (i, t, round(xu[i,t])))
                    count_asg+=round(xu[i,t])
                    
                    #this means count_asg = count_asg + xu[i,t]
                    
        print('print q i')
        txt_out.append('print q i')
        for i in I:                
            if q[i].x > 0.0001:
                print('%s %g' % (i, round(qu[i])))
                txt_out.append('%s %g' %(i, round(qu[i])))
                    
        print('print a i')
        txt_out.append('print a i')
        for i in I:
            if a[i].x > 0.0001:
                    print('%s, %g' % (i, round(au[i])))
                    txt_out.append('%s, %g' %(i, round(au[i])))
                    
                    
        print('print y iitj')
        txt_out.append('print y iitj')
        for i in I:
            for ii in I:
                for t in T:
                    for j in range(x[ii,t]):
                        if ((i,ii,t,j) in aux_idx_y) and (y[i,ii,t,j].x > 0.01):
                            print('%s %s %s %s, %g' % (i, ii, t, j, yu[i,ii,t,j]))
                            txt_out.append('%s %s %s %s, %g' % (i, ii, t, j, round(yu[i,ii,t,j])))
                            
                            if i<ii:
                                count_y+=1
                                #this means count_y = count_y + 1
                            
        print('print z iitj')
        txt_out.append('print z iitj')
        for i in I:
            for ii in I:
                for t in T:
                    for j in range(x[ii,t]):
                        if ((i,ii,t,j) in aux_idx_z) and (z[i,ii,t,j].x > 0.01):
                            print('%s %s %s %s, %g' % (i, ii, t, j, zu[i,ii,t,j]))
                            txt_out.append('%s %s %s %s, %g' % (i, ii, t, j, round(zu[i,ii,t,j])))
                            count_z+=1

        print('print w iitj')
        txt_out.append('print w iitj')
        for i in I:
            for ii in I:
                for t in T:
                    for j in range(x[ii,t]):
                        if ((i,ii,t,j) in aux_idx_w) and (w[i,ii,t,j].x > 0.01):
                            print('%s %s %s %s, %g' % (i, ii, t, j, wu[i,ii,t,j]))
                            txt_out.append('%s %s %s %s, %g' % (i, ii, t, j, round(wu[i,ii,t,j])))
                            count_w+=1
       
        count_result=min(count_w,count_z)

        print('print v iiit')
        txt_out.append('print v iiit')
        for i in I:
            for ii in I:
                for iii in I:
                    for t in T:
                        for j1 in range(x[ii,t]):
                            for j2 in range(x[iii,t+ii//slot]):
                                if (i,ii,iii,t,j1,j2) in aux_idx_v and (v[i,ii,iii,t,j1,j2].x > 0.01):
                                    print('%s %s %s %s %s, %s, %g' % (i, ii, iii, t, j1, j2, vu[i,ii,iii,t,j1,j2]))
                                    txt_out.append('%s %s %s %s %s, %s, %g' % (i, ii, iii, t, j1, j2, round(vu[i,ii,iii,t,j1,j2])))

        print('print beta iiitj')
        txt_out.append('print beta iiitj')
        
        #print(b)
        for i in I:
            for ii in I:
                for iii in I:
                    for t in T:
                        for j in range(x[iii,t]):
                            if ((i,ii,iii,t,j) in aux_idx_b) and (b[i,ii,iii,t,j].x > 0.01):
                                print('%s %s %s %s %s, %g' % (i, ii, iii, t, j, bu[i,ii,iii,t,j]))
                                txt_out.append('%s %s %s %s %s, %g' % (i, ii, iii, t, j, round(bu[i,ii,iii,t,j])))
                                count_beta+=1
    else:
        txt_out.append('No solution')
        print('No solution')
    counters_=[]
    counters_.append('No. of times a larger block was assigned to a patients requiring smaller time blocks %s'%count_y)
    counters_.append('No. of times two blocks were combined %s'%count_result)
    counters_.append('No. of times a larger block was broken %s'%count_beta)
    counters_.append('No. secondary assignments %d'%int(round((count_asg))))
    
    text_output=counters_+[' ']+build_in_val+txt_out
    
    out_to_excel=(txt_out[txt_out.index('print u it'):txt_out.index('print q i')][1:])
    
    print('text'+str(count+1))
    with open(str(count+1)+'.txt', 'w') as filehandle:
        for listitem in text_output:
            filehandle.write('%s\n' % listitem)
            
    values=[]
    for ele in out_to_excel:
        s=ele.split(' ')
        temporary=[]
        for k in s:
            temporary.append(int(k))
        values.append(temporary)
    #print (values)
    values=np.array(values)
    #print(values)
    q=values
   

    a_360=np.zeros((41,1))            #subject to change if we have more than 40 slots
    a_300=np.zeros((41,1))
    a_240=np.zeros((41,1))
    a_180=np.zeros((41,1))
    a_120=np.zeros((41,1))
    a_60=np.zeros((41,1))
    a_30=np.zeros((41,1))
    
    for j in range(q.shape[0]):
        if (q[j][0]==360):
            a_360[q[j][1]]=q[j][2]
        elif (q[j][0]==300):
            a_300[q[j][1]]=q[j][2]
        elif (q[j][0]==240):
            a_240[q[j][1]]=q[j][2]
        elif (q[j][0]==180):
            a_180[q[j][1]]=q[j][2]
        elif (q[j][0]==120):
            a_120[q[j][1]]=q[j][2]
        elif (q[j][0]==60):
            a_60[q[j][1]]=q[j][2]
        elif (q[j][0]==30):
            a_30[q[j][1]]=int(q[j][2])

    values_a_30=[]        
    for a_30_ in a_30:
        values_a_30.append(a_30_[0])
    #print(values_a_30)

    values_a_60=[]        
    for a_60_ in a_60:
        values_a_60.append(a_60_[0])
    #print(values_a_60)

    values_a_120=[]        
    for a_120_ in a_120:
        values_a_120.append(a_120_[0])
    #print(values_a_120)

    values_a_180=[]        
    for a_180_ in a_180:
        values_a_180.append(a_180_[0])
    #print(values_a_180)

    values_a_240=[]        
    for a_240_ in a_240:
        values_a_240.append(a_240_[0])
    #print(values_a_240)

    values_a_300=[]        
    for a_300_ in a_300:
        values_a_300.append(a_300_[0])
    #print(values_a_300)

    values_a_360=[]        
    for a_360_ in a_360:
        values_a_360.append(a_360_[0])
    #print(values_a_360)

    out_dict={30:values_a_30,60:values_a_60,120:values_a_120,180:values_a_180,240:values_a_240,300:values_a_300,360:values_a_360}
    
  
    
    final.append(out_dict)

#subject to change if we have timeslots after 4:45    
import datetime
order=pd.DataFrame([0,datetime.time(7, 0), datetime.time(7, 15), datetime.time(7, 30),
                   datetime.time(7, 45), datetime.time(8, 0), datetime.time(8, 15),
                   datetime.time(8, 30), datetime.time(8, 45), datetime.time(9, 0),
                   datetime.time(9, 15), datetime.time(9, 30), datetime.time(9, 45),
                   datetime.time(10, 0), datetime.time(10, 15), datetime.time(10, 30),
                   datetime.time(10, 45), datetime.time(11, 0), datetime.time(11, 15),
                   datetime.time(11, 30), datetime.time(11, 45), datetime.time(12, 0),
                   datetime.time(12, 15), datetime.time(12, 30),
                   datetime.time(12, 45), datetime.time(13, 0), datetime.time(13, 15),
                   datetime.time(13, 30), datetime.time(13, 45), datetime.time(14, 0),
                   datetime.time(14, 15), datetime.time(14, 30),
                   datetime.time(14, 45), datetime.time(15, 0), datetime.time(15, 15),
                   datetime.time(15, 30), datetime.time(15, 45), datetime.time(16, 0),
                   datetime.time(16, 15), datetime.time(16, 30),
                   datetime.time(16, 45)],columns=['time'])




writer = pd.ExcelWriter('output.xlsx')
for i in range(len(final)):
    df = pd.DataFrame(final[i]) 
    df=df.iloc[1:,:]
    df=pd.concat([order.iloc[1:,:],df],axis='columns')
    df.to_excel(writer, "Sheet{}".format(i + 1))
writer.save()
   
