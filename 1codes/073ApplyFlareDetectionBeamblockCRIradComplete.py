'''
2020.05.30 หา radar flare กับ beamblock เชียงราย
ใช้โค้ดจากไฟล์ "071"
1.คำนวนหา radarflare ก่อน สองรอบ
2.หา beamblock จากการผลลัพธ์ราสเตอร์ที่ได้ทำไว้ในโค้ด "072"
3.อัพเดทค่ารหัสคุณภาพเรดาร์คอลัมน์ RQI (0,1,2,3=ดี,flare,bb,flare+bb)

ต่อไปจะนำไปโมเสคกับเรดาร์พิษณุโลก

'''

import numpy as np
from scipy.stats import linregress

#-------------------------------------------------------------------------------
def copyRad(pLayer,phLayer,pr_phs):    
    print('คัดลอกเรดาร์เชียงราย.....')
    i=0
    for f in pLayer.getFeatures():
        poly = QgsFeature()
        #สร้างชิ้นรูปปิดกริดจากชุดข้อมูลจุดด้านบน ดูค่าตัวแปร poly ด้านบน
        poly.setGeometry(f.geometry())
        #-update feature
        poly.setAttributes([i,f['value'],f['radialAng'],f['heightRel']])
        pr_phs.addFeatures([poly]) #อัพเดทค่ารูปปิดชิ้นที่กำลังทำงานผ่าน dataProvider หรือ pr
        phLayer.updateExtents() #อัพเดท map
        i+=1

#-------------------------------------------------------------------------------
def radarFlareDetectionRound1(phLayer,PC_BinWithVal,Corr,dist):
    print('ค้นหา radar flare ตามมุม รอบที่ 1.....')
    #หาค่ามุมทั้งหมดของเรดาร์
    idx = phLayer.fields().indexOf('radialAng')
    values = phLayer.uniqueValues(idx)

    phLayer.startEditing()
    i=0
    
    #ลูปทีละมุมเพื่อคำนวนค่าสถิติ
    for ang in values:
#        if i<10:print('angle:',ang)
        #อ่านเพิ่ม selectByExpression https://gis.stackexchange.com/questions/340961/pyqgis-using-variable-instead-of-number-in-selectbyexpression-query
        #อ่านเพิ่ม https://docs.qgis.org/testing/pdf/en/QGIS-testing-PyQGISDeveloperCookbook-en.pdf
        #    req = QgsFeatureRequest().setFilterExpression(' "radialAng" == "ang" ') #ไม่ใช้แบบนี้
        phLayer.selectByExpression('"radialAng" = {}'.format(ang))
        ct=phLayer.selectedFeatureCount()
       
        #เก็บค่าระยะทางและการสะท้อนสู่ลิสเพื่อนำไปคำนวนสถิติ
        val_list=[]
        for f in phLayer.selectedFeatures():
            val_list.append((f.id(),f['value'])) 
    #        if i<1:print(f.id(),f['value'])

        dv=np.array(val_list) #แปลงเป็นอาเรย์

        slope, intercept, r_value, p_value, std_err = linregress(dv[:,0], dv[:,1])
    #    print(slope)
        
        #ลูปเติมค่าในคอลัมน์ของแต่ละฟีเจอร์        
        for k,f in enumerate(phLayer.selectedFeatures()):
            phLayer.changeAttributeValue(f.id(),4,k)
            phLayer.changeAttributeValue(f.id(),5,ct)
            phLayer.changeAttributeValue(f.id(),6,(ct/dist)*100.0) #240 คือจำนวน bin ถ้า gatsize=1.0km
            phLayer.changeAttributeValue(f.id(),7,str(np.min(dv[:,1])))
            phLayer.changeAttributeValue(f.id(),8,str(np.max(dv[:,1])))
            phLayer.changeAttributeValue(f.id(),9,str(np.mean(dv[:,1])))
            phLayer.changeAttributeValue(f.id(),10,str(np.std(dv[:,1])))
            phLayer.changeAttributeValue(f.id(),11,str(slope)) #slope of regression line (distance vs dbz)
            phLayer.changeAttributeValue(f.id(),12,str(r_value)) #coorelation coefficients (distance vs dbz)
            
            #ค่าเปอร์เซ็นต์ของการมีอยู่ของค่าการสะท้อนกับค่าสหสัมพันธ์ถูกนำมาใช้ โดยทดลองหา sensitivity test
            #85 & 0.85 คือค่าที่คิดว่าดีในตอนนี้
            if ((ct/dist)*100.0)>=PC_BinWithVal and r_value>=Corr : 
                phLayer.changeAttributeValue(f.id(),13,1)#1=flare
            else:
                phLayer.changeAttributeValue(f.id(),13,0)#0=ok

        i+=1
    phLayer.commitChanges()
#-------------------------------------------------------------------------------
#refine เพื่อหา radar flare ขนาดใหญ่ที่ยังตกค้างจากการหารอบแรก 
#ในรอบนี้จะใช้ "PC_BinWithVal">=0.80 และ"Corr">=0.5 และต้องเป็นมุมที่อยู่ข้าง Flare=1 ที่หาในรอบแรกไปแล้ว
#ค่า "Corr">=0.5 นี้เป็นตามสมมติฐานที่ว่าความสัมพันธ์แบบ linear ไม่เหมาะสมกับ flare ทำให้ค่า corr ต่ำ
#แม้ว่าค่า "Corr">=0.5 จะต่ำ แต่ก็ยังแสดงให้เห็นว่ามีความสัมพันธ์ การใช้ nonlinear จะทำให้พบความสัมพันธ์
#ที่อาจจะให้ค่า R2 ที่สูงก็ตาม แต่จะทำให้การคำนวนใช้เวลาเพิ่มไปอีก จะทำให้ไม่เหมาะกับการใช้งานจริงของ TMD
#นิสิตอาจลองใช้ nonlinear เก็บ radar flare ในรอบ refine นี้ก็ได้ ลองใช้ y=x^2 ก่อน


def radarFlareDetectionRound2(phLayer,PC_BinWithVal,Corr):
    print('ค้นหา radar flare ตามมุม รอบที่ 2.....')
    #หาค่ามุมทั้งหมดของเรดาร์
    idx = phLayer.fields().indexOf('radialAng')
    values = phLayer.uniqueValues(idx)

    phLayer.startEditing()
    
    #เก็บมุมทั้งหมดในลิส
    flare_ang_list=[]
    for ang in values:
        phLayer.selectByExpression('"radialAng" = {}'.format(ang))
        for k,f in enumerate(phLayer.selectedFeatures()):
            flare_ang_list.append((ang,f['Flare1']))
            break
    
    #แปลงลิสมุมเป็นอาเรย์ numpy
    np_flare=np.array(flare_ang_list)
        
    #หาอินเด็กซ์ของมุมที่พบ flare
    id_fl=np.where(np_flare[:,1]==1)   
    
    #สร้างลิสหามุมข้างเคียงของ Flare ในรอบแรก
    flare_list=[] #ลิสของมุมที่มีแต่flare เท่านั้น
    for id in id_fl[0]:        
        #กรณีที่ flare ไม่ได้เป็นมุมแรกและมุมสุดท้าย        
        if id>0 and id<(len(flare_ang_list)-1):
            pre_id=id-1 #อินเด็กซ์ก่อน flare
            pot_id=id+1 #อินเด็กหลัง flare
            flare_list.append(np_flare[pre_id,0])
            flare_list.append(np_flare[pot_id,0])
        
        #กรณีที่มุมของ flare เป็นมุมแรกของ sweep
        if id==0: flare_list.append(np_flare[id+1,0]) #ให้อินเด็กซ์เป็น +1
        
        #กรณีที่มุมของ flare เป็นมุมสุดท้ายของ sweep ให้อินเด็กซ์เป็น -1
        if id==len(np_flare[:,1])-1: flare_list.append(np_flare[id-1,0])
    
    #flare_list คือ ลิสของมุมที่คาดว่าน่าจะเป็น flare ที่ตกค้างจากการใช้ linear regression ในรอบแรก
    #โดยเป็น range ที่อยู่ข้างๆกับ flare ในรอบแรก ซึ่งจะไปกรองอีกสองค่าดังลูปด้านล่าง
    
    #ลูปเพื่ออัพเดท flare รอบ 2
    for ang in set(flare_list): #ใช้ set เพราะจะเอามุมที่เป็น unique จริงๆ
        phLayer.selectByExpression('"radialAng" = {}'.format(ang))
        
        for k,f in enumerate(phLayer.selectedFeatures()):
#            print(ang,f['PC_BinWithVal'],f['Corr'])
            if int(f['Flare1'])==1:continue   #ไม่คำนวน flare ที่ตรวจได้ในรอบแรก
#            if (f['PC_BinWithVal']>=85.0 and f['Corr']>=0.50) :  #ใช้ corr=0.50 เพื่อเก็บตก flare จากรอบแรก
            if float(f['PC_BinWithVal'])<PC_BinWithVal: continue
            if float(f['Corr'])<Corr: continue  #ใช้ corr=0.50 เพื่อเก็บตก flare จากรอบแรก
#            print('ang',ang)
            phLayer.changeAttributeValue(f.id(),14,2)#2=flare ที่ตกค้างมาจากรอบแรก "flare2"
            phLayer.changeAttributeValue(f.id(),13,2)#2=flare ที่ตกค้างมาจากรอบแรก "flare1"

    #ลูปเพื่ออัพเดทค่า value ที่ไม่มีและมี flare ลงในคอลัมน์ผลลัพธ์ "valueFlare"
    for ang in values:
        phLayer.selectByExpression('"radialAng" = {}'.format(ang))
        for k,f in enumerate(phLayer.selectedFeatures()):
            if int(f['Flare1'])==0:
                phLayer.changeAttributeValue(f.id(),15,float(f['value']))
            else:
                phLayer.changeAttributeValue(f.id(),15,-999.00)
    
    
    
    phLayer.commitChanges()
#-------------------------------------------------------------------------------
def interpolateNearFlarebyIDW(phLayer,geom):
    print('ประมาณค่า dbz รอบข้าง flare......')
    #เก็บมุมทั้งหมดใส่ลิส
    idx = phLayer.fields().indexOf('radialAng')
    values = phLayer.uniqueValues(idx)
    ang_list=list(values)
    ang_list.sort() #จัดเรียงมุมนในลิสเพื่อจะนำไปหาอินเด็กซ์

    #เก็บมุมที่พบ flare ทั้งหมดในลิส
    flare_ang_list=[]
    phLayer.selectByExpression('"valueFlare" = {}'.format(-999.0))
    for k,f in enumerate(phLayer.selectedFeatures()):
        flare_ang_list.append((f['radialAng']))
    flare_list=set(flare_ang_list)

    #ลูปเพื่อหาค่าด้วย idw
    #นำมุมข้างๆที่พบ flare ไปเป็นค่า idw
    print('ประมาณค่า dbz ข้างๆ มุมที่เป็น radar flare ...')
    phLayer.startEditing()
    for ang in flare_list:
        id=ang_list.index(ang) #หาค่ามุมจากค่าอินเด็กซ์ข้างๆตามกรณีด้านล่าง
        if id>0 and id<len(ang_list):
            pre_id=id-1
            pst_id=id+1
        
        if id==0:
            pre_id=0
            pst_id=id+1
        
        if id==len(ang_list):
            pre_id=id-1
            pst_id=id
        
        val_list=[ang_list[pre_id],ang_list[pst_id]] #มุมข้างๆ flare ในแต่ละครั้งของลูป
        

        phLayer.selectByExpression('"radialAng" = {}'.format(ang))#ang คือ มุมที่พบ flare
        #ลูปเฉพาะมุมที่เป็น flare เพื่อหา centroid 
        for k,f in enumerate(phLayer.selectedFeatures()):
                
            #สร้างลิสเปล่าเก็บระยะทางและค่า dbz
            dist_val=[]

            #สร้างลิสถ่วงค่าน้ำหนักตามระยะทางที่ห่างออกไป
            w_list=[]        
                
            #หา centroid ของ f
            pt_f=f.geometry().centroid().asPoint()
            #หาระยะทางของ f กับจุดสถานีเรดาร์
            distance = QgsDistanceArea()
            d = distance.measureLine(pt_f, geom.asPoint()) #ระยะทางของจุด f กับ จุดสถานีเรดาร์ (m)
                        
            #หา effective radius ตามระยะทางโดยเรดาร์บีม assume ที่ 1.0 องศา
            #-http://www.1728.org/angsize.htm        
            re=np.tan(np.radians(1.0/2))*2*(d/1000) #หน่วย กม.
    #        print(d,re,ang,f['valueFlare'])
                
            #สร้างรูปปิดจาก effective radius เพื่อนำไป intersect กับค่าศก.เรดาร์ที่ตกในเงื่อนไข
            poly=QgsFeature()
            rem=re*1000.0 #effective radius หน่วยเมตร
                
            ll=pt_f[0]-rem,pt_f[1]-rem
            ul=pt_f[0]-rem,pt_f[1]+rem
            ur=pt_f[0]+rem,pt_f[1]+rem
            lr=pt_f[0]-rem,pt_f[1]-rem        
                
            points = [QgsPointXY(ll[0],ll[1]),QgsPointXY(ul[0],ul[1]),\
                    QgsPointXY(ur[0],ur[1]),QgsPointXY(lr[0],lr[1])]
                
            poly.setGeometry(QgsGeometry.fromPolygonXY([points]))
            
            #ลูปมุมข้างๆทั้งสองเพื่อนำมาตรวจเงื่อนไขแล้วถ้าตรง จะเก็บในลิสเพื่อทำ idw
            for ba in val_list: #ตรงนี้จะช้ามาก เพราะต้องลูปทุกฟีเจอร์ในทั้งสองมุม
                phLayer.selectByExpression('"radialAng" = {}'.format(ba)) #ใช้ซ้ำกับลูปบนได้หรือไม่
                for kk,fa in enumerate(phLayer.selectedFeatures()):
                    if fa.geometry().intersects(poly.geometry()): #spatial intersect การกรองครั้งแรก
                        pt_fa=fa.geometry().centroid().asPoint()
                                
                        #หาระยะทางของ fa รอบๆ กับจุดศก.เรดาร์ที่มี flare กรองครั้งที่สอง
                        dist = QgsDistanceArea()
                        dt = distance.measureLine(pt_f, pt_fa) #ระยะทางของจุด f กับ fa์ (m)
                        if dt<rem and fa['valueFlare']>-999:
                                
                            #-เพิ่มค่าระยะ่ทางที่คำนวนได้ กับค่าการสะท้อน(value)ของ fa เข้าไปในลิส
                            dist_val.append((dt,fa['valueFlare']))
            
                            #ถ้าระยะทางมากกว่า 0 แต่ยังอยู่ในรัศมีให้ถ่วงน้ำหนักตามระยะทางแล้วนำไปเก็บใน list ของค่าถ่วงน้ำหนัก
                            if dt>0:    
                                w=1/dt
                                w_list.append(w)
                            #    break                
                            else:
                                w_list.append(0)                     
            
            if len(dist_val)==0:continue #ถ้าไม่มีจุดตกในรัศมี effective radius ของ pt_f เลย ให้วน
            
#            print(dist_val)
            
            w_check=0 in w_list
            dv=np.array(dist_val) #แปลงเป็นอาเรย์
            if w_check==True:
                idx=w_list.index(0) #หาตำแหน่งในลิสว่าตรงไหนที่มีค่าน้ำหนักเป็น 0
                z_idw=dv[idx,1] ##กำหนดให้ใช้ค่าที่ตรงกับพิกัดของกริดเล็กนั้นเลย โดยไม่สนใจว่าจะมีค่าอื่นที่อยู่ในรัศมีนั้นหรือไม่
                phLayer.changeAttributeValue(f.id(),15,float(z_idw)) 
            else:
                wt=np.transpose(w_list)
                z_idw=np.dot(dv[:,1],wt)/sum(w_list) # ใช้ dot product เพื่อคำนวนหาค่าdbzด้วยวิธีการ idw จะได้ค่าเดียว
                # อ่านเพิ่ม https://www.guru99.com/numpy-dot-product.html
                phLayer.changeAttributeValue(f.id(),15,float(z_idw)) 

    phLayer.commitChanges()
#-------------------------------------------------------------------------------
#เริ่มกระบวนการหา radar flare นำมาจากไฟล์ "070"
print('>>>>>หา radar flare และประมาณค่าข้างเคียงด้วย idw....')

#1.อ่านshapefile ข้อมูลดิบเรดาร์พิษณุโลก
path_to_rad_layer = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/rad_cri_utm201908041300.shp"
pLayer = QgsVectorLayer(path_to_rad_layer, "Rad_PHS", "ogr") #ค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
#QgsProject.instance().addMapLayers([pLayer])

#2.สร้างโดยคัดลอกข้อมูล 1. บางคอลัมน์ที่จะนำมาคำนวน
epsg = 32647 #กำหนดค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
uri = "Polygon?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
phLayer = QgsVectorLayer(uri, 'rad_CRI_final', 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
pr_phs = phLayer.dataProvider() #เก็บค่า dataProvider ของชั้นข้อมูลรูปปิด
#poly_phs = QgsFeature() #สร้าง instance ของ feature ที่จะใช้สร้างรูปปิดแต่ละชิ้น

#-เพิ่มหัวตารางโดยเก็บค่าบางคอลัมน์จากไฟล์ต้นฉบับบางส่วนและเพิ่มคอลัมน์ที่จะคำนวนสถิติเพื่อขจัด radar flare
pr_phs.addAttributes([QgsField("value", QVariant.Double,'double', 10, 3),
                     QgsField("radialAng", QVariant.Double,'double', 10, 3),
                     QgsField("heightRel", QVariant.Double,'double', 10, 3),
                     QgsField("ID", QVariant.Int,len=3),
                     QgsField("numBinWithVal", QVariant.Double,'double', 10, 3),
                     QgsField("PC_BinWithVal", QVariant.Double,'double', 10, 3),
                     QgsField("MinVal", QVariant.Double,'double', 10, 3),
                     QgsField("Max", QVariant.Double,'double', 10, 3),
                     QgsField("MeanVal", QVariant.Double,'double', 10, 3),
                     QgsField("SD", QVariant.Double,'double', 10, 3),
                     QgsField("Slope", QVariant.Double,'double', 10, 3),
                     QgsField("Corr", QVariant.Double,'double', 10, 3),
                     QgsField("Flare1", QVariant.Int),
                     QgsField("Flare2", QVariant.Int), 
                     QgsField("valueFlare", QVariant.Double,'double', 10, 3),
                     QgsField("BeamBlock", QVariant.Int,len=5),
                     QgsField("RQI", QVariant.Int,len=5)])
phLayer.updateFields() #update attribute

#-------------------------------------------------------------------------------
#ขนาดความละเอียดของการตรวจวัด ตรงนี้เพิ่มมาจาก 071
binSize=500.0

if binSize == 1000:
#รัศมีเรดาร์
#dist=240.0 #กิโลเมตร
    dist=237.0 #กิโลเมตร
else:
    dist=237.0*(1000/binSize) #กิโลเมตร
#-------------------------------------------------------------------------------
#คัดลอกเรดาร์พิษณุโลก
copyRad(pLayer,phLayer,pr_phs)
#-------------------------------------------------------------------------------
#ตรวจวัดRadar flare รอบที่ 1
PC_BinWithVal=85.0
Corr=0.85
radarFlareDetectionRound1(phLayer,PC_BinWithVal,Corr,dist)
#radarFlareDetectionRound1(phLayer,PC_BinWithVal,Corr)

#-------------------------------------------------------------------------------
#ตรวจวัดRadar flare รอบที่ 2
PC_BinWithVal=80.0
Corr=0.50
radarFlareDetectionRound2(phLayer,PC_BinWithVal,Corr)
#-------------------------------------------------------------------------------
#การนำค่ากริดรอบๆของ flare มาประมาณค่าด้วย idw เพื่อเติมค่า วิธีนี้ต้องใช้รัศมีตาม effective radius
#tan(theta/2)=size/(2*dist) โดยที่ size คือด้านที่ต้องการหา ส่วน dist คือ ระยะของกริดนั้นๆกับสถานี
#โดยที่ theta คือ beamwidth ในที่นี้ให้ทดลอง 1 degree ก่อน ยิ่งไกลค่า size จะใหญ่ขึ้นตามระยะทาง
#geom = QgsGeometry(QgsPoint(100.2174233,16.7755399)) # นำพิกัดสถานีมาจากกุเกิ้ล
geom = QgsGeometry(QgsPoint(99.88159181,19.96147083)) # นำพิกัดสถานีมาจากประมาณจุดกลางของเรดาร์ shapefile
sourceCrs = QgsCoordinateReferenceSystem(4326)
destCrs = QgsCoordinateReferenceSystem(32647)
tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
geom.transform(tr)

uri = "Point?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
ptLayer = QgsVectorLayer(uri, 'point_rad_CRI', 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
pr_pt = ptLayer.dataProvider()
pt_rd=QgsFeature()
pt_rd.setGeometry(QgsGeometry.fromPointXY(geom.asPoint()))
pr_pt.addFeatures([pt_rd])
ptLayer.updateExtents()


#เรียกฟังค์ชั่นประมาณค่า dbz ข้างเคียงกับเรดาร์ flare ให้เข้าไปเติมบริเวณ flare ด้วย IDW
interpolateNearFlarebyIDW(phLayer,geom)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#เริ่มกระบวนการสกัดค่า beamblock ที่เป็นผลจากไฟล์ "072"
#-------------------------------------------------------------------------------
def ExtractBeamBlockByCentroid(phLayer,rLayer):
    print('สกัดค่า BeamBlock....')
    phLayer.startEditing()
    for f in phLayer.getFeatures():
        #สร้างจุดจาก centroid ของรูปปิด    
        pts = f.geometry().centroid().asPoint() #get ค่าพิกัด centroid ของกริดแล้วสร้างให้เป็นจุด
        
        #นำค่าจุดมาสกัดค่า beamblock
        val, res = rLayer.dataProvider().sample(QgsPointXY(pts[0],pts[1]), 1) #val คือค่าbeamblockที่รีเทิร์นกลับมาจากการสกัดด้วยจุด sample    
        
        #อัพเดทเฉพาะค่า beamblock ในไฟล์ pLayer
        if np.isnan(val):
            phLayer.changeAttributeValue(f.id(),16,0)
        else:
            phLayer.changeAttributeValue(f.id(),16,val)


    phLayer.commitChanges()    
    print('เสร็จสิ้นการสกัดค่า BeamBlock....')        
#-------------------------------------------------------------------------------
#เปิดราสเตอร์ผลลัพธ์การคำนวน beamblock 
path_to_beamblock = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/BeamBlockChiangraiRaster.tif"
rLayer = QgsRasterLayer(path_to_beamblock , "BeamBlock_CRI")
#-------------------------------------------------------------------------------
#สกัดค่า beamblock เข้าสู่เวกเตอร์เรดาร์
ExtractBeamBlockByCentroid(phLayer,rLayer)
#-------------------------------------------------------------------------------
#อัพเดทคอลัมน์ RQI โดย 0=bin is clear,1=Flare,2=Beamblock,3=Flare+Beamblock
def updateRQI(phLayer):
    print('กำลังอัพเดทคอลัมน์ RQI...')
    phLayer.startEditing()
    #for az in values:
    phLayer.selectByExpression('"Flare1" = {} AND "BeamBlock" = {}'.format(0,0))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),17,0)

    phLayer.selectByExpression('"Flare1" = {} AND "BeamBlock" = {}'.format(0,1))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),17,2)

    phLayer.selectByExpression('"Flare1" >= {} AND "BeamBlock" = {}'.format(1,0))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),17,1)

    phLayer.selectByExpression('"Flare1" >= {} AND "BeamBlock" = {}'.format(1,1))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),17,3)

    phLayer.commitChanges() 
    print('เสร็จสิ้นการอัพเดทคอลัมน์ RQI...')
updateRQI(phLayer)
#-------------------------------------------------------------------------------

#แสดงผลในแผนที่
QgsProject.instance().addMapLayers([phLayer])
QgsProject.instance().addMapLayers([rLayer])
#-------------------------------------------------------------------------------