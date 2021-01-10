'''
20200612 สร้างไฟล์ฝนราย15นาที จากลิสไฟล์สถานีที่ตรวจแล้วว่ามีข้อมูลสมบูรณ์จากไฟล์"105"

ต่อไปจะทำฝนสะสมราย 1ชั่วโมง (3,6,12,24)

'''

import csv
import numpy as np
import os
import fnmatch

gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด
pathGauge='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/1gauge_org/' #เป็นโฟลเดอร์เก็บข้อมูลดิบฝนแต่ละสถานี
outpRain15m='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_gauge_temp/1gauge15min/'#เป็นโฟลเดอร์เก็บข้อมูลผลลัพธ์ฝนราย15นาทีของสถานีที่สมบูรณ์ที่ได้จากไฟล์"105"

#สถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
with open(gaugeName+'list_passedQG_gauges.csv', 'r') as f:
    st = list(csv.reader(f, delimiter=','))[0]


print('เริ่มการดึงข้อมูลฝนราย15นาทีของแต่ละสถานีฝน..............')
#วันเวลาที่ต้องการรวมไฟล์ฝน15นาที
time=['20180717','20180718']     
#ลูปเวลาเพื่อดึงตามเวลา 15 นาทีในแต่ละไฟล์
for dd in time: #วัน
    for hh in range(0,24):#ชั่วโมง
        for mn in range(0,60,15): #นาที                
#            pat1=dd[6:]+'/'+dd[4:6]+'/'+dd[0:4]
            pat=dd[6:]+'/'+dd[4:6]+'/'+dd[0:4]+' '+"{:02d}".format(hh)+':'+"{:02d}".format(mn)+':'+'00' #คอลัมน์1 ของ g
            tt=dd+"{:02d}".format(hh)+"{:02d}".format(mn) #เวลา yyyymmddhhmn
            print('>>>','tt:',tt,pat)
            
            #ลิสสำหรับเก็บข้อมูลฝนที่ตรงกับ pat ของแต่ละสถานีในเวลา15นาที tt นั้นๆ
            gg=[]
                    
            #ลูปเพื่อเปิดแต่ละสถานีเพื่อที่จะดึงตามเวลา 15 นาทีในแต่ละไฟล์
            for s in st:#สถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
                gf=pathGauge+s+'.csv' #ข้อมูลไฟล์สถานีไหม
                if os.path.isfile(gf): #ตรวจว่ามีข้อมูลไฟล์สถานีไหม
                    
                    #เปิดไฟล์สถานี s
                    with open(gf, 'r') as f:
                        g = list(csv.reader(f, delimiter=','))
                    g=np.asarray(g)
                    
                    #ดึงข้อมูลฝนราย15นาทีจากข้อมูลดิบสถานี s ที่ตรงกับ pat
                    data=g[np.where(np.isin(g[:,1], pat))]                        
                    
                    #เก็บข้อมูลฝนราย15นาทีที่ดึงได้มาไว้ในลิสจนครบทุกสถานี
                    gg.append((data[0]))
                    
#                    print('.....',s,len(g),len(data),data[0])
            
            #เซฟเป็นไฟล์ csv ของเวลาราย15นาทีนั้นๆ tt+'.csv'
            gf = open(outpRain15m+tt+'.csv', 'w',newline='') #newline='' เพื่อป้องกันการเพิ่มบรรทัดตอนเซฟ csv
            with gf:
                w = csv.writer(gf)
                w.writerows(gg)                
#            break            

#        break
            
print('เสร็จสิ้นการดึงข้อมูลฝนราย15นาทีของแต่ละสถานีฝน..............')

