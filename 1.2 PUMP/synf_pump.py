'''

required files - 

1) wdn in graphml format (e.g., tempe_dia.graphml)
2) wdn in EPANET format (e.g., tempe.inp)

'''




from datetime import datetime
start=datetime.now()
import epa_valve
import epa_pump_1

cityname='sanjuan'

print ('valve started')
epa_valve.epa_2('%s'%(cityname))

print ('pump started')
epa_pump_1.epa_2('%s'%(cityname))




print ('Total time taken : %s'%(datetime.now()-start))