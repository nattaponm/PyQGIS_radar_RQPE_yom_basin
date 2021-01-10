'''
20200608 โมเสคราย 15นาที บริเวณลุ่มน้ำยม ใช้เรดาร์เชียงรายและพิษณุโลก
ใช้โค้ด "089"

ต่อไปจะทำการสร้างฝนสะสมราย 1 ชั่วโมง ต้องลองสร้างจากไฟล์ "087" ให้มีการเลือกช่วงเวลาของฝนสะสมที่ต้องการ

'''
import numpy as np
from scipy.stats import linregress
import os
import datetime
import fnmatch

#-------------------------------------------------------------------------------
def copyRad(pLayer,phLayer,pr_phs):    
    print('คัดลอกเรดาร์.....')
    i=0
    for f in pLayer.getFeatures():
        poly = QgsFeature()
        #สร้างชิ้นรูปปิดกริดจากชุดข้อมูลจุดด้านบน ดูค่าตัวแปร poly ด้านบน
        poly.setGeometry(f.geometry())
        #-update feature
        poly.setAttributes([i,f['value'],f['radialAng'],f['heightASL']])
        pr_phs.addFeatures([poly]) #อัพเดทค่ารูปปิดชิ้นที่กำลังทำงานผ่าน dataProvider หรือ pr
        phLayer.updateExtents() #อัพเดท map
        i+=1
    return phLayer
#-------------------------------------------------------------------------------
def radarFlareDetectionRound1(phLayer,PC_BinWithVal,Corr,dist):
    #ตกลงโค้ดฟังค์ชั่นนี้ไม่ได้ใช้ spatial index นะ
    print('ค้นหา radar flare ตามมุม รอบที่ 1.....')
    #หาค่ามุมทั้งหมดของเรดาร์
    idx = phLayer.fields().indexOf('radialAng')
    values = phLayer.uniqueValues(idx)

    #สร้าง spatial index ให้ฟีเจอร์เพื่อเพิ่มความเร็วในการประมวลผล
    all_features = {}
    index = QgsSpatialIndex() # Spatial index
    for ft in phLayer.getFeatures():
        index.insertFeature(ft)
        all_features[ft.id()] = ft

#    phLayer.startEditing()
    i=0
    
    #ลูปทีละมุมเพื่อคำนวนค่าสถิติ
    flare_ang=[]#ลิสเพื่อเก็บมุมที่เป็น flare
    for ang in values:
#        if i<10:print('angle:',ang)
        #อ่านเพิ่ม selectByExpression https://gis.stackexchange.com/questions/340961/pyqgis-using-variable-instead-of-number-in-selectbyexpression-query
        #อ่านเพิ่ม https://docs.qgis.org/testing/pdf/en/QGIS-testing-PyQGISDeveloperCookbook-en.pdf
        #    req = QgsFeatureRequest().setFilterExpression(' "radialAng" == "ang" ') #ไม่ใช้แบบนี้

        phLayer.selectByExpression('"radialAng" = {}'.format(ang))
        inds=phLayer.selectedFeatureIds()
        
        #ลูปเพื่อคำนวนค่าสถิติของแต่ละมุม ด้วยการใช้ spatialIndex ที่ทำไว้ก่อนหน้านี้
        val_list=[]
        
        #เก็บค่าการสะท้อนของมุมที่ถูกเลือกด้วยการลูปทุกฟีเจอร์ในมุมนั้นๆด้วย spatial index
        for id in inds:
            val_list.append((id,all_features[id]['value']))
        
        dv=np.array(val_list) #แปลงเป็นอาเรย์
        slope, intercept, r_value, p_value, std_err = linregress(dv[:,0], dv[:,1])
        ct=len(inds)
        
        #อัพเดทคอลัมน์ด้วยการฟีเจอร์ของลูปมุมที่เลือกด้วย spatial index
        j=0
        for k,f in enumerate(phLayer.selectedFeatures()):              
            if ((ct/dist)*100.0)>=PC_BinWithVal and r_value>=Corr : 
                #ตรงนี้แตกต่างจาก "082" เพราะอัพเดทค่า -999.0 ลงไปเมื่อเจอ flare ในรอบที่ 1 เลย
                attrs={1:-999.0,4:k,5:ct,6:(ct/dist)*100.0,7:str(slope),8:str(r_value),9:1}
                phLayer.dataProvider().changeAttributeValues({f.id():attrs})#1=flare
                if j==0:flare_ang.append(ang) #เก็บค่ามุมที่เป็น flare สำหรับฟีเจอร์แรกที่พบ                    

            else:
                attrs={4:k,5:ct,6:(ct/dist)*100.0,7:str(slope),8:str(r_value),9:0}
                phLayer.dataProvider().changeAttributeValues({f.id():attrs})#0=ok   
            
            j+=1

#    phLayer.commitChanges()
    return phLayer,flare_ang,values
#-------------------------------------------------------------------------------
#refine เพื่อหา radar flare ขนาดใหญ่ที่ยังตกค้างจากการหารอบแรก 
#ในรอบนี้จะใช้ "PC_BinWithVal">=0.80 และ"Corr">=0.5 และต้องเป็นมุมที่อยู่ข้าง Flare=1 ที่หาในรอบแรกไปแล้ว
#ค่า "Corr">=0.5 นี้เป็นตามสมมติฐานที่ว่าความสัมพันธ์แบบ linear ไม่เหมาะสมกับ flare ทำให้ค่า corr ต่ำ
#แม้ว่าค่า "Corr">=0.5 จะต่ำ แต่ก็ยังแสดงให้เห็นว่ามีความสัมพันธ์ การใช้ nonlinear จะทำให้พบความสัมพันธ์
#ที่อาจจะให้ค่า R2 ที่สูงก็ตาม แต่จะทำให้การคำนวนใช้เวลาเพิ่มไปอีก จะทำให้ไม่เหมาะกับการใช้งานจริงของ TMD
#นิสิตอาจลองใช้ nonlinear เก็บ radar flare ในรอบ refine นี้ก็ได้ ลองใช้ y=x^2 ก่อน
def radarFlareDetectionRound2(phLayer,PC_BinWithVal,Corr,flare_ang,values):
    print('ค้นหา radar flare ตามมุม รอบที่ 2.....')
    phLayer.startEditing()
     
    #แปลงมุมทั้งหมดเป็นอาเรย์
    ang_arr=np.array(values)   
    
    #สร้างลิสหามุมข้างเคียงของ Flare ในรอบแรก
    flare_list=[] 
    for ang in flare_ang:
        w_check=ang in ang_arr
        if w_check==False: continue #ตรวจมุมที่กำลังลูปนี้ถ้าไม่ใช้ flare ให้วนไป        
        id=np.where(ang_arr==ang) #หาอินเด็กมุม flare ของมุมทั้งหมดที่มี
        id=id[0]
        #กรณีที่ flare ไม่ได้เป็นมุมแรกและมุมสุดท้าย        
        if id>0 and id<(len(values)-1):
            pre_id=id-1 #อินเด็กซ์ก่อน flare
            pot_id=id+1 #อินเด็กหลัง flare
            flare_list.append(ang_arr[pre_id])
            flare_list.append(ang_arr[pot_id])
        
        #กรณีที่มุมของ flare เป็นมุมแรกของ sweep
        if id==0: flare_list.append(ang_arr[id+1]) #ให้อินเด็กซ์เป็น +1
        
        #กรณีที่มุมของ flare เป็นมุมสุดท้ายของ sweep ให้อินเด็กซ์เป็น -1
        if id==len(values)-1: flare_list.append(ang_arr[id-1])
    
    #flare_list คือ ลิสของมุมที่คาดว่าน่าจะเป็น flare ที่ตกค้างจากการใช้ linear regression ในรอบแรก
    #โดยเป็น range ที่อยู่ข้างๆกับ flare ในรอบแรก ซึ่งจะไปกรองอีกสองค่าดังลูปด้านล่าง
    
    #ลูปเพื่ออัพเดท flare รอบ 2
    for ang in set(flare_list): #ใช้ set เพราะจะเอามุมที่เป็น unique จริงๆ
        #https://gis.stackexchange.com/questions/315601/getting-particular-feature-using-expression-in-pyqgis
        #https://docs.qgis.org/testing/pdf/en/QGIS-testing-PyQGISDeveloperCookbook-en.pdf
        #ตรงส่วนนี้ที่ปรับปรุงเพิ่มจากไฟล์ "082" เพื่อเก็บตก flare จากรอบแรก
        phLayer.selectByExpression('"radialAng" = {} AND "Flare1" != {} AND "PC_BinWithVal">= {} AND "Corr">={}'.format(ang,1,PC_BinWithVal,Corr))
        
        for f in phLayer.selectedFeatures():
            phLayer.changeAttributeValue(f.id(),10,2)#2=flare ที่ตกค้างมาจากรอบแรก "flare2"
            phLayer.changeAttributeValue(f.id(),9,2)#2=flare ที่ตกค้างมาจากรอบแรก "flare1"
            phLayer.changeAttributeValue(f.id(),1,-999.00) #เปลี่ยนแนวคิดใหม่ ให้แทนที่ค่า dbZ คอลัมน์ "value" เลย แล้วจะใช้แทน valueFlare 
    
    phLayer.commitChanges()
    return phLayer
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
    phLayer.selectByExpression('"value" = {}'.format(-999.0))
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
            #ตรงนี้ต้องใช้ QgsSpatialIndex จะทำให้การ intersects เร็วขึ้นมาก
            for ba in val_list: #ตรงนี้จะช้ามาก เพราะต้องลูปทุกฟีเจอร์ในทั้งสองมุม
                phLayer.selectByExpression('"radialAng" = {}'.format(ba)) #ใช้ซ้ำกับลูปบนได้หรือไม่
                for kk,fa in enumerate(phLayer.selectedFeatures()):
                    if fa.geometry().intersects(poly.geometry()): #spatial intersect การกรองครั้งแรก
                        pt_fa=fa.geometry().centroid().asPoint()
                                
                        #หาระยะทางของ fa รอบๆ กับจุดศก.เรดาร์ที่มี flare กรองครั้งที่สอง
                        dist = QgsDistanceArea()
                        dt = distance.measureLine(pt_f, pt_fa) #ระยะทางของจุด f กับ fa์ (m)
                        if dt<rem and fa['value']>-999:
                                
                            #-เพิ่มค่าระยะ่ทางที่คำนวนได้ กับค่าการสะท้อน(value)ของ fa เข้าไปในลิส
                            dist_val.append((dt,fa['value']))
            
                            #ถ้าระยะทางมากกว่า 0 แต่ยังอยู่ในรัศมีให้ถ่วงน้ำหนักตามระยะทางแล้วนำไปเก็บใน list ของค่าถ่วงน้ำหนัก
                            if dt>0:    
                                w=1/dt
                                w_list.append(w)
                            else:
                                w_list.append(0)                     
            
            if len(dist_val)==0:continue #ถ้าไม่มีจุดตกในรัศมี effective radius ของ pt_f เลย ให้วน
            
            w_check=0 in w_list
            dv=np.array(dist_val) #แปลงเป็นอาเรย์
            if w_check==True:
                idx=w_list.index(0) #หาตำแหน่งในลิสว่าตรงไหนที่มีค่าน้ำหนักเป็น 0
                z_idw=dv[idx,1] ##กำหนดให้ใช้ค่าที่ตรงกับพิกัดของกริดเล็กนั้นเลย โดยไม่สนใจว่าจะมีค่าอื่นที่อยู่ในรัศมีนั้นหรือไม่
                phLayer.changeAttributeValue(f.id(),1,float(z_idw)) #1 หมายความว่าแทนแทนค่า dbz ใน value เลย แตกต่างกับ 082
            else:
                wt=np.transpose(w_list)
                z_idw=np.dot(dv[:,1],wt)/sum(w_list) # ใช้ dot product เพื่อคำนวนหาค่าdbzด้วยวิธีการ idw จะได้ค่าเดียว
                # อ่านเพิ่ม https://www.guru99.com/numpy-dot-product.html
                phLayer.changeAttributeValue(f.id(),1,float(z_idw)) #1 หมายความว่าแทนแทนค่า dbz ใน value เลย แตกต่างกับ 082

    phLayer.commitChanges()

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
            phLayer.changeAttributeValue(f.id(),11,0)
        else:
            phLayer.changeAttributeValue(f.id(),11,val)


    phLayer.commitChanges()    
    print('เสร็จสิ้นการสกัดค่า BeamBlock....')        
    return phLayer
#-------------------------------------------------------------------------------
#อัพเดทคอลัมน์ RQI โดย 0=bin is clear,1=Flare,2=Beamblock,3=Flare+Beamblock
def updateRQI(phLayer):
    print('กำลังอัพเดทคอลัมน์ RQI...')
    phLayer.startEditing()
    #for az in values:
    phLayer.selectByExpression('"Flare1" = {} AND "BeamBlock" = {}'.format(0,0))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),12,0)

    phLayer.selectByExpression('"Flare1" = {} AND "BeamBlock" = {}'.format(0,1))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),12,2)

    phLayer.selectByExpression('"Flare1" >= {} AND "BeamBlock" = {}'.format(1,0))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),12,1)

    phLayer.selectByExpression('"Flare1" >= {} AND "BeamBlock" = {}'.format(1,1))
    for f in phLayer.selectedFeatures():
        phLayer.changeAttributeValue(f.id(),12,3)

    phLayer.commitChanges() 
    print('เสร็จสิ้นการอัพเดทคอลัมน์ RQI...')
    return phLayer

#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------
#ฟังค์ชั่นด้านล่างเป็นของการโมเสค
def calParaGrid(xmin,xmax,ymin,ymax,ds_s):
    print('คำนวนพารามิเตอร์เพื่อการโมเสค.....')
    #-คำนวนจำนวนกริดที่ต้องใช้ในแนวแถวและหลัก
    numCols=int((xmax-(xmin-(xmin//ds_s)))//ds_s)+1 #จำนวนกริดในแนวหลัก  // คือการหารเอาเศษ, +1 คือต้องการให้คลุมเศษตัวเลข
#    print('จำนวนกริดในแนวหลัก:',numCols)
    numRows=int((ymax-(ymin-(ymin//ds_s)))//ds_s)+1 #จำนวนกริดในแนวแถว
#    print('จำนวนกริดในแนวแถว:',numRows)

    #-กำหนดค่าพิกัดมุมซ้ายล่าง
    llx=xmin-(xmin//ds_s)
    lly=ymin-(ymin//ds_s)

    #-set dimension first polygon at lower left
    ll,ul,ur,lr=[llx,lly],[llx,lly+(ds_s*2)],\
                [llx+(ds_s*2),lly+(ds_s*2)],[llx+(ds_s*2),ds_s]

    return numCols,numRows,llx,lly,ll,ul,ur,lr
    print('เสร็จสิ้นคำนวนพารามิเตอร์เพื่อการโมเสค.....')
#-------------------------------------------------------------------------------
def createGrid(numCols,numRows,llx,lly,ll,ul,ur,lr,ds_s,pLayer,poly,pr,gridVal):
    print('ทำการสร้างกริดผลลัพธ์การโมเสค.....')
    i=0
    for r in range(numRows):
        for c in range(numCols):
            #ตั้งค่าพิกัดของแต่ละมุมของรูปปิด
            ll[0],ll[1] = llx+(c*ds_s),lly+(r*ds_s)
            lr[0],lr[1] = ll[0]+ds_s, ll[1]
            ur[0],ur[1] = lr[0],lr[1]+ds_s
            ul[0],ul[1] = ll[0],ur[1]
            
            #สร้าง list ของจุด หรือชุดข้อมูลจุดเพื่อนำไปสร้างเป็นรูปปิดกริดเล็ก
            points = [QgsPointXY(ll[0],ll[1]),QgsPointXY(ul[0],ul[1]),\
                QgsPointXY(ur[0],ur[1]),QgsPointXY(lr[0],lr[1])]         
                   
            #สร้างชิ้นรูปปิดกริดจากชุดข้อมูลจุดด้านบน ดูค่าตัวแปร poly ด้านบน
            poly.setGeometry(QgsGeometry.fromPolygonXY([points]))
            
            #-calculate area and perimeter from geometry
            #-คำนวนค่าเรขาคณิตของรูปปิดกริดได้แก่พื้นที่และความยาวเส้นรอบรูป
            area=(poly.geometry().area())/1000/1000
            peri=poly.geometry().length() 

            #อัพเดทค่าฟิวด์ของฟีเจอร์ที่กำลังคำนวน
            poly.setAttributes([i,area,peri,gridVal])
            
            pr.addFeatures([poly]) #อัพเดทค่ารูปปิดชิ้นที่กำลังทำงานผ่าน dataProvider หรือ pr
               
            pLayer.updateExtents() #อัพเดท map
                    
            i+=1        

    print('เสร็จสิ้นการสร้างกริดผลลัพธ์.....')
    return pLayer
#-------------------------------------------------------------------------------
def clipRadarByProvince(pLayer,prLayer,pcLayer,pr):
    #ปรับปรุงโค้ดใหม่ส่วนนี้ทำให้ใช้เวลาไม่ถึงนาที คัดมาจากไฟล์ "075"
    #pLayer=ข้อมูลเรดาร์ที่จะตัด, prLayer=ขอบเขตจังหวัดแพร่
    #pcLayer=shapefileเพื่อเก็บเรดาร์ที่จะตัดตามขอบเขตแพร่
    #pr=dataProvider ของpcLayer
        
    #สร้างรูปปิดขอบเขตจังหวัดแพร่ตาม extent เพื่อนำไปquery กรองเรดาร์ดิบ
    poly_p=QgsFeature()
    offset=2000
    ext = prLayer.extent()
    (xmin, xmax, ymin, ymax) = (ext.xMinimum()-offset, ext.xMaximum()+offset,\
                                    ext.yMinimum()-offset, ext.yMaximum()+offset)
    
    #สร้าง list ของจุด หรือชุดข้อมูลจุดเพื่อนำไปสร้างเป็นรูปปิด
    points = [QgsPointXY(xmin,ymin),QgsPointXY(xmin,ymax),\
              QgsPointXY(xmax,ymax),QgsPointXY(xmax,ymin)]    
    
    #สร้างชิ้นรูปปิดขอบเขตพื้นที่ศึกษาจากชุดข้อมูลจุดด้านบน 
    poly_p.setGeometry(QgsGeometry.fromPolygonXY([points]))

    #ลูปเรดาร์เพื่อ intersect ผล spatial index กับ ขอบเขต extent
    inBound = poly_p.geometry().boundingBox()    
    i=0
    for ft in pLayer.getFeatures():
        if ft.geometry().intersects(inBound):            
            poly_cri = QgsFeature()  #เพิ่มตรงนี้
            #สร้างชิ้นรูปปิดกริดจากชุดข้อมูลจุดด้านบน ดูค่าตัวแปร poly ด้านบน
            poly_cri.setGeometry(ft.geometry())
            #-update feature
            poly_cri.setAttributes([i,ft['value'],ft['heightASL']])
            pr.addFeatures([poly_cri]) #อัพเดทค่ารูปปิดชิ้นที่กำลังทำงานผ่าน dataProvider หรือ pr
            pcLayer.updateExtents() #อัพเดท map
            i+=1

    return pcLayer

#-------------------------------------------------------------------------------
#-คำนวนจุด centroid ของกริด C ที่ตกในพื้นที่กริด A หรือ B เพื่ออัพเดทค่าฟิวด์มาสู่กริด C
def updateFieldOutputByIntersectCentroid(paLayer,pbLayer,pcLayer,rd):
    print('กำลังคำนวนการอัพเดทค่าฟิวด์ในกริด C ด้วยวิธี spatial intersection.........')
    i=0 

    #อ่านวิธีการใช้ spatial index เพื่อการเข้าถึงฟีเจอร์ที่ไวขึ้น
    #https://gis.stackexchange.com/revisions/224954/4
    pcLayer.startEditing() #ตั้งค่าให้เริ่มการแก้ไขชั้นขัอมูล C
    
    all_featuresA = {}
    indexA = QgsSpatialIndex() # Spatial index
    for ft in paLayer.getFeatures():
        indexA.insertFeature(ft)
        all_featuresA[ft.id()] = ft
    
    all_featuresB = {}
    indexB = QgsSpatialIndex() # Spatial index
    for ft in pbLayer.getFeatures():
        indexB.insertFeature(ft)
        all_featuresB[ft.id()] = ft    
    
    #loopเพื่อคำนวนกริดผลลัพธ์ของ idw 
    for feat in pcLayer.getFeatures():
        inGeom = feat.geometry()
        idsListA = indexA.intersects(inGeom.boundingBox())
        idsListB = indexB.intersects(inGeom.boundingBox())
        
        pt_c=feat.geometry().centroid().asPoint()
        
        #สร้างลิสเปล่าเก็บระยะทางและค่า dbz
        dist_val=[]
        
        #สร้างลิสถ่วงค่าน้ำหนักตามระยะทางที่ห่างออกไป
        w_list=[]
        
        #loop idsListA เพื่อหาจุดที่อยู่ในแนวรัศมีในการทำ idw ค่า dbz
        for id in idsListA:
            pt_a = all_featuresA[id].geometry().centroid().asPoint()
            distance = QgsDistanceArea()
            d = distance.measureLine(pt_c, pt_a) #ระยะทางของจุด C กับ จุดA            
            
            if d>rd: continue
            
            if all_featuresA[id]['value']>0 and all_featuresA[id]['heightASL']<5000:
                #-เพิ่มค่าระยะ่ทางที่คำนวนได้ กับค่าการสะท้อน(value)ของ B เข้าไปในลิส
                dist_val.append((d,all_featuresA[id]['value']))
                        
                #ถ้าระยะทางมากกว่า 0 แต่ยังอยู่ในรัศมีให้ถ่วงน้ำหนักตามระยะทางแล้วนำไปเก็บใน list ของค่าถ่วงน้ำหนัก
                if d>0:    
                    w=1/d
                    w_list.append(w)
                else:
                    w_list.append(0)  
                    

        #loop idsListB เพื่อหาจุดที่อยู่ในแนวรัศมีในการทำ idw ค่า dbz
        for id in idsListB:
            pt_b = all_featuresB[id].geometry().centroid().asPoint()
            
            #ทำเป็นฟังค์ชั่นได้
            distance = QgsDistanceArea()
            d = distance.measureLine(pt_c, pt_b) #ระยะทางของจุด C กับ จุดA            
            
            if d>rd: continue
            
            if all_featuresB[id]['value']>0 and all_featuresB[id]['heightASL']<5000:
                #-เพิ่มค่าระยะ่ทางที่คำนวนได้ กับค่าการสะท้อน(value)ของ B เข้าไปในลิส
                dist_val.append((d,all_featuresB[id]['value']))
                        
                #ถ้าระยะทางมากกว่า 0 แต่ยังอยู่ในรัศมีให้ถ่วงน้ำหนักตามระยะทางแล้วนำไปเก็บใน list ของค่าถ่วงน้ำหนัก
                if d>0:    
                    w=1/d
                    w_list.append(w)
                else:
                    w_list.append(0)  

        if len(w_list)==0:continue #ถ้าไม่มีจุดตกในกริด C เลยให้กลับไปวนใหม่        
        
        #อัพเดทค่าที่ได้จากการประมาณค่าในคอลัมน์
        w_check=0 in w_list
        dv=np.array(dist_val) #แปลงเป็นอาเรย์
        if w_check==True:
            idx=w_list.index(0) #หาตำแหน่งในลิสว่าตรงไหนที่มีค่าน้ำหนักเป็น 0
            z_idw=dv[idx,1] ##กำหนดให้ใช้ค่าฝนที่วัดได้จากสถานีที่ตรงกับพิกัดของกริดเล็กนั้นเลย โดยไม่สนใจว่าจะมีฝนที่วัดได้จากสถานีอื่นที่อยู่ในรัศมีนั้นอีกกี่จุดก็ตาม
            pcLayer.changeAttributeValue(feat.id(),3,str(z_idw)) 
            pcLayer.changeAttributeValue(feat.id(),4,len(dist_val))
        else:
            wt=np.transpose(w_list)
            z_idw=np.dot(dv[:,1],wt)/sum(w_list) # ใช้ dot product เพื่อคำนวนหาค่าฝนด้วยวิธีการ idw จะได้ค่าเดียว
            # อ่านเพิ่ม https://www.guru99.com/numpy-dot-product.html
            pcLayer.changeAttributeValue(feat.id(),3,str(z_idw)) 
            pcLayer.changeAttributeValue(feat.id(),4,len(dist_val))

    pcLayer.commitChanges() #ตั้งค่าให้หยุดการแก้ไขชั้นขัอมูล C
    print('เสร็จสิ้นการอัพเดทค่าฟิวด์ในกริดผลลัพธ์.........')
    return pcLayer
    
#-------------------------------------------------------------------------------
def Timing_start(): 
    stt=datetime.datetime.now()
    print('*'*50)
    print ("started: {0}".format(datetime.datetime.now()))
    return stt
    
def Timing_used(stt):  
    stp=datetime.datetime.now()
    print ("finished: {0}".format(datetime.datetime.now()))
    delTime=stp-stt
    print('ใช้เวลาวินาที:',delTime.seconds)
    print('*'*50)
    print('')
#-------------------------------------------------------------------------------
def run_main_flare_beamBlock(pLayer,rad_name,epsg,binSize,path_beamblock):
    #ฟังค์ชั่นเรียกใช้กระบวนการทั้งหมดของการตรวจหา radar flare และ beamblock
    #1.เริ่มกระบวนการหา radar flare นำมาจากไฟล์ "070" 
    print('>>>>>หา radar flare และ beamblock ประมาณค่าข้างเคียงด้วย idw....')
    
    #-------------------------------------------------------------------------------
    #1.1.อ่านshapefile ข้อมูลดิบเรดาร์เชียงราย
#    path_rad = "D:/tmp/PyQGIS/Plugin_practice/1data/rad_cri_utm201908041300.shp"
#    pLayer = QgsVectorLayer(path_rad, "Rad_"+rad_name, "ogr") #ค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
    
    #-------------------------------------------------------------------------------
    #1.2.สร้างโดยคัดลอกข้อมูล 1.1 บางคอลัมน์ที่จะนำมาคำนวน    
#    epsg = 32647 #กำหนดค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
    uri = "Polygon?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
    opLayer = QgsVectorLayer(uri, 'rad_final_'+rad_name, 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
    pr = opLayer.dataProvider() #เก็บค่า dataProvider ของชั้นข้อมูลรูปปิด

    #-เพิ่มหัวตารางโดยเก็บค่าบางคอลัมน์จากไฟล์ต้นฉบับบางส่วนและเพิ่มคอลัมน์ที่จะคำนวนสถิติเพื่อขจัด radar flare
    pr.addAttributes([QgsField("value", QVariant.Double,'double', 10, 3),
                    QgsField("radialAng", QVariant.Double,'double', 10, 3),
                    QgsField("heightASL", QVariant.Double,'double', 10, 3),
                    QgsField("ID", QVariant.Int,len=3),
                    QgsField("numBinWithVal", QVariant.Double,'double', 10, 3),
                    QgsField("PC_BinWithVal", QVariant.Double,'double', 10, 3),
                    QgsField("Slope", QVariant.Double,'double', 10, 3),
                    QgsField("Corr", QVariant.Double,'double', 10, 3),
                    QgsField("Flare1", QVariant.Int),
                    QgsField("Flare2", QVariant.Int), 
                    QgsField("BeamBlock", QVariant.Int,len=5),
                    QgsField("RQI", QVariant.Int,len=5)])
    opLayer.updateFields() #update attribute
    #-------------------------------------------------------------------------------
    #1.3ขนาดความละเอียดของการตรวจวัดของเชียงราย ตรงนี้เพิ่มมาจาก 071
    if binSize == 1000:
    #รัศมีเรดาร์
    #dist=240.0 #กิโลเมตร
        dist=237.0 #กิโลเมตร
    else:
        dist=237.0*(1000/binSize) #กิโลเมตร        
       
    #-------------------------------------------------------------------------------
    #1.4คัดลอกเรดาร์
    stt=Timing_start()    
    opLayer=copyRad(pLayer,opLayer,pr)
    print('copyRad(pLayer,opLayer,pr)....'+rad_name)
    Timing_used(stt)    
    
    #-------------------------------------------------------------------------------
    #1.5ตรวจวัดRadar flare รอบที่ 1
    PC_BinWithVal=85.0
    Corr=0.85
    
    stt=Timing_start()
    opLayer,flare_ang,values=radarFlareDetectionRound1(opLayer,PC_BinWithVal,Corr,dist)
   
    
    print('radarFlareDetectionRound1(opLayer,PC_BinWithVal,Corr,dist)....'+rad_name)
    Timing_used(stt)
    
    #-------------------------------------------------------------------------------
    #1.6ตรวจวัดRadar flare รอบที่ 2
    PC_BinWithVal=80.0
    Corr=0.50
    
    stt=Timing_start()
    opLayer=radarFlareDetectionRound2(opLayer,PC_BinWithVal,Corr,flare_ang,values)
    print('radarFlareDetectionRound2(opLayer,PC_BinWithVal,Corr,flare_ang,values)....'+rad_name)
    Timing_used(stt)

    #-------------------------------------------------------------------------------
    #1.7การนำค่ากริดรอบๆของ flare มาประมาณค่าด้วย idw เพื่อเติมค่า วิธีนี้ต้องใช้รัศมีตาม effective radius
    #tan(theta/2)=size/(2*dist) โดยที่ size คือด้านที่ต้องการหา ส่วน dist คือ ระยะของกริดนั้นๆกับสถานี
    #โดยที่ theta คือ beamwidth ในที่นี้ให้ทดลอง 1 degree ก่อน ยิ่งไกลค่า size จะใหญ่ขึ้นตามระยะทาง
    #หมายเหตุ: การเติม flare ด้วยการประมาณค่ารอบข้างเข้าไปจะประมวลผลช้ามากคือ มากกว่า 1000 วินาที
    #ดังนั้นเรดาร์ในพืนที่ภาคเหนือไม่แนะนำให้ใช้เนื่องจากมีการบดบังภูมิประเทศเยอะมาก ใช้ได้แต่เพียงพืนที่ราบเช่นพิษณุโลก
    #ส่วนภาคเหนือต้องใช้การวิจัยอีกแบบ ที่จะสร้างภาพเรดาร์โดยใช้มุมยกที่สูงขึ้นไป หรือ psudocappi
#    geom = QgsGeometry(QgsPoint(sta_coord[0],sta_coord[1])) # นำพิกัดสถานีมาจากประมาณจุดกลางของเรดาร์ shapefile
#    sourceCrs = QgsCoordinateReferenceSystem(4326)
#    destCrs = QgsCoordinateReferenceSystem(epsg)
#    tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
#    geom.transform(tr)

#    uri = "Point?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
#    ptLayer = QgsVectorLayer(uri, 'point_rad_CRI', 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
#    pr_pt = ptLayer.dataProvider()
#    pt_rd=QgsFeature()
#    pt_rd.setGeometry(QgsGeometry.fromPointXY(geom.asPoint()))
#    pr_pt.addFeatures([pt_rd])
#    ptLayer.updateExtents()

    #เรียกฟังค์ชั่นประมาณค่า dbz ข้างเคียงกับเรดาร์ flare ให้เข้าไปเติมบริเวณ flare ด้วย IDW
#    stt=Timing_start()
#    interpolateNearFlarebyIDW(phLayer,geom)
#    print(' interpolateNearFlarebyIDW(phLayer,geom)....')
#    Timing_used(stt)
    #-------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------
    #2.เริ่มกระบวนการสกัดค่า beamblock ที่เป็นผลจากไฟล์ "072"
    #2.1เปิดราสเตอร์ผลลัพธ์การคำนวน beamblock 
    rLayer = QgsRasterLayer(path_beamblock , "BeamBlock_"+rad_name)
    #-------------------------------------------------------------------------------
    #2.2สกัดค่า beamblock เข้าสู่เวกเตอร์เรดาร์
    stt=Timing_start()
    opLayer=ExtractBeamBlockByCentroid(opLayer,rLayer)
    print(' ExtractBeamBlockByCentroid(opLayer,rLayer)....'+rad_name)
    Timing_used(stt)
    #-------------------------------------------------------------------------------
    #2.3อัพเดทค่า RQI 
    stt=Timing_start()
    
    opLayer=updateRQI(opLayer)
    
    print(' updateRQI(opLayer)....'+rad_name)
    Timing_used(stt)
    
    print('เสร็จสิ้นการหา radar flare และ beamblock...'+rad_name)
    return opLayer

##-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
################################################################################
def Mosaic_CRI_PHS(Flare_BB_CRI,Flare_BB_PHS,path_to_bound_layer,ds_s,epsg,rad_name1,rad_name2,file_time):
    #มาจากไฟล์ "052"    
    #กำหนดค่าพารามิเตอร์ของกริด C ผลลัพธ์ของการโมเสค
    uri = "Polygon?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
    pcLayer = QgsVectorLayer(uri, file_time, 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
    pr_c = pcLayer.dataProvider() #เก็บค่า dataProvider ของชั้นข้อมูลรูปปิด
    poly_c = QgsFeature() #สร้าง instance ของ feature ที่จะใช้สร้างรูปปิดแต่ละชิ้น
    #-กำหนดหัวฟิวด์
    pr_c.addAttributes([QgsField("Area", QVariant.Double,'double', 10, 3),
                      QgsField("Perimeter", QVariant.Double,'double', 10, 3),
                      QgsField("Val", QVariant.Double,'double', 10, 3),
                      QgsField("NumPtsIntp", QVariant.Int,len=5),
                      QgsField("RainRad", QVariant.Double,'double', 10, 3)])
    pcLayer.updateFields() #update attribute
    #
    ##-------------------------------------------------------------------------------
    ##-offset ตามค่าความยาวด้านของกริด 
    offset=ds_s*1 #จะใช้ค่านี้ในการเผื่อพื้นที่ทั้งกริด A,B,C เพราะเราไม่ควรจะตัดให้พอดีเป๊ะกับพื้นที่ แต่ถ้าไม่เอาก็เปลี่ยน *0
    #-------------------------------------------------------------------------------
    #-ตั้งค่าเวกเตอร์รูปปิดจังหวัดแพร่เพื่อแสดงในแผนที่
    prLayer = QgsVectorLayer(path_to_bound_layer, "Boundary_mosaic", "ogr") #ค่าพิกัดชั้นข้อมูลที่จะใช้WGS84 47n
    ext = prLayer.extent()
    (xmin, xmax, ymin, ymax) = (ext.xMinimum()-offset, ext.xMaximum()+offset,\
                                    ext.yMinimum()-offset, ext.yMaximum()+offset)

#    QgsProject.instance().addMapLayers([prLayer])
    #-------------------------------------------------------------------------------
    #-สร้างกริด C
    #-กำหนดขอบเขตกริดC ผลลัพธ์ของการโมเสค ตามขอบเขตของ extent shapefile จังหวัดแพร่
    numCols,numRows,llx,lly,ll,ul,ur,lr=calParaGrid(xmin, xmax, ymin, ymax,ds_s)
    #-เรียกใช้ฟังค์ชั่นเพื่อสร้างกริดC
    gridVal=-999
    pcLayer=createGrid(numCols,numRows,llx,lly,ll,ul,ur,lr,ds_s,pcLayer,poly_c,pr_c,gridVal)
    #--------------------------------------------------------------------------------
    #-สร้างชั้นข้อมูลเพื่อเก็บเรดาร์ที่ตัดของ CRI
    #epsg = 32647 #กำหนดค่าพิกัดชั้นข้อมูลที่จะใช้WGS84 47N UTM 
    uri = "Polygon?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
    pcriLayer = QgsVectorLayer(uri, 'clip_rad_grid'+rad_name1, 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
    pr_cri = pcriLayer.dataProvider() #เก็บค่า dataProvider ของชั้นข้อมูลรูปปิด
    poly_cri = QgsFeature() #สร้าง instance ของ feature ที่จะใช้สร้างรูปปิดแต่ละชิ้น
    #-add field to mem_layer to provide for feats.fields data
    pr_cri.addAttributes([QgsField("value", QVariant.Double),
                         QgsField("heightASL", QVariant.Double)])
    pcriLayer.updateFields() #update attribute

    #-สร้างชั้นข้อมูลเพื่อเก็บเรดาร์ที่ตัดของ PHS
    uri = "Polygon?crs=epsg:" + str(epsg) + "&field=id:integer""&index=yes" # กำหนดค่าของข้อมูลชั้นเวกเตอร์
    pphsLayer = QgsVectorLayer(uri, 'clip_rad_grid'+rad_name2, 'memory') #สร้าง instance ของชั้นข้อมูลเวกเตอร์ตาม uri
    pr_phs = pphsLayer.dataProvider() #เก็บค่า dataProvider ของชั้นข้อมูลรูปปิด
    poly_phs = QgsFeature() #สร้าง instance ของ feature ที่จะใช้สร้างรูปปิดแต่ละชิ้น
    #-add field to mem_layer to provide for feats.fields data
    pr_phs.addAttributes([QgsField("value", QVariant.Double),
                         QgsField("heightASL", QVariant.Double)])
    pphsLayer.updateFields() #update attribute

    #-------------------------------------------------------------------------------
    #-ตัดเรดาร์ให้ตรงกับ extent ของจังหวัดที่ต้องการ
    stt=Timing_start()
    criLayer=clipRadarByProvince(Flare_BB_CRI,prLayer,pcriLayer,pr_cri)
    print(' clipRadarByProvince(Flare_BB_CRI,prLayer,pcriLayer,pr_phs).......... ')
    Timing_used(stt)
        
    stt=Timing_start()
    phsLayer=clipRadarByProvince(Flare_BB_PHS,prLayer,pphsLayer,pr_phs)
    print(' clipRadarByProvince(Flare_BB_CRI,prLayer,pphsLayer,pr_cri).......... ')
    Timing_used(stt)

    #-------------------------------------------------------------------------------
    #กำหนดรัศมีที่จะใช้คำนวน IDW จากจุดศูนย์กลางของกริดผลลัพธ์
    #ตรงนี้คือสิ่งที่แตกต่างจาก "050Mosiac..."
#    rd=ds_s*2 #ตัวเลขที่ใช้คูณ ถ้ามากจะทำให้การคำนวนจุดมาทำ idw มีเยอะใช้เวลานาน
    rd=ds_s*1.0 #ตัวเลขที่ใช้คูณ ถ้ามากจะทำให้การคำนวนจุดมาทำ idw มีเยอะใช้เวลานาน
    #เอาสัก 1 หรือ 2 เท่าพอ ถ้า0.5 หมายถึงเอาจุดเฉพาะในกริดมาประมาณค่า
    #พบว่าใช้ 0.5 ได้ผลดีกว่าค่าที่สูง คือ ไม่พบ overestimate หรือ underestimate มากนัก

    #-อัพเดทค่าฟิวด์ในกริด C ด้วยการ intersect
    stt=Timing_start()
    updateFieldOutputByIntersectCentroid(criLayer,phsLayer,pcLayer,rd)
    print(' updateFieldOutputByIntersectCentroid(pcriLayer,pphsLayer,pcLayer,rd).......... ')
    Timing_used(stt)        
    return pcLayer
#-------------------------------------------------------------------------------
def reprojectRad(path_rad,rad_name):
    #แปลงพิกัดเรดาร์ NAD83 เป็น WGS84 ๊UTM47N
    print('reprojection....'+rad_name)
    parameter = {'INPUT': path_rad, 'TARGET_CRS': 'EPSG:32647',
                     'OUTPUT': 'memory:Rad_Reprojected'}
    result = processing.run('native:reprojectlayer', parameter)
    path_rad=result['OUTPUT']

    return path_rad
#-------------------------------------------------------------------------------
def convertdbZ2RainRadar(a,b,pLayer):
    #แปลงค่าการสะท้อนของเรดาร์ dbZ เป็นฝนประมาณค่า rain rate ด้วยความสัมพันธ์ Z-R
    print('ทำการอัพเดทค่าฟิวด์ฝนประมาณค่าจากเรดาร์ในกริดผลลัพธ์.........')
    pLayer.startEditing() #ตั้งค่าให้เริ่มการแก้ไขชั้นขัอมูล 
    
    #เลือกเฉพาะค่า dbzที่มากไม่กว่า -999
#    pLayer.selectByExpression('"Val" > {}'.format(-999)) 
    
#    for ft in pLayer.selectedFeatures():
    for ft in pLayer.getFeatures():
        if ft['Val']==-999:
            r=0.0
        else:        
            z=10**(float(ft['Val'])/10)
            r=(z/a)**(1/b)
            
        pLayer.changeAttributeValue(ft.id(),5,r) #mm/hr        
        
    pLayer.commitChanges() #ตั้งค่าให้หยุดการแก้ไขชั้นขัอมูล   
    print('เสร็จสิ้นการอัพเดทค่าฟิวด์ฝนประมาณค่าจากเรดาร์ในกริดผลลัพธ์.........')
    return pLayer
#-------------------------------------------------------------------------------
def updateColumnFlare2Rainrad(pLayer,pfLayer):
    #อัพเดทcolumns เพื่อกำหนดค่ากริดที่ตกอยู่ใน radar flare ให้เป็น nodata -999
    pLayer.startEditing() #ตั้งค่าให้เริ่มการแก้ไขชั้นขัอมูล C
        
    all_features = {}
    index = QgsSpatialIndex() # Spatial index
    for ft in pfLayer.getFeatures():
        index.insertFeature(ft)
        all_features[ft.id()] = ft

    #loopเพื่อหาว่าผลลัพธ์ที่โมเสคนี้มีกริดใดที่ตกอยู่ใน radarflare 
    for feat in pLayer.getFeatures():
        inGeom = feat.geometry()
        idsList = index.intersects(inGeom.boundingBox())
        #loop idsListB เพื่อหาจุดที่อยู่ในแนวรัศมีในการทำ idw ค่า dbz
        for id in idsList:          
            if feat['Val']==-999 and all_features[id]['heightASL']<5000 and all_features[id]['Flare1']>0:
                pLayer.changeAttributeValue(feat.id(),5,-999) #flare
                break
    
    pLayer.commitChanges() #ตั้งค่าให้หยุดการแก้ไขชั้นขัอมูล  
    return pLayer
#-------------------------------------------------------------------------------
def exportRainEstimates2Tif(outp,final_rainRad):
    #ส่งออกผลลัพธ์ฝนประมาณค่าเป็น geotif เพื่อนำไป validate กับฝนสถานี
    processing.run("gdal:rasterize", 
    {'INPUT':final_rainRad,
    'FIELD':'RainRad',
    'BURN':0,'UNITS':1,
    'WIDTH':2000,'HEIGHT':2000,
    'EXTENT':'522494.1237852003,678494.1237852003,1751182.977305875,2151182.977305875 [EPSG:32647]',
    'NODATA':-999,'OPTIONS':'',
    'DATA_TYPE':5,'INIT':None,
    'INVERT':False,
    'EXTRA':'',
    'OUTPUT':outp})
#-------------------------------------------------------------------------------

################################################################################
#โค้ดหลัก
print('#'*50)
print('เริ่มการประมวลผลโมเสคราย 15 นาที...................')

#เตรียมชื่อไฟล์เรดารเชียงราย
rad_cri = 'D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/1rad_sontihn/shp15Test/CRI/'
fn1 = []
fn1 += [f for f in os.listdir(rad_cri) if f.endswith('.shp')] #ลิสชื่อไฟล์เต็ม
ft1=[]
ft1+=[f[7:19]for f in fn1 ] #ลิสเวลาจากชื่อไฟล์ราย15นาที่
#print(ft)

#เตรียมชื่อไฟล์เรดาร์พิษณุโลก
rad_phs = 'D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/1rad_sontihn/shp15Test/PHS/'
fn2 = []
fn2 += [f for f in os.listdir(rad_phs) if f.endswith('.shp')] #ลิสชื่อไฟล์เต็ม
ft2=[]
ft2+=[f[3:15]for f in fn2 ] #ลิสเวลาจากชื่อไฟล์์ราย15นาที่
################################################################################

#ลูปหลักเพื่อเรียกฟังค์ชั่นย่อยๆด้านบนมาโมเสค
for f in ft1:
#    print('+',f)
    #ตรวจสอบว่ามีไฟล์ครบทั้งสองสถานีไหม ถ้าครบจะได้ทำโมเสคเลย
    if f in ft2:
        print('#-'*25)
        print('เริ่มการประมวลผลไฟล์'+f+'.....')
        
        #1.แปลงพิกัดและประมวลผล radar flare กับ beamblock
        #ตั้งค่าพารามิเตอร์ของเรดาร์เชียงราย
        pat = '*'+f+'*.shp'
        file = fnmatch.filter(fn1, pat)
#        print(file)
        
        path_rad = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/1rad_sontihn/shp15Test/CRI/"+file[0]
        path_beamblock = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/BeamBlockChiangraiRaster.tif"
        rad_name='CRI'
        epsg = 32647 #กำหนดค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
        binSize=500.0
        sta_coord=(99.88159181,19.96147083) #พิกัดสถานีเรดาร์ได้จาก shapefile

        #แปลง shapefile จาก EPSG:4269 - NAD83 ไปเป็น epsg:32647 UTM47N
        path_rad=reprojectRad(path_rad,rad_name)
        #ประมวลผล radar flare และ beamblock เชียงราย
        Flare_BB_CRI=run_main_flare_beamBlock(path_rad,rad_name,epsg,binSize,path_beamblock)
        #-------------------------------------------------------------------------------
        #ตั้งค่าพารามิเตอร์ของเรดาร์พิษณุโลก

        pat = '*'+f+'*.shp'
        file = fnmatch.filter(fn2, pat)
        
        path_rad = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/1rad_sontihn/shp15Test/PHS/"+file[0]
        path_beamblock = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/BeamBlockPhitsanulokRadarRaster.tif"
        rad_name='PHS'
        epsg = 32647 #กำหนดค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
        binSize=1000.0
        sta_coord=(100.2179637,16.7754090) #พิกัดสถานีเรดาร์ได้จาก shapefile

        #แปลง shapefile จาก EPSG:4269 - NAD83 ไปเป็น epsg:32647 UTM47N
        path_rad=reprojectRad(path_rad,rad_name)
        #ประมวลผล radar flare และ beamblock พิษณุโลก
        Flare_BB_PHS=run_main_flare_beamBlock(path_rad,rad_name,epsg,binSize,path_beamblock)
        #-------------------------------------------------------------------------------
        ################################################################################
        #2.โมเสคเรดาร์
        path_to_bound_layer = "D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1data/Yom_Basin_utm.shp"
        ds_s=2000 #กริดผลลัพธ์ที่ต้องการตามระบบพิกัดห้ามต่ำกว่า 5000 เมตร 
        epsg = 32647 #กำหนดค่าพิกัดชั้นข้อมูลที่จะใช้WGS84
        rad_name1="CRI"
        rad_name2="PHS"

        stt=Timing_start()
        mosaic_cri_phs=Mosaic_CRI_PHS(Flare_BB_CRI,Flare_BB_PHS,path_to_bound_layer,ds_s,epsg,rad_name1,rad_name2,f)
#        mosaic_cri_phs=Mosaic_CRI_PHS(Flare_BB_CRI,Flare_BB_PHS,path_to_bound_layer,ds_s,epsg,rad_name1,rad_name2)
        print('Mosaic_CRI_PHS(Flare_BB_CRI,Flare_BB_PHS,path_to_bound_layer,ds_s,epsg,rad_name1,rad_name2,f).......... ')
        Timing_used(stt)
        #-------------------------------------------------------------------------------
        #3.แปลงฝน dbz เป็นฝนประมาณค่าด้วย z-r relationship
        a=200.0
        b=1.6

        stt=Timing_start()
        rainRad=convertdbZ2RainRadar(a,b,mosaic_cri_phs)
        print('convertdbZ2RainRadar(a,b,mosaic_cri_phs)..........')
        Timing_used(stt)
        #-------------------------------------------------------------------------------
        #4.อัพเดทcolumns เพื่อกำหนดค่ากริดที่ตกอยู่ใน radar flare ให้เป็น nodata -999
        #ใช้Flare_BB_CRI และ Flare_BB_PHS เพื่อหา spatial index ในการ intersect กับ mosaic_cri_phs

        #อ่านวิธีการใช้ spatial index เพื่อการเข้าถึงฟีเจอร์ที่ไวขึ้น
        #https://gis.stackexchange.com/revisions/224954/4
        #pLayer=rainRad
        stt=Timing_start()
        rainRad=updateColumnFlare2Rainrad(rainRad,Flare_BB_CRI)
        print('updateColumnFlare2Rainrad(rainRad)..........CRI')
        Timing_used(stt)

        stt=Timing_start()
        final_rainRad=updateColumnFlare2Rainrad(rainRad,Flare_BB_PHS)
        print('updateColumnFlare2Rainrad(rainRad)..........PHS')
        Timing_used(stt)
        #-------------------------------------------------------------------------------
        #5.ส่งออกผลลัพธ์ฝนประมาณค่าเป็น geotif เพื่อนำไป validate กับฝนสถานี
        outp_file=f+".tif"
        outp='D:/Yang/1Reseach/0.2563.RadarMosGISYomNan/2codes/3For_TMD/1outp_mosaic_temp/'+outp_file
#        outp='D:/tmp/PyQGIS/Plugin_practice/1data/rainradarEstimates.tif'
        stt=Timing_start()
        exportRainEstimates2Tif(outp,final_rainRad)
        print('exportRainEstimates2Tif(outp)..........')
        Timing_used(stt)
        #-------------------------------------------------------------------------------
        ################################################################################
        #6.แสดงผลในแผนที่
        QgsProject.instance().addMapLayers([final_rainRad])
        #-------------------------------------------------------------------------------
        print(' จบการประมวลผลไฟล์'+f+'.....')
        print('#-'*25)
        
print('สิ้นสุดการประมวลผลโมเสคราย 15 นาที...................')
print('#'*50)
        
