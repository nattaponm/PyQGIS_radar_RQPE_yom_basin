'''
20200611 ฝนสะสมรายชั่วโมงแบบราสเตอร์ ปรับปรุงจากไฟล์ "096" แก้ค่าลบด้วยการ mask จุดที่เป็น flare 
สามารถนำไฟล์นี้ไปทำฝนสะสมราย3ชั่วโมงได้

ผลลัพธ์ที่ได้คือฝนสะสมรายชั่วโมงที่มีเวลาเป็น local time นำไปเทียบกับฝนสถานีได้เลย

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
print('เริ่มการประมวลผลทำฝนสะสมรายชั่วโมงจากการโมเสคราย 15 นาที(local time จากไฟล์"095")...................')

path_hr='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_mosaic_temp/mosaic_1h/' #ที่เก็บไฟล์ราสเตอร์ฝนโมเสครายชั่วโมง
path_r15m='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_mosaic_temp/' #ที่เก็บไฟล์ราสเตอร์ฝนโมเสคราย15นาที

fn = []
fn += [f for f in os.listdir(path_r15m) if f.endswith('.tif')] #ลิสชื่อไฟล์เต็ม15นาที
hr=[]
hr+=[f[0:10]for f in fn ] #ลิสชื่อไฟล์รายชั่วโมง

fh=list(set(hr)) #ลิสของฝนรายชั่วโมง
fh.sort()
################################################################################
#คำนวนฝนสะสมรายชั่วโมง
for f in fh: #ลูปลิสชื่อชั่วโมง
    print('ทำการสะสมฝนรายชั่วโมง....'+f)
    pat = '*'+f+'*.tif' #
    files = fnmatch.filter(fn, pat) #ลิสชื่อไฟล์ราสเตอร์ที่โมเสคราย15นาทีในชั่วโมงนั้นๆ    
    xsize,ysize,geotransform,geoproj,data=readTif(path_r15m+files[0]) #get พารามิเตอร์ของไฟล์ต้นแบบ    
    out_arr=np.zeros(data.shape,dtype=float) #ผลลัพธ์ที่จะเอาเก็บฝนสะสมรายชั่วโมง
    out_cnt=np.zeros(data.shape,dtype=float) #ผลลัพธ์ที่จะเอาเก็บตัวนับว่ามีฝนหรือไม่หรือมี flare จะกำหนดให้เป็น0
    filename=path_hr+f #ที่เก็บผลลัพธ์ฝนสะสมรายชั่วโมง    
    
    #อ่าน รวม และบันทึกผลลัพธ์ของฝนสะสม
    num_file=len(files)
    for n in range(num_file):
        count_data=np.zeros(data.shape,dtype=float) #อาเรย์ชั่วคราวเอาไว้นับว่ามีฝนหรือมี flare
        file=path_r15m+files[n]
        xsize,ysize,geotransform,geoproj,data=readTif(path_r15m+files[n])                  
        count_data[data >= 0.0] = 1.0 #กริดนั้นๆเป็นฝน
        count_data[data == -999] = 0.0 #กริดนั้นๆเป็นflare (no data)
        
        data[data == -999] = 0.0 #กริดใดๆที่พบว่าเป็น flare ให้กริดนั้นๆเป็น 0.0        
        
        out_arr = out_arr+data #ทำฝนสะสมในชั่วโมงนั้นๆ
        out_cnt = out_cnt+count_data #สะสมตัวหาร
        
#        out_arr=out_arr+(data/num_file) #data/num_file คำนวนฝนสะสมรายชั่วโมง
    
    out_arr=out_arr/out_cnt
        
    #ถ้าครบจำนวนไฟล์ที่ต้องการสะสมแล้วให้ write 
    writeFile(filename,geotransform,geoproj,out_arr)
    print('เสร็จสิ้นการสะสมฝนรายชั่วโมง....'+f)
    print('#'*50)


    
    
    
    