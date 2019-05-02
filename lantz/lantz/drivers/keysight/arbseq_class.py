class Arbseq_Class(object):

    def __init__(self, name, timestep):
        self.name = name
        self.timestep = timestep
        self.ydata = None
        self.totaltime = None
        self.timeexp = 1e-6
        self.widths = None
        self.heights = None
        self.delays = None
        self.nrepeats = None
        self.repeatstring = None
        self.markerstring = None
        self.markerloc = None

    def create_sequence(self):
        if self.totaltime is None:
            raise ValueError('createsequence: No value defined for totaltime')
        if self.widths is None:
            raise ValueError('createsequence: No value defined for widths')
        if self.heights is None:
            raise ValueError('createsequence: No value defined for heights')
        if self.delays is None:
            raise ValueError('createsequence: No value defined for delays')

        values = list()
        totaltime = self.totaltime
        timestep = self.timestep

        for i in range(len(self.widths)):
            width = self.widths[i]
            height = self.heights[i]
            delay = self.delays[i]

            if (timestep > width or (delay > 0 and timestep > delay)):
                raise ValueError('createsequence: timestep does not match values')

            for x in range(int(delay/timestep)):
                values.append(0)
            for y in range(int(width/timestep)):
                values.append(height)

            totaltime -= (delay + width)

        for x in range(int(totaltime/timestep)):
            values.append(0)

        self.ydata = values

    def get_seqstring(self):
        seqstring = ('"{}"'.format(self.name) 
        + ',' + str(self.nrepeats) + ',' + self.repeatstring 
        + ',' + self.markerstring + ',' + str(self.markerloc))
        print('Created seqstring: ' + seqstring)
        return seqstring





