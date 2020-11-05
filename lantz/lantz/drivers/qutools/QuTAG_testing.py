import qutag
import time


threshold_voltage = 0.1 #100mV

#device = QuTAG()
device = qutag.QuTAG()

#device.enableChannels((1,2,3,4))
device.enableChannels((0,1))
#Set threshold voltage on all channels
device.setSignalConditioning(1, 3, 1, threshold_voltage)
# device.setSignalConditioning(2, 3, 1, threshold_voltage)
# device.setSignalConditioning(3, 3, 1, threshold_voltage)
# device.setSignalConditioning(4, 3, 1, threshold_voltage)

print("Searching for timestamp on all channels")


timestamp_list = []

while(1):
#Check the data loss
    
    try:
    
        d_loss = device.getDataLost()
        if(d_loss != 0):
            print("Warning, data loss was " + str(d_loss) + ", some timestamps have been missed")
        time.sleep(3)
        #Readback timestamps from the device
        t_s = device.getLastTimestamps(True)
        
        #If we didnt get any timestamps
        if(t_s[2] == 0):
            print("Empty")
            continue#keep going
        
        for i in range(0, t_s[2]):
            #If we find a timestamp of this channel
            if(t_s[1][i] != 104):
                ret_val = t_s[0][i]
                timestamp_list.append(ret_val)
                print("Timestamp found for channel #" + str(t_s[1][i]) + ", timestamp was: " + str(ret_val))
                
                
    except KeyboardInterrupt:

         print("TDC interrupted by user, exiting...")
         break



device.deInitialize()  

print("Timestamp list was: " + str(timestamp_list))