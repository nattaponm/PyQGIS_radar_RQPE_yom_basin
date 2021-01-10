'''
20200612 QCความสมบูรณ์ของสถานีฝนแบบหลายวัน
โปรแกรมQC ความสมบูรณ์ของสถานีวัดฝน จะกรองเฉพาะสถานีที่ไม่มี None เลยในช่วงวันที่ต้องการ
ส่งออกผลเป็นลิสชื่อสถานี จำนวนสถานีที่สมบูรณ์และไม่สมบูรณ์ในช่วงเวลาที่ต้องการ

ต่อไปจะนำลิสรายชื่อสถานี ออกไปสร้างฝนราย15นาที รวมสถานีที่ผ่าน QC ในเวลานั้นๆ
'''

import csv
import numpy as np
import os
import fnmatch
import re

def qc_gauge_completeness(st,ymd):
    '''
    โปรแกรมQC ความสมบูรณ์ของสถานีวัดฝน จะกรองเฉพาะสถานีที่ไม่มี None เลยในช่วงวันที่ต้องการ
    ส่งออกผลเป็นลิสชื่อสถานี จำนวนสถานีที่สมบูรณ์และไม่สมบูรณ์ในช่วงเวลาที่ต้องการ
    '''
    sta=[]
    ko,kn=(0,0)
    print('.....เริ่มการตรวจความสมบูรณ์ของฝนสถานีวันที่...'+ymd)
    for sn in st: #ลูปชื่อสถานี
            fn=sn+'.csv'
#            print('>>>',sn)
            
            if os.path.isfile(pathGauge+fn): #ตรวจว่ามีข้อมูลไฟล์สถานีไหม
                with open(pathGauge+fn, 'r') as f:
                    g = list(csv.reader(f, delimiter=','))
                g=np.asarray(g)
                
                #กรองเอาเฉพาะวันเวลาที่ต้องการไปใช้งาน
                pat=ymd[6:]+'/'+ymd[4:6]+'/'+ymd[0:4]
                
                #กรองเอาแถวที่มีเวลาตรงกับ pat 
                #1.ต้องจัดระเบียบไฟล์ก่อน โดยเอาวันเดือนปีของคอลัมน์2ไปแทนคอลัมน์1 ของ g
                a=[]
                a+=[re.sub(i[-9:], '', i) for i in g[:,1]]
                g[:,0]=a
                
                #2.เอาชั่วโมงนาทีและวินาทีของคอลัมน์2ไปแทนคอลัมน์2 ของ g (แทนที่เดิมเลย)
                b=[]
                b+=[re.sub(i[0:11], '', i) for i in g[:,1]]
                g[:,1]=b
                
                #ใช้ pat (ymd) หาว่าช่วงเวลาที่ต้องการอยู่ในแถวใดบ้าง
                data=g[np.where(np.isin(g[:,0], pat))]       
                
                #อ่าน https://stackoverflow.com/questions/51030608/finding-indices-of-values-in-2d-numpy-array
                #อ่าน https://stackoverflow.com/questions/40976714/string-slicing-in-numpy-array
                
                #ตรวจความสมบูรณ์ของ data ว่ามี "None" ไหม ถ้าไม่มีให้เก็บในลิสเพื่อจะ write เป็น csv เก็บไว้เพื่อไปรวมไฟล์ต่อ
                if len(data[data[:,2]=='None'])==0:
                    sta.append(sn) #write ออกไปเป็นไฟล์ของสถานีที่สมบูรณ์ นำไป validate
                    ko +=1
                    print('.....สถานี ',sn, ' สมบูรณ์ มีความยาว None',len(data[data[:,2]=='None']))
                else:
                    kn +=1
                    print('.....สถานี ',sn,' *ไม่*สมบูรณ์ มีความยาว None',len(data[data[:,2]=='None']))
    print('.....เสร็จสิ้นการตรวจความสมบูรณ์ของฝนสถานีวันที่...'+ymd)
    return sta,ko,kn

#-------------------------------------------------------------------------------
#อ่านสถานี
gaugeName='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/' #เป็นโฟลเดอร์ของไฟล์ชื่อสถานีพร้อมพิกัด
pathGauge='D:/tmp/PyQGIS/Plugin_practice/1data/1gauges_yom2018/1gauge_org/' #เป็นโฟลเดอร์เก็บข้อมูลดิบฝนแต่ละสถานี
with open(gaugeName+'1สถานีวัดฝนกรมอุตุลุ่มน้ำยม2018.csv', 'r') as f:
    st = list(csv.reader(f, delimiter=','))

st=np.asarray(st[1:])[:,0] #ชื่อสถานีไม่เอา header

#วันเวลาที่ต้องการQC
time=['20180715','20180716','20180717', '20180718','20180719','20180720','20180721','20180722','20180723','20180724'] #พายุsontihn
res=[]#เก็บผลการqc 
i=0
for ymd in time:
    i+=1
    print('*'*50)     
    print('ตรวจความสมบูรณ์ของสถานีวัดฝนวันที่',i,': ',ymd )
    print('*'*50)
    st,ko,kn=qc_gauge_completeness(st,ymd)    #st,ko,kn รายชื่อสถานีที่สมบูรณ์,จำนวนสถานีที่สมบูรณ์,จำนวนสถานีที่ไม่สบูรณ์
    res.append((ymd,st,ko,kn)) #เก็บผลการqc    

#เซฟ res[6][1] เป็น csv เพื่อนำไปใช้รวมฝน
gf = open(gaugeName+'list_passedQG_gauges.csv', 'w')
gaugeLists=res[6][1]
with gf:
   w = csv.writer(gf)
   w.writerow(gaugeLists)

print('*'*50)
print('เสร็จสิ้นการตรวจสอบความสมบูรณ์ของสถานีฝน..............')