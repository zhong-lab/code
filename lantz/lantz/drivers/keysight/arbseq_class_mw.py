import numpy as np 
from scipy import signal
import matplotlib.pyplot as plt

class Arbseq_Class_MW(object):

    def __init__(self, name, timestep, typepulse ,amplitude,widths,freq,phase):
        self.name = name
        self.timestep = timestep
        self.ydata = None
        self.widths = widths   # Minimum width is 32*Samples, so width and timestep should be such that width>=32*timestep
        self.amplitude = amplitude  #Number between 0-1
        self.nrepeats = 0
        self.repeatstring = 'once'
        self.markerstring = 'lowAtStart'
        self.markerloc = 0
        self.freq = freq   # Frequency of the sine wave
        self.phase = phase  #  Phase of sine wave, could be 0 to 360 degrees. 
        self.type = typepulse  #  Type of pulse envelope, could be 'Square', 'Gaussian', 'Triangle' or 'DC'
        self.delays = 0        # Delay before a pulse
        self.postdelay = 0    # Delay after a pulse

    
    def sendTrigger(self):
        # self.markerstring ='highAtStartGoLow'
        self.markerstring ='highAtStart'

    def setRepeats(self,repeatwidth):

        self.repeatstring = 'repeat'
        self.nrepeats = round(repeatwidth/self.widths)

    def create_sequence_mwpulse(self):
        if self.widths is None:
            raise ValueError('createsequence: No value defined for widths')
        if self.amplitude is None:
            raise ValueError('createsequence: No value defined for amplitude')
        if self.delay is None:
            raise ValueError('createsequence: No value defined for delay')



        self.ydata = values

    def Gauss(self,sig,mu,x):
        
        f=np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

        return f

    def create_envelope(self):
        

        values = list()
        timestep = self.timestep

        width = self.widths
        height = self.amplitude
        delay1= self.delays
        delay2=self.postdelay
        omega=2*np.pi*self.freq 
        phi=self.phase*(np.pi/180)

        if (timestep > width or (delay1> 0 and timestep > delay1)):
            raise ValueError('createsequence: timestep does not match values')

        for x in range(round(delay1/timestep)):
            values.append(0)


        if (self.type == 'DC') :

            for y in range(round(width/timestep)):   # Added a +1 here since it was causing problems in CPMG, each pulse was delayed by like 0.1 us

                values.append(height)

        if (self.type== 'Square'):
            

            if omega == 0:
                for y in range(round(width/timestep)):
                    values.append(height)
            else:
                for y in range(round(width/timestep)):
                    values.append(height*np.sin(omega*timestep*y+phi))


        if (self.type== 'COMP1'):     # Composite pulse pi/2x pi2my
            
            if omega == 0:
                for y in range(round(width/timestep)):
                    values.append(height)

            else:
                for y in range(round(width/timestep)):

                    if(y<(round(0.5*width/timestep))):

                        values.append(height*np.sin(omega*timestep*y+0+phi))

                    else:

                        time=(y-round(0.5*width/timestep))
                        values.append(-height*np.sin(omega*timestep*time+(np.pi/2)+phi ))  


        if (self.type== 'COMP2'):   # Composite pulse pi2my  pi/2x
            
            if omega == 0:
                for y in range(round(width/timestep)):
                    values.append(height)

            else:
                for y in range(round(width/timestep)):

                    if(y<(round(0.5*width/timestep))):

                        values.append(-height*np.sin(omega*timestep*y+(np.pi/2)+phi )) 

                    else:

                        time=(y-round(0.5*width/timestep))
                        values.append(height*np.sin(omega*timestep*time+0+phi))


        if (self.type== 'COMP3'):   # Composite pulse pi/2x  pi/2y
            
            if omega == 0:
                for y in range(round(width/timestep)):
                    values.append(height)

            else:
                for y in range(round(width/timestep)):

                    if(y<(round(0.5*width/timestep))):

                        values.append(height*np.sin(omega*timestep*y+0+phi )) 

                    else:

                        time=(y-round(0.5*width/timestep))
                        values.append(height*np.sin(omega*timestep*time+(np.pi/2)+phi))


        if (self.type== 'COMP4'):   # Composite pulse pi/2y  pi/2x
            
            if omega == 0:
                for y in range(round(width/timestep)):
                    values.append(height)

            else:
                for y in range(round(width/timestep)):

                    if(y<(round(0.5*width/timestep))):

                        values.append(height*np.sin(omega*timestep*y+(np.pi/2)+phi )) 

                    else:

                        time=(y-round(0.5*width/timestep))
                        values.append(height*np.sin(omega*timestep*time+0+phi))


        elif (self.type == 'Gaussian'):
            mu=width/2
            sigma=width/4     # Assuming pulse width is 4 sigma = point where the amplitude goes down to 0.1% of peak value


            if omega ==0:
                for y in range(round(width/timestep)):
                    values.append(height*self.Gauss(sigma,mu,y*timestep))

            else:
                for y in range(round(width/timestep)):
                    values.append(height*self.Gauss(sigma,mu,y*timestep)*np.sin(omega*timestep*y+phi))





        elif (self.type == 'Triangle'):

            
            
            slope=height/(width*0.5)

            if omega ==0:
                for y in range(round(width/timestep)+1):

                    if(y<(int(0.5*width/timestep))):

                        h=(y*timestep)*slope
                        values.append(h)

                    else:

                        h=height-(y*timestep - width*0.5)*slope
                        values.append(h)

            else:
                for y in range(round(width/timestep)+1):

                    if(y<(int(0.5*width/timestep))):

                        h=(y*timestep)*slope
                        values.append(h*np.sin(omega*timestep*y+phi))

                    else:

                        h=height-(y*timestep - width*0.5)*slope
                        values.append(h*np.sin(omega*timestep*y+phi))                

        for x in range(round(delay2/timestep)):
            values.append(0)

        print('Lenght of sequence is {}'.format(len(values)))
        # print('Seq is {}'.format(values))
        self.ydata=values
                






    def get_seqstring(self):
        seqstring = ('"{}"'.format(self.name) 
        + ',' + str(self.nrepeats) + ',' + self.repeatstring 
        + ',' + self.markerstring + ',' + str(self.markerloc))
        print('Created seqstring: ' + seqstring)
        return seqstring

    



