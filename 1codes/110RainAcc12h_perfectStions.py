'''
20200612
ฝนสะสมราย12ชั่วโมงของสถานีที่มีข้อมูลฝนสมบูรณ์ ปรับปรุงจาก "109"

'''

import csv
import numpy as np
import os
import fnmatch

gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด
pathGauge='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/1gauge_org/' #เป็นโฟลเดอร์เก็บข้อมูลดิบฝนแต่ละสถานี
outpRain12h='D:/tmp/PyQGIS/Plugin_practice/z_temp/1outp_gauge_temp/1gauge12h/'#เป็นโฟลเดอร์เก็บข้อมูลผลลัพธ์ฝนราย12ชมของสถานีที่สมบูรณ์ที่ได้จากไฟล์"105"

#สถานีวัดฝนที่สมบูรณ์จากไฟล์"105"
with open(gaugeName+'list_passedQG_gauges.csv', 'r') as f:
    st = list(csv.reader(f, delimiter=','))[0]
print(st)

print('เริ่มการสะสมฝน12ชั่วโมงจากการดึงข้อมูลฝนราย15นาทีของแต่ละสถานีฝน..............')
#วันเวลาที่ต้องการรวมไฟล์ฝนราย12ชั่วโมง
time=['20180717','20180718']     #เพิ่มวันที่ต้องการ
#ลูปเวลาเพื่อดึงตามเวลา 15 นาทีในแต่ละไฟล์
for dd in time: #วัน
    #ลูป 2 รอบใน 1 วัน
    for n in range(2): #2 คือ 24/12 สะสมฝนทุกๆ12ชม.
        print('ทำการสะสมฝนราย12ชั่วโมง...'+dd+"{:02d}".format(n*12))
        start=n*12
        stop=start+12
        
        gg=[] #ลิสเก็บชื่อไฟล์ที่หาได้ในแต่ละชั่วโมงที่ต้องการ ในที่นี้ทีละ12ชั่วโมง
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
                    
                sum_rr=0.0
                i=1
                for hh in range(start,stop): #ลูป12ชั่วโมงที่ต้องการ           
                        
                    pat=dd[6:]+'/'+dd[4:6]+'/'+dd[0:4]+' '+"{:02d}".format(hh) #ใช้คอลัมน์1 ของ g
                    if i==1:hh_start=dd+"{:02d}".format(start) #ชื่อไฟล์ชั่วโมงแรกของ12ชั่วโมงที่กำลังสะสม
                    tt=dd+"{:02d}".format(hh) #เวลา yyyymmddhh
#                    print('>>>','tt:',tt,'pat:',pat)            
                                    
                    #ใช้ pat (ymd) หาว่าช่วงเวลาที่ต้องการอยู่ในแถวใดบ้าง
                    data=g[np.where(np.isin(g[:,1], pat))]    
                    rr=sum([float(data[i][2])for i in range(len(data))]) #รวมฝนในชั่วโมงที่ตรงกับ pat
                    sum_rr+=rr
                    i+=1
                        
#                    print('.....',len(data),rr,sum_rr)                    
                    data=[str(s),hh_start,str(sum_rr)]
                    
                #เก็บข้อมูลฝนสะสมราย12 ชั่วโมงที่ดึงมาจากฝน15นาทีมาเก็บในลิสจนครบทุกสถานี
                gg.append((data))
                    
        #เซฟ gg เป็น csv ตามชื่อไฟล์
        #เซฟเป็นไฟล์ csv ของเวลาราย15นาทีนั้นๆ tt+'.csv'
        gf = open(outpRain12h+hh_start+'.csv', 'w',newline='') #newline='' เพื่อป้องกันการเพิ่มบรรทัดตอนเซฟ csv
        with gf:
            w = csv.writer(gf)
            w.writerows(gg)         
#        break
#    break
print('เสร็จสิ้นการสะสมฝน12ชั่วโมงจากการดึงข้อมูลฝนราย15นาทีของแต่ละสถานีฝน..............')
