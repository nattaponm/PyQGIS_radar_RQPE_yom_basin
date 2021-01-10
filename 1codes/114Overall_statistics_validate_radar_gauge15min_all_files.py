'''
20200613 คำนวนค่าสถิติ validation ระหว่างฝนสถานีกับฝนเรดาร์
เพื่อให้ได้ค่าสถิติรวม

ต่อไปจะคำนวนค่าสถิติแต่ละสถานี เพื่อนำไปแสดง spatial bias
'''

import csv
import numpy as np
from scipy import stats
#โฟลเดอร์เก็บค่าการสกัด rr+rg และเก็บผลลัพธ์การคำนวนค่าสถิติ validataion
path_val='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_validation/1validate15min/' 

#อ่านผลลัพธ์สกัดข้อมูลrr+rg
with open(path_val+'validate_rr_rg_15min.csv', 'r') as f:
     val= list(csv.reader(f, delimiter=','))

#แปลงลิสเป็นอาเรย์
r=np.asarray(val)
r = r.astype(np.float) #แปลงstring เป็น float เพื่อการคำนวน

#กรองเอาrg>0.5 & rr>0.5
rr=r[r[:,1]>0.5 ]
r=rr[rr[:,2]>0.5]

def statistics(r):
    '''
    สถิติ validation เปรียบเทียบระหว่าง gauge และ การประมาณค่าฝนด้วย radar
    '''
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

    #MAE
    mae=np.sum(yhat-Y)/len(yhat)

    #NSE The Nash-Sutcliffe-Efficiency (NSE, Nash and Sutcliffe, 1970)
    nse= 1-(np.sum((yhat-Y)**2)/np.sum((Y-np.mean(Y))**2))

    #RMSE
    rmse=np.sqrt((np.sum((yhat-Y)**2))/len(yhat))

    return sse,var,bias,r_value,r_value**2,mfb,mae,nse,rmse

def saveValidate(res,path_val,fileOutput):
    #เซฟผลลัพธ์การ validate เป็น csv
    val_res = open(path_val+fileOutput, 'w',newline='') #newline='' เพื่อป้องกันการเพิ่มบรรทัดตอนเซฟ csv
    with val_res:
       w = csv.writer(val_res)
       w.writerow(res)

#-------------------------------------------------------------------------------
#คำนวนค่า validation statistics
sse,var,bias,r_value,r_square,mfb,mae,nse,rmse=statistics(re)
res=np.asarray([sse,var,bias,r_value,r_square,mfb,mae,nse,rmse])

#ค่าสถิติการตรวจสอบรวม
print('#'*50)
print('+++ค่าสถิติตรวจสอบความถูกต้องของการโมเสค+++')
print("Residual sum of squares: %.2f" % sse)
print("Variance: {var}".format(var=var))
print("Bias: {bias}".format(bias=bias))
print("correlation coefficient: {:.2f}".format(r_value))
print("coefficient of determination (r_squared): {:.2f}".format(r_value**2))
print("Mean Field Bias: {:.2f}".format(mfb))
print("Mean Absolute Error:{:.2f}".format(mae))
print("NSE:{:.2f}".format(nse))
print("RMSE: {:.2f}".format(rmse))
print('#'*50)

#เซฟไฟล์ผลลัพธ์การ validate ออกไปเป็น csv เพื่อใช้ pyqgis พล๊อตแผนที่
fileOutput='validate_rr_rg_15min_all_stations.csv'
saveValidate(res,path_val,fileOutput)




