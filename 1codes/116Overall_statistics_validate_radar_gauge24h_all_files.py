'''
20200613 คำนวนค่าสถิติ validation ระหว่างฝนสถานีกับฝนเรดาร์ราย24h จากไฟล์115
เพื่อให้ได้ค่าสถิติรวม

ต่อไปจะคำนวนค่าสถิติแต่ละสถานี เพื่อนำไปแสดง spatial bias

อ่าน http://scienceasia.org/2012.38.n4/scias38_373.pdf
Bias correction of radar rainfall estimates based on ageostatistical technique
'''

import csv
import numpy as np
from scipy import stats

path_val='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_validation/1validate24h/' #โฟลเดอร์เก็บผลลัพธ์สกัดข้อมูลrg+rr

#อ่านผลลัพธ์สกัดข้อมูลrr+rg
with open(path_val+'validate_rr_rg_24h.csv', 'r') as f:
     val= list(csv.reader(f, delimiter=','))

#แปลงลิสเป็นอาเรย์
r=np.asarray(val)
r = r.astype(np.float) #แปลงstring เป็น float เพื่อการคำนวน

#กรองเอาrg>0.5 & rr>0.5
rr=r[r[:,1]>0.5 ]
r=rr[rr[:,2]>0.5]

yhat=r[:,2] #estimator=rr
Y=r[:,1] #expected=rg

#SSE:sum of squared errors (or MSE:mean square error)
sse=np.mean((np.mean(yhat) - Y) ** 2)

#Variance
var = np.var(yhat)

#Bias of estimator
bias = sse - var

#ค่าสถิติ regression line
slope, intercept, r_value, p_value, std_err = stats.linregress(yhat,Y)

#MFB mean field bias
mfb=np.sum(Y)/np.sum(yhat)

#RMSE
rmse=np.sqrt((np.sum((yhat-Y)**2))/len(yhat))


#ค่าสถิติการตรวจสอบรวม
print('#'*50)
print('+++ค่าสถิติตรวจสอบความถูกต้องของการโมเสค+++')
print("Residual sum of squares: %.2f" % sse)
print("Variance: {var}".format(var=var))
print("Bias: {bias}".format(bias=bias))
print("correlation coefficient: {:.2f}".format(r_value))
print("coefficient of determination (r_squared): {:.2f}".format(r_value**2))
print("Mean Field Bias: {:.2f}".format(mfb))
print("RMSE: {:.2f}".format(rmse))
print('#'*50)


