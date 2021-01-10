'''
20200611 ทำฝนสะสมราย6ชั่วโมง เวลาท้องถิ่น ใช้ผลการโมเสคจาก15นาที แบบราสเตอร์จากไฟล์ "095"
ปรับปรุงโค้ดจากไฟล์ "098,099" คำนึงค่า radar flare แล้วในการทำฝนสะสม

00:00+01+02+03+04+05 (มี24ไฟล์ ถ้า1ชั่วโมงมีการสแกน4ครั้ง) หมายความว่า ฝนสะสมย้อนหลัง6ชั่วโมงจาก 05:45
.
.
.

ต่อไปจะทำแบบ 12,24 ชั่วโมง

'''

import os
import fnmatch
import gdal
import numpy as np

def readTif(file):
    #อ่านฝนราสเตอร์ราย15นาที
    ds = gdal.Open(file)
    geotransform = ds.GetGeoTransform()
    geoproj = ds.GetProjection()
    band1 = ds.GetRasterBand(1).ReadAsArray()
    xsize = ds.RasterXSize
    ysize = ds.RasterYSize        
    return xsize,ysize,geotransform,geoproj,band1

def writeFile(filename,geotransform,geoprojection,data):
    #บันทึกฝนสะสมฟอร์แมท Geotif
    (x,y) = data.shape
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    dst_datatype = gdal.GDT_Float32 #ชนิดข้อมูลเป็นแบบ float
    dst_ds = driver.Create(filename,y,x,1,dst_datatype)
    dst_ds.GetRasterBand(1).WriteArray(data)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(geoprojection)
    return 1

################################################################################
#โค้ดหลัก
print('#'*50)
print('เริ่มทำฝนสะสมราย6ชั่วโมงจากผลโมเสคราย 15 นาที(local time จากไฟล์"098"+"099")...................')

path_r15m='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_mosaic_temp/' #ที่เก็บไฟล์ราสเตอร์ฝนโมเสคราย15นาที
path_outp6hr='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_mosaic_temp/mosaic_6h/' #เก็บผลลัพธ์ฝนสะสม6ชม.

fn = []
fn += [f for f in os.listdir(path_r15m) if f.endswith('.tif')] #ลิสชื่อไฟล์เต็ม15นาที

ymdn = []
ymdn += [f[0:8] for f in os.listdir(path_r15m) if f.endswith('.tif')] #ลิสชื่อไฟล์เต็ม15นาที yyyymmdd
fymd=list(set(ymdn)) #ลิสของฝนรายชั่วโมง
fymd.sort()


#ลูปลิสชื่อปีเดือนวัน yyyymmdd
for ymd in fymd:

    #ลูป 8 รอบใน 1 วัน
    for n in range(4): #4 คือ 24/6 สะสมฝนทุกๆ6ชม.
        print('ทำการสะสมฝนราย6ชั่วโมง...'+ymd)
        start=n*6
        stop=start+6
        
        files=[] #ลิสเก็บชื่อไฟล์ที่หาได้ในแต่ละชั่วโมงที่ต้องการ ในที่นี้ทีละ6ชั่วโมง
        for h in range(start,stop): #ลูป6ชั่วโมงที่ต้องการ
            f="{:02d}".format(h) #กำหนดให้เลขทุกตัวเป็นสองตำแหน่ง ถ้าเลขตัวเดียวให้เพิ่ม0นำหน้า
            print('>>>เวลาชั่วโมงที่',ymd+f)
            
            pat = ymd+f+'??.tif' #ตั้งรูปแบบให้หาเฉพาะตำแหน่งที่เป็นชั่วโมง
            files += fnmatch.filter(fn, pat) #ลิสชื่อไฟล์ราสเตอร์ที่โมเสคราย15นาทีในชั่วโมงนั้นๆ 
#        break    
        #สะสมฝนในรอบ 6 ชั่วโมงที่ต้องการ
        num_file=len(files)
        fileName=files[0][0:10]+'.tif' #ชื่อไฟล์ที่ต้องการเก็บผลลัพธ์ yyyymmddhh เป็นชื่อไฟล์ชั่วโมงต้นทาง        
        
        xsize,ysize,geotransform,geoproj,data=readTif(path_r15m+files[0]) #get พารามิเตอร์ของไฟล์ต้นแบบ    
        out_arr=np.zeros(data.shape,dtype=float) #ผลลัพธ์ที่จะเอาเก็บฝนสะสมราย6ชั่วโมง
        out_cnt=np.zeros(data.shape,dtype=float) #ผลลัพธ์ที่จะเอาเก็บตัวนับว่ามีฝนหรือไม่หรือมี flare จะกำหนดให้เป็น0
        
        filename=path_outp6hr+fileName #ไฟล์ที่เก็บผลลัพธ์ฝนสะสมราย3ชั่วโมง    
        
        for rr in range(num_file):
            count_data=np.zeros(data.shape,dtype=float) #อาเรย์ชั่วคราวเอาไว้นับว่ามีฝนหรือมี flare
            file=path_r15m+files[rr]
            xsize,ysize,geotransform,geoproj,data=readTif(path_r15m+files[rr])
            count_data[data >= 0.0] = 1.0 #กริดนั้นๆเป็นฝน
            count_data[data == -999] = 0.0 #กริดนั้นๆเป็นflare (no data)
            
            data[data == -999] = 0.0 #กริดใดๆที่พบว่าเป็น flare ให้กริดนั้นๆเป็น 0.0        
            
            out_arr = out_arr+data #ทำฝนสะสมในชั่วโมงนั้นๆ
            out_cnt = out_cnt+(count_data/6) #สะสมตัวหาร    
            #count_data/6> หาร6หมายถึง มี6ชั่วโมงที่นำมาสะสม เมื่อนำมาหาร6จะทำให้กลายเป็นฝนสะสมราย6ชั่วโมง
            #ถ้าต้องการฝนราย 6,12,24 ชม. ก็เอาตัวเลขไปหาร 6,12,24 ไปหาร
        
        out_arr=out_arr/out_cnt
        #ถ้าครบจำนวนไฟล์ที่ต้องการสะสมแล้วให้ write 
        writeFile(filename,geotransform,geoproj,out_arr)
        print('เสร็จสิ้นการสะสมฝนราย6ชั่วโมง...'+fileName)

        print('.'*30)
print('เสร็จสิ้นการสะสมฝนราย6ชั่วโมง.....')

    