'''
20200528 การคำนวนการบดบังของบีมจากภูมิประเทศแบบสมบูรณ์ จะนำไปเป็นไฟล์ต้นแบบเพื่อทำ spatial intersect กับทุกการสแกน
การสร้างรูปปิดของเรดาร์ของมุมยกแรกในทุกอซิมุทและทุกระยะทางด้วยการคำนวน radius effective ตามระยะทางและมุมของเรดาร
ใช้ค่ามุมจากการอ่านไฟล์ต้นฉบับเพื่อให้ได้อซิมุทของเรดาร์พิษณุโลก แล้วนำมาหารสองกับมุมข้างเคียงเพื่อให้ได้ตรงกลางของแนวสแกน
1.กำหนดค่าพิกัดสถานีแบบ geo และแปลงเป็น utm
2.อ่านข้อมูล shape ของเรดาร์พิษณุโลกเพื่อget ค่าอซิมุทจริงที่จะนำไปคำนวน beamwidth
3.สร้างชั้นรูปปิดผลลัพธ์ใน memory
4.สร้างคอลัมน์ของรูปปิด
5.คำนวนพิกัดเพื่อให้ได้จุดของมุมรูปปิด
6.นำพิกัดของจุดเหล่านั้นมาสร้างเป็นรูปปิด
7.คำนวนการบดบังลำบีมจากภูมิประเทศ (DEM)
7.อัพเดทตารางและแผนที่
8.แสดงผลแผนที่
9.ส่งผลออกเป็น shapefile และ ราสเตอร์ (แต่เราจะใช้ราสเตอร์ในการประมวลผลโค้ดต่อไป)

นำผลการคำนวน beamblock นี้ไปใช้หาการบดบังของแต่ละไฟล์ที่สแกนมาทุกๆ 15 นาที

'''
import math
import numpy as np
print('คำนวนลำบีมที่ถูกภูมิประเทศบดบังโดยใช้โครงสร้างของเรดาร์จริงของเรดาร์พิษณุโลก.............')
#-------------------------------------------------------------------------------
def CalcGeographicAngle(arith):
    #-to convert arithematic angle to geographic angle
    return (360 - arith + 90) % 360
#-------------------------------------------------------------------------------
def createPolyRadAlongAzimuth(numRange,dist,binSize,elevAng,pt_rd,pLayer,pr,h_rd,rad_alt):
    print('สร้างรูปปิดของกริดตามแนวอซิมัท....')
    #ค่าพารามิเตอร์สำหรับคำนวนความสูงของลำบีมจากระดับน้ำทะเลปานกลาง
    pi=3.14159265358979
    re=6374000  # รัศมีโลก (เมตร)
    rr=4.0/3.0*re # earth effective radius   
    
    #ลูปตามแนวมุมอซิมัทจากไฟล์ shape ต้นฉบับ
    k=0
    for az in values:
        azimuth=CalcGeographicAngle(az)#แปลงเป็นมุมอซิมัท
#        print('มุมอซิมัทที่:',az)
        
        #หาความกว้างของลำบีมตามกรณี
        if k==0: 
            beamWidth=(((values[0]+values[1])/2) - (values[len(values)-1]+values[0])/2 )%180
#            print('>>0',k,beamWidth)
        
        if k==(len(values)-1):
            beamWidth=((values[k]+values[0])/2)-((values[k-1]+values[k])/2)
#            print('>>L',k,beamWidth)
        
        if k>0 and k<(len(values)-1):
            beamWidth=((values[k]+values[k+1])/2)-((values[k-1]+values[k])/2)
        
        #เขียนกำกับกรณี error ใช้มุมตรงกลางมาคำนวน beamwidthแทน
        if (beamWidth < -5.0 or beamWidth>5.0):                
            beamWidth=(values[int(len(values)/2)+1]-values[int(len(values)/2)-1])/2
#            print('>>+',k,beamWidth)        

        
        #คำนวนมุมก่อนและหลังเพื่อนำไปหาค่าพิกัดปลายรูปปิด
        angle1 = math.radians(azimuth-(beamWidth/2)) #แปลงมุมอซิมัทเป็นเรเดียนสำหรับมุมก่อนหน้า
        angle2 = math.radians(azimuth+(beamWidth/2)) #แปลงมุมอซิมัทเป็นเรเดียนสำหรับมุมด้านหลัง    
    
        #ลูปตามแนวระยะทางที่กำหนด
        i=0
        for dt in range(int(dist)):    
#            print('ระยะ:',dt)

            #ระยะทางตามแนวรัศมีในหน่วยเมตร
            distance=(dt+1)*binSize #เมตร
            
            if i==0:#กรณีเป็น bin ที่ 1
                dist_x1, dist_y1 = (distance * math.cos(angle1), distance * math.sin(angle1))
                dist_x2, dist_y2 = (distance * math.cos(angle2), distance * math.sin(angle2))
                xp1, yp1 = (pt_rd[0] + dist_x1, pt_rd[1] + dist_y1)
                xp2, yp2 = (pt_rd[0] + dist_x2, pt_rd[1] + dist_y2)

                points = [QgsPointXY(pt_rd[0],pt_rd[1]),QgsPointXY(xp1,yp1),\
                                QgsPointXY(xp2,yp2)] 

            else:
                dist_x1, dist_y1 = ((distance-binSize) * math.cos(angle1), (distance-binSize) * math.sin(angle1))
                dist_x2, dist_y2 = ((distance-binSize) * math.cos(angle2), (distance-binSize) * math.sin(angle2))
                xp1, yp1 = (pt_rd[0] + dist_x1, pt_rd[1] + dist_y1)
                xp2, yp2 = (pt_rd[0] + dist_x2, pt_rd[1] + dist_y2)
                
                dist_x3, dist_y3 = (distance * math.cos(angle1), distance * math.sin(angle1))
                dist_x4, dist_y4 = (distance * math.cos(angle2), distance * math.sin(angle2))
                xp3, yp3 = (pt_rd[0] + dist_x3, pt_rd[1] + dist_y3)
                xp4, yp4 = (pt_rd[0] + dist_x4, pt_rd[1] + dist_y4)
                points = [QgsPointXY(xp1,yp1), QgsPointXY(xp2,yp2),\
                          QgsPointXY(xp4,yp4), QgsPointXY(xp3,yp3) ] 
                
            
            #คำนวน size ตาม effective radius ของมุมและระยะทาง
            size=np.tan(np.radians(beamWidth/2))*2*(distance/1000) #หน่วย กม.
#           print ("พิกัดที่คำนวนได้ตามมุม:",az,size,i+1,xfinal,yfinal )
            
            #-คำนวนความสูงของลำบีมในหน่วยเมตรcal beam height + rad altitude in meter. 
            beam_height= np.sqrt((distance)**2+rr**2+(2*(distance)*rr*np.sin(np.radians(elevAng))))-rr+h_rd+rad_alt #เมตร
            
            #สร้างชิ้นรูปปิดจากชุดข้อมูลจุดด้านบน ดูค่าตัวแปร poly ด้านบน
            poly = QgsFeature()
            poly.setGeometry(QgsGeometry.fromPolygonXY([points])) #ตั้งค่าเรขาคณิต
            poly.setAttributes([i,elevAng,az,distance,float(size),float(beam_height)]) #อัพเดทค่าในตาราง            
            pr.addFeatures([poly])
            pLayer.updateExtents()
            i+=1
        k+=1
    print('เสร็จสิ้นการสร้างรูปปิด....')
#-------------------------------------------------------------------------------
def findUniqueAngle(ppLayer):
    idx = ppLayer.fields().indexOf('radialAng')
    values = ppLayer.uniqueValues(idx)
    val=list(values)
    val.sort()
    list_ang=[]
    i=0
    #ต้องการนำมุมมาหารกันเพื่อให้มุมอยู่ตรงกลางรูปปิด
    for ang in val:
        if i<(len(val)-1):
            ang_cal=((val[i]%360)+(val[i+1]%360))/2
            #เขียนกำกับเพื่อแก้ปัญหามุมรองสุดท้ายที่คำนวนแล้วน้อยกว่า 300.0 โดยเลข 300.0 เป็นเพียงเลขตัวอย่างตามความเป็นจริง
            if i==(len(val)-2) and ang_cal<300.0: ang_cal=(list_ang[i-1]+1)%360.0
        
        if i==(len(val)-1): #มุมสุดท้าย จะถูกนำมารวมกับมุมแรกแล้วหารสอง
            ang_cal=(val[i]%360+(val[0]%360))/2

        list_ang.append(ang_cal)
          
        i+=1        
#    print(list_ang)
    return list_ang

#-------------------------------------------------------------------------------
def ExtractDEMByCentroid(pLayer):
    print('สกัดค่า DEM....')
    pLayer.startEditing()
    for f in pLayer.getFeatures():
        #สร้างจุดจาก centroid ของรูปปิด    
        pts = f.geometry().centroid().asPoint() #get ค่าพิกัด centroid ของกริดแล้วสร้างให้เป็นจุด
        
        #นำค่าจุดมาสกัดความสูง DEM
        val, res = rlayer.dataProvider().sample(QgsPointXY(pts[0],pts[1]), 1) #val คือค่า dem ที่รีเทิร์นกลับมาจากการสกัดด้วยจุด sample    
        
        #อัพเดทเฉพาะค่า DEM ในไฟล์ pLayer
        pLayer.changeAttributeValue(f.id(),6,val)

    pLayer.commitChanges()    
    print('เสร็จสิ้นการสกัดค่า DEM....')
#-------------------------------------------------------------------------------
def CalBeamBlock(pLayer):
    print('คำนวนการบดบังของบีมจากภูมิประเทศ...')
    pLayer.startEditing()
    
    #ลูปแต่ละมุมเพื่อหาการบดบังของลำบีม
    i=0
    for az in values:
        #กรองฟีเจอร์ด้วยมุม
        pLayer.selectByExpression('"radialAng" = {}'.format(az))
       
        #ลูปฟีเจอร์ตามมุมที่ได้กรองไว้เพื่อหาลำบีมที่ถูกบดบัง
        for k,f in enumerate(pLayer.selectedFeatures()):
            #print('ลำดับ',k)
            if f['heightASL']<=f['DEM_ASL']:
                dis_block=f['horizonDis']
                i+=1                            
                #กรองฟีเจอร์ด้วยมุมและระยะทางที่พบว่าถูกภูมิประเทศบดบัง
                pLayer.selectByExpression('"radialAng" = {} AND "horizonDis">= {}'.format(az,dis_block))
                for fb in pLayer.selectedFeatures():
                    pLayer.changeAttributeValue(fb.id(),7,1) #ลำบีมช่วงที่ถูกบดบังโดยภูมิประเทศ
                
                break #เมื่ออัพเดทคอลัมน์เสร็จให้ออกลูปใหญ่ เพื่อคำนวนมุมถัดไป
    pLayer.commitChanges()     

    print('จำนวนมุมทั้งหมดที่ถูกภูมิประเทศบดบัง:',i)
    print('เสร็จสิ้นการคำนวนการบดบังของบีมจากภูมิประเทศ...')
#-------------------------------------------------------------------------------
def updateColumnBeamBlock(pLayer):
    print('อัพเดทคอลัมน์ BeamBlock สำหรับบีมที่ไม่ถูกบดบัง...')
    pLayer.startEditing()
    for az in values:
        #กรองฟีเจอร์ด้วยมุม
        pLayer.selectByExpression('"radialAng" = {}'.format(az))
          
        #ลูปฟีเจอร์ตามมุมที่ได้กรองไว้เพื่อหาลำบีมที่ถูกบดบัง
        for k,f in enumerate(pLayer.selectedFeatures()):
            if f['BeamBlock'] == NULL:
                pLayer.changeAttributeValue(f.id(),7,0) #ลำบีมช่วงที่ไม่ถูกบดบังโดยภูมิประเทศ
    pLayer.commitChanges()         
    print('เสร็จสิ้นการอัพเดทคอลัมน์ BeamBlock สำหรับบีมที่ไม่ถูกบดบัง...')
#-------------------------------------------------------------------------------
#1.แปลงพิกัดสถานีพิษณุโลกจาก geo เป็น utm
#geom = QgsGeometry(QgsPoint(100.2174233,16.7755399)) # นำพิกัดสถานีมาจากกุเกิ้ล
geom = QgsGeometry(QgsPoint(100.2179637,16.7754090)) # นำพิกัดสถานีมาจากประมาณจุดกลางของเรดาร์ shapefile
sourceCrs = QgsCoordinateReferenceSystem(4326)
destCrs = QgsCoordinateReferenceSystem(32647)
tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
geom.transform(tr)

epsg=32647
uri = "Point?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
ptLayer = QgsVectorLayer(uri, 'sta_rad_PHS', 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
pr_pt = ptLayer.dataProvider()
pt_rd=QgsFeature()
pt_rd.setGeometry(QgsGeometry.fromPointXY(geom.asPoint()))
pr_pt.addFeatures([pt_rd])
ptLayer.updateExtents() 

#-------------------------------------------------------------------------------
#2.สร้างชั้นรูปปิดใน memory
uri = "Polygon?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
pLayer = QgsVectorLayer(uri, 'poly_beamblock', 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
pr = pLayer.dataProvider() #เก็บค่า dataProvider ของชั้นข้อมูลรูปปิด
#poly = QgsFeature() #สร้าง instance ของ feature ที่จะใช้สร้างรูปปิดแต่ละชิ้น
#-add field to mem_layer to provide for feats.fields data
pr.addAttributes([QgsField("elevAngle", QVariant.Double,'double', 10, 3),
                     QgsField("radialAng", QVariant.Double,'double', 10, 3),
                     QgsField("horizonDis", QVariant.Double,'double', 10, 3),
                     QgsField("size", QVariant.Double,'double', 10, 3),
                     QgsField("heightASL", QVariant.Double,'double', 10, 3),
                     QgsField("DEM_ASL", QVariant.Double,'double', 10, 3),
                     QgsField("BeamBlock", QVariant.Int,len=5)])#1=block,0=Unblock

pLayer.updateFields() #update attribute
#-------------------------------------------------------------------------------
#3.ตั้งค่าพารามิเตอร์เพื่อสร้างรูปปิด
#พิกัดสถานีเรดาร์
pt_rd=geom.asPoint()

#รัศมีเรดาร์
#dist=240.0 #กิโลเมตร
dist=237.0 #กิโลเมตร

beamWidth=1.0 #องศา

#มุมที่ต้องการ
#az=270.0 
#azimuth=CalcGeographicAngle(az)#แปลงเป็นมุมอซิมัท

#จำนวนอซิมัท
numRange=360 #องศา

#ขนาดความละเอียดของการตรวจวัด
binSize=1000.0

if binSize == 1000:
#รัศมีเรดาร์
#dist=240.0 #กิโลเมตร
    dist=237.0 #กิโลเมตร
else:
    dist=237.0*(1000/binSize) #กิโลเมตร

#มุมยก
elevAng=0.5 #องศา

#ค่าพารามิเตอร์สำหรับคำนวนความสูงของลำบีมจากระดับน้ำทะเลปานกลาง
h_rd=30.0 #-ความสูงของหอคอยเรดาร์ของกรมอุตุนิยมวิทยา (เมตร)
rad_alt=47  # ความสูงสถานีจากระดับน้ำทะเลปานกลาง (เมตร)
#-------------------------------------------------------------------------------
#4.หามุมตามเรดาร์ต้นฉบับ ตรงนี้ที่แตกต่างจากไฟล์ "060"
path_to_rad_layer = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/rad_phs_utm201908041300.shp"
ppLayer = QgsVectorLayer(path_to_rad_layer, "rad_phs_utm201908041300", "ogr") #ค่าพิกัดชั้นข้อมูลที่จะใช้WGS84

values=findUniqueAngle(ppLayer)
#-------------------------------------------------------------------------------
#5.สร้างชิ้นรูปปิดเรดาร์ตามแนวมุมอซิมัทที่กำหนด
createPolyRadAlongAzimuth(numRange,dist,binSize,elevAng,pt_rd,pLayer,pr,h_rd,rad_alt)

#-------------------------------------------------------------------------------
#6.สกัดความสูง DEM เพื่อนำค่ามาใส่ในคอลัมน์ pLayer
path_to_DEM = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/DEM_for_PHS_radar.tif"
rlayer = QgsRasterLayer(path_to_DEM, "DEM_PHS")

#สกัดความสูง
ExtractDEMByCentroid(pLayer)
#-------------------------------------------------------------------------------
#7.คำนวน beamblock
CalBeamBlock(pLayer)
#-------------------------------------------------------------------------------
#8.อัพเดทคอลัมน์ BeamBlock สำหรับบีมที่ไม่ถูกบดบัง
updateColumnBeamBlock(pLayer)
#-------------------------------------------------------------------------------
#9.ส่งออกผลการคำนวน beamblock ในรูป shapefile polygon
path_to_rad_layer = "D:/tmp/PyQGIS/Plugin_practice/1data/BeamBlockPhitsanulokRadar.shp"
QgsVectorFileWriter.writeAsVectorFormat(pLayer,path_to_rad_layer,'utf-8',driverName='ESRI Shapefile')

#-------------------------------------------------------------------------------
#10.rasterize beamblock เพื่อส่งออกเป็นราสเตอร์ 
outp = "D:/tmp/PyQGIS/Plugin_practice/1data/BeamBlockPhitsanulokRadarRaster.tif"
processing.run("gdal:rasterize", 
{'INPUT':pLayer,'FIELD':'BeamBlock',
'BURN':0,
'UNITS':0,
'WIDTH':500,
'HEIGHT':500,
'EXTENT':'392807.3827114203,866803.0786619843,1618109.471501457,2092107.6119104286 [EPSG:32647]',
'NODATA':0,'OPTIONS':'',
'DATA_TYPE':5,
'INIT':None,
'INVERT':False,
'EXTRA':'',
'OUTPUT':outp})

#-------------------------------------------------------------------------------
#11.แสดงผลในแผนที่
QgsProject.instance().addMapLayers([pLayer])
QgsProject.instance().addMapLayers([ptLayer])

#-------------------------------------------------------------------------------
print('จบการคำนวน....................')