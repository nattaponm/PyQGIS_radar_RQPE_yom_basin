'''
20200612 สร้างไฟล์ฝนสะสมราย1ชั่วโมง สะสมจากฝน15นาที จากลิสไฟล์สถานีที่ตรวจแล้วว่ามีข้อมูลสมบูรณ์จากไฟล์"105"

ต่อไปจะทำฝนสะสมราย 3ชั่วโมง (6,12,24)

'''

import csv
import numpy as np
import os
import fnmatch

gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด
pathGauge='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/1gauge_org/' #เป็นโฟลเดอร์เก็บข้อมูลดิบฝนแต่ละสถานี
outpRain1h='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_gauge_temp/1gauge1h/'#เป็นโฟลเดอร์เก็บข้อมูลผลลัพธ์ฝนราย1ชมของสถานีที่สมบูรณ์ที่ได้จากไฟล์"105"

#สถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
with open(gaugeName+'list_passedQG_gauges.csv', 'r') as f:
    st = list(csv.reader(f, delimiter=','))[0]
print(st)


print('เริ่มการสะสมฝน1ชั่วโมงจากการดึงข้อมูลฝนราย15นาทีของแต่ละสถานีฝน..............')
#วันเวลาที่ต้องการรวมไฟล์ฝนราย1ชั่วโมง
time=['20180717','20180718']     #เพิ่มวันที่ต้องการ
#ลูปเวลาเพื่อดึงตามเวลา 15 นาทีในแต่ละไฟล์
for dd in time: #วัน
    for hh in range(0,24):#ชั่วโมง
        pat=dd[6:]+'/'+dd[4:6]+'/'+dd[0:4]+' '+"{:02d}".format(hh) #ใช้คอลัมน์1 ของ g
        tt=dd+"{:02d}".format(hh) #เวลา yyyymmddhh
        print('>>>','tt:',tt,'pat:',pat)
        
        #ลิสสำหรับเก็บข้อมูลฝนสะสมราย 1 ชั่วโมงที่ตรงกับ pat ของแต่ละสถานี ดึงจากฝนราย15นาที tt นั้นๆ
        gg=[]
                    
        #ลูปเพื่อเปิดแต่ละสถานีเพื่อที่จะดึงตามเวลา 15 นาทีในแต่ละไฟล์
        for s in st:#สถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
            gf=pathGauge+s+'.csv' #ข้อมูลไฟล์สถานีไหม
            if os.path.isfile(gf): #ตรวจว่ามีข้อมูลไฟล์สถานีไหม
                    
                #เปิดไฟล์สถานี s
                with open(gf, 'r') as f:
                    g = list(csv.reader(f, delimiter=','))
                g=np.asarray(g)
                
                #กรองเอาแถวที่มีเวลาตรงกับ pat 
                #1.ต้องจัดระเบียบไฟล์ก่อน โดยเอาวันเดือนปี+ชั่วโมงของคอลัมน์2ไปแทนคอลัมน์1 ของ g
                a=[]
                a+=[re.sub(i[-6:], '', i) for i in g[:,1]]
                g[:,1]=a
                                
                #ใช้ pat (ymd) หาว่าช่วงเวลาที่ต้องการอยู่ในแถวใดบ้าง
                data=g[np.where(np.isin(g[:,1], pat))]    
                rr=sum([float(data[i][2])for i in range(len(data))]) #รวมฝนในชั่วโมงที่ตรงกับ pat
                data=[data[0][0],data[0][1],str(rr)]
                
                #เก็บข้อมูลฝนสะสมราย1 ชั่วโมงที่ดึงมาจากฝน15นาทีมาเก็บในลิสจนครบทุกสถานี
                gg.append((data))
                
#                print('.....',s,len(g),len(data),data)
                    
        #เซฟเป็นไฟล์ csv ของเวลาราย15นาทีนั้นๆ tt+'.csv'
        gf = open(outpRain1h+tt+'.csv', 'w',newline='') #newline='' เพื่อป้องกันการเพิ่มบรรทัดตอนเซฟ csv
        with gf:
            w = csv.writer(gf)
            w.writerows(gg)                
                
#        break
#    break
        
print('เสร็จสิ้นการสะสมฝน1ชั่วโมงจากการดึงข้อมูลฝนราย15นาทีของแต่ละสถานีฝน..............')
        
        
        
        
        