'''
20200613 การสกัดค่าฝนเรดาร์และฝนสถานีในแต่ละเวลา ราย24ชม. ปรัับปรุงจากไฟล์113

ต่อไปจะใช้ผลลัพธ์จากไฟล์นี้ในการ validate ด้วยสถิติ bias,mse,rmse

'''

import csv
import numpy as np

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

#-------------------------------------------------------------------------------
gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด
path_rg='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_gauge_temp/1gauge24h/'#โฟลเดอร์เก็บฝนสถานี24ชม.
path_rr='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_mosaic_temp/mosaic_24h/' #โฟลเดอร์เก็บฝนเรดาร์24ชม.
path_val='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_validation/1validate24h/' #โฟลเดอร์เก็บผลลัพธ์สกัดข้อมูลrg+rr

#อ่านสถานีวัดฝนทั้งหมดในลุ่มยม
with open(gaugeName+'1สถานีวัดฝนกรมอุตุลุ่มน้ำยม2018.csv', 'r') as f:
    st_all = list(csv.reader(f, delimiter=','))

#อ่านสถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
with open(gaugeName+'list_passedQG_gauges.csv', 'r') as f:
    st = list(csv.reader(f, delimiter=','))[0]

#สร้างลิสฝนเรดาร์15นาที
fn_rr = []
fn_rr += [f for f in os.listdir(path_rr) if f.endswith('.tif')] 

#สร้างลิสฝนสถานี15นาที
fn_rg = []
fn_rg += [f for f in os.listdir(path_rg) if f.endswith('.csv')] 

#-------------------------------------------------------------------------------
#แปลงพิกัดสถานีฝนภาพพื้นดินจาก Geo เป็น UTM
st_all=np.asarray(st_all)
s_utm=[]
for s in st:    
    #หาพิกัด geo(lon,lat) ในลิสสถานีทั้งหมด
    id=np.where(st_all==s)[0][0] #หาอินเด็กซ์แถวที่มีรหัสสถานีตรงกับ s
    lon,lat=(st_all[id][1],st_all[id][2]) #get ค่าพิกัดสถานีของ s จากไฟล์สถานีหลัก
    
    #แปลงพิกัด geo เป็น utm47N
    x_utm,y_utm=transformGeo2UTM(lon,lat)
    s_utm.append((s,x_utm,y_utm))
          
print('เริ่มการ validate.....')        
res=[]
fn_rg=np.asarray(fn_rg)
for fr in fn_rr:
    rg_name=fr[0:10]+'.csv'
    rr_name=fr
    print('*'*50)
    print('+++',rg_name,rr_name)
    
    #ถ้าพบไฟล์เรดาร์ในฝนสถานี
    if len(np.where(rg_name==fn_rg)[0])>0:
        
        #เปิดฝนเรดาร์
        rlayer = QgsRasterLayer(path_rr+rr_name, rr_name)
        
        #เปิดฝนสถานีราย15นาทีแบบ csv
        with open(path_rg+rg_name, 'r') as f:
            rg = list(csv.reader(f, delimiter=','))
        
        #ลูปสถานีจากลิสไฟล์สถานีที่สมบูรณ์พร้อมพิกัดที่แปลงเป็น UTM แล้ว
        #เปรียบเทียบฝนสถานีกับฝนจากเรดาร์แต่ละช่วงเวลา
        rg=np.asarray(rg)
        for s in s_utm:
            st,x_utm,y_utm=s
            
            #สกัดค่าฝนสถานีจาก rg ในสถานีนั้นๆ
            idg=np.where(rg==st)[0][0] #หาอินเด็กซ์แถวของฝนสถานีที่สมบูรณ์ที่มีรหัสสถานีตรงกับ s 
            gauge=rg[idg][2]
            
            #สกัดค่าฝนเรดาร์จาก rlayer ในสถานีนั้นๆ            
            radar, result = rlayer.dataProvider().sample(QgsPointXY(x_utm,y_utm), 1) #radar คือค่าฝนเรดาร์ที่รีเทิร์นกลับมาจากการสกัดด้วยจุด
            print(st,"{:.2f} , {:.2f}".format(float(gauge),float(radar)))
                
            #เก็บผลลัพธ์การสกัด rr และ rg ของแต่ละสถานีไว้ในลิส res
            res.append((st,"{:.2f}".format(float(gauge)), "{:.2f}".format(float(radar))))
   
    print('*'*50)   
#    break

#เซฟไฟล์ผลลัพธ์การ validate ออกไปเป็น csv เพื่อคำนวนค่าสถิติ    
fileOutput='validate_rr_rg_24h.csv'
saveValidate(res,path_val,fileOutput)
                
        
print('สิ้นสุดการ validate.....')        
    
    
