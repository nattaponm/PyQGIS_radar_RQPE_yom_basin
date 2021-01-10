'''
20200613 เปรียบเทียบฝนสถานีกับฝนจากเรดาร์ราย15นาที
ต่อไปจะลูปเพื่อสกัดค่าฝนสถานีกับฝนเรดาร์หลายไฟล์

'''

import csv
import numpy as np

gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด
path_rg='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_gauge_temp/1gauge15min/201807171800.csv'
path_rr='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_mosaic_temp/201807171800.tif'
path_val='D:/tmp/PyQGIS/Plugin_practice/z_temp/' #โฟลเดอร์เก็บผลลัพธ์การ validate

#อ่านสถานีวัดฝนทั้งหมดในลุ่มยม
with open(gaugeName+'1สถานีวัดฝนกรมอุตุลุ่มน้ำยม2018.csv', 'r') as f:
    st_all = list(csv.reader(f, delimiter=','))

#อ่านสถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
with open(gaugeName+'list_passedQG_gauges.csv', 'r') as f:
    st = list(csv.reader(f, delimiter=','))[0]

#อ่านฝนเรดาร์
rr_name='rr_201807171800'
rlayer = QgsRasterLayer(path_rr, rr_name)
#QgsProject.instance().addMapLayer(rlayer)

#อ่านฝนสถานีราย15แบบ csv
with open(path_rg, 'r') as f:
    rg = list(csv.reader(f, delimiter=','))
#print('len(rg):',len(rg))

def transformGeo2UTM(lon,lat):
    #แปลงพิกัด geo เป็น utm47N
    geom = QgsGeometry(QgsPoint(float(lon),float(lat))) # นำพิกัดสถานีฝนมาสร้างเป็น geometry
    sourceCrs = QgsCoordinateReferenceSystem(4326)
    destCrs = QgsCoordinateReferenceSystem(32647)
    tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
    geom.transform(tr) #แปลง geo เป็น utm
    x_utm,y_utm=(geom.asPoint()[0],geom.asPoint()[1]) #get ค่า utm   
    return x_utm,y_utm    

def saveValidate(res,path_val,fileOutput):
    #เซฟผลลัพธ์การ validate เป็น csv
    val_res = open(path_val+fileOutput, 'w',newline='') #newline='' เพื่อป้องกันการเพิ่มบรรทัดตอนเซฟ csv
    with val_res:
       w = csv.writer(val_res)
       w.writerows(res)

#เปรียบเทียบฝนสถานีกับฝนจากเรดาร์
rg=np.asarray(rg)
st_all=np.asarray(st_all)
res=[]
for s in st:
    #get ฝนสถานีที่ตรงกับ s
    idg=np.where(rg==s)[0][0] #หาอินเด็กซ์แถวของฝนสถานีที่สมบูรณ์ที่มีรหัสสถานีตรงกับ s 
    gauge=rg[idg][2]
    
    #หาพิกัด geo(lon,lat) ในลิสสถานีทั้งหมด
    id=np.where(st_all==s)[0][0] #หาอินเด็กซ์แถวที่มีรหัสสถานีตรงกับ s
    lon,lat=(st_all[id][1],st_all[id][2]) #get ค่าพิกัดสถานีของ s จากไฟล์สถานีหลัก
    
    #แปลงพิกัด geo เป็น utm47N
    x_utm,y_utm=transformGeo2UTM(lon,lat)   
#    print('...',s,lon,lat,x_utm,y_utm)

    #สกัดค่าฝนเรดาร์ด้วยการ query โดยใช้ค่าพิกัด UTM ของสถานีฝน    
    radar, result = rlayer.dataProvider().sample(QgsPointXY(x_utm,y_utm), 1) #radar คือค่าฝนเรดาร์ที่รีเทิร์นกลับมาจากการสกัดด้วยจุด
    
    #เซฟไฟล์ผลลัพธ์การ validate ออกไปเป็น csv เพื่อคำนวนค่าสถิติ
    res.append((s,"{:.2f}".format(float(gauge)), "{:.2f}".format(float(radar))))
    fileOutput='temp_val15min.csv'
    saveValidate(res,path_val,fileOutput)
        
    print(s,"{:.2f} , {:.2f}".format(float(gauge),float(radar)))
