'''
20200613 หาค่าสถิติ validation รายสถานี ราย15นาที ปรับปรุงโค้ดจาก 117 โดยข้อมูลจากไฟล์113
เพื่อนำไปวิเคราะห์และแสดงผลในรูปแผนที่

อ่านสถิติที่ใช้ในการหาbias http://scienceasia.org/2012.38.n4/scias38_373.pdf
Bias correction of radar rainfall estimates based on ageostatistical technique
'''

import csv
import numpy as np
from scipy import stats

gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด

#โฟลเดอร์เก็บค่าการสกัด rr+rg และเก็บผลลัพธ์การคำนวนค่าสถิติ validataion
path_val='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_validation/1validate15min/' 

#อ่านสถานีวัดฝนทั้งหมดในลุ่มยม
with open(gaugeName+'1สถานีวัดฝนกรมอุตุลุ่มน้ำยม2018.csv', 'r') as f:
    st_all = list(csv.reader(f, delimiter=','))

#อ่านผลลัพธ์สกัดข้อมูลrr+rg
with open(path_val+'validate_rr_rg_15min.csv', 'r') as f:
     val= list(csv.reader(f, delimiter=','))

#แปลงลิสเป็นอาเรย์
r=np.asarray(val)
r = r.astype(np.float) #แปลงstring เป็น float เพื่อการคำนวน

#กรองเอาrg>0.5 & rr>0.5
rr=r[r[:,1]>0.5 ]
r=rr[rr[:,2]>0.5]

def transformGeo2UTM(lon,lat):
    #แปลงพิกัด geo เป็น utm47N
    geom = QgsGeometry(QgsPoint(float(lon),float(lat))) # นำพิกัดสถานีฝนมาสร้างเป็น geometry
    sourceCrs = QgsCoordinateReferenceSystem(4326)
    destCrs = QgsCoordinateReferenceSystem(32647)
    tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
    geom.transform(tr) #แปลง geo เป็น utm
    x_utm,y_utm=(geom.asPoint()[0],geom.asPoint()[1]) #get ค่า utm   
    return x_utm,y_utm   

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
       w.writerows(res)

#หารายชื่อสถานีฝนภาคพื้นดิน
st_all=np.asarray(st_all)
st=set(r[:,0]) #หารายชื่อสถานีแบบ unique
res=[]
res.append(("code_st","x_utm","y_utm","sse","var","bias","r_value","r_square","mfb","mae","nse","rmse"))
for s in st:
    print('*'*50)
    print('+++สถานี',s)
    ids=np.where(st_all==str(int(s)))[0][0] #หาอินเด็กซ์แถวที่มีรหัสสถานีตรงกับ s
    lon,lat=(st_all[ids][1],st_all[ids][2]) #get ค่าพิกัดสถานีของ s จากไฟล์สถานีหลัก
    x_utm,y_utm=transformGeo2UTM(lon,lat)
    
#    break
    
    id=np.where(r[:,0]==s) #หาว่าสถานี s มีข้อมูลอยู่แถวไหนบ้าง
    re=r[id[0]] #ดึงข้อมูลแถวของสถานี s
    
    #คำนวนค่า validation statistics
    sse,var,bias,r_value,r_square,mfb,mae,nse,rmse=statistics(re)
    res.append((int(s),x_utm,y_utm,sse,var,bias,r_value,r_square,mfb,mae,nse,rmse))

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
    print('*'*50)
    
#    break

#เซฟไฟล์ผลลัพธ์การ validate ออกไปเป็น csv เพื่อใช้ pyqgis พล๊อตแผนที่
fileOutput='validate_rr_rg_15min_each_stations.csv'
saveValidate(res,path_val,fileOutput)
    
    
    
    






