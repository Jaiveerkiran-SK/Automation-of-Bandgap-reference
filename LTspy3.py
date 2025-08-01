# -*- coding: utf-8 -*-
"""
Created on Sat Jun 28 16:54:26 2025

@author: Dr. Senthilkumar
"""

#!/usr/bin/python3
#LTSPy - an LTSpice raw-file output Python reading module (python3 version)

#    Copyright (C) 2013, 2014, 2016, 2017, 2019, 2023 Torsten Lehmann
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#revision history
#v 1.041-3 file open fix
#v 1.04-3 python3 implementation
#v 1.04 fixed null-char insertion in raw files inserted in ltspice XVII
#v 1.03 fixing stepped .op generating a non-stepped data set
#v 1.02 ignoring .backanno
#v 1.01 dealing with files under windoze properly
#v 1.00 first release

#to do:
#extension for reading part of data only

#binary files:
#ac and noise sims: 2 x 8 bytes per var per point (complex)
#dc sims: 8 bytes independent then 4 bytes each var per point
#tran sims like dc - but compression has glitch negative times!
#op point like dc - first entry 8 bytes subsequent 4 bytes (silly).
#tf like dc - again a bit silly

#This program is inspired by...
#cdspy by Torsten Lehmann (spectre reader for python)
#spice_read by Werner Hoch (ngspice reader for python)
#LTSpice2Matlab by Paul Wagner (ltspice reader for matlab)

#Format has been deciphered from ascii and binary files...
#steps decided by looking at the first [0] value entry...

#import string as st #python3 string ops are string methods
import numpy as np
import sys
import os.path

debug=True

class SimData(object):
    '''Returns object with LTSpice simulation data from .raw file.  Use:
    dat=SimData(filename): read all data from filename.
    dat=SimData(filename,variablelist): read only data from variables in list.
    Key data fields:
    dat.variables is array of variables read.
        dat.variables[0] is independent variable.
    dat.variabletypes is array of variable types.
        ('voltage', 'time', etc).
    dat.values is array of values corresponding to the variable list.
        dat.values[0] is array of independent data points (no stepping).
        dat.values[0][stp] is array of independent data point in step stp.
        dat.values is complex array for ac or noise sims - otherwise real.
    with stepped simulation, information of steps attempted read from filename.log:
    dat.stepvariables is array of variables stepped
    dat.stepvalues[var][stp] is value of step variable var at step stp
    Commands and flags in .raw file is set as attribute.
        (dat.offset, dat.output, dat.date, dat.stepped, etc).
    '''

    def __init__(self,filename,tranfix=True,variablelist=None):
        '''The main reading routine...
        '''
        self.title = None
        self.date = None
        self.plotname = None
        self.novariables = None
        self.nopoints = None
        self.offset = None
        self.output = None
        self.command = None
        self.variables = []
        self.variabletypes = []
        self.values = []
        self.real = True #for complex real=False
        self.forward = True #for reverse forward=False
        self.linear = True #for log linear=False
        self.stepped = False
        self.steplen = None
        self.nosteps = None
        self.steppoints = None
        self.stepvariables = None
        self.stepvalues = None
        self.flags = None
        self.analysis = None
        self.binary = None
        self.ltsvxvii = False
        debug = 0

        (simfilename,logfilename)=self.getfilenames(filename)
        simfile = open(simfilename,'rb') #TL removed 'U' from mode 
        line = simfile.readline()
        if debug: print('Debug: ',line)
        if line.find(b'\0') >= 0:
            self.ltsvxvii = True # null chars detected
            if debug: print('Debug: ltsvxvii')
        while line != b'':
            keylist = [t.strip() for t in line.replace(b'\0',b'').split(b':',1)]
            keyword = keylist[0].lower()
            if debug & 1: print(">"+keyword+"<", ord(keyword[0]))
            if keyword == b'title':
                self.title = keylist[1]
            elif keyword == b'date':
                self.date = keylist[1]
            elif keyword == b'plotname': #DC AC Operating Transfer Transient Noise
                self.plotname = keylist[1]
                self.analysis = keylist[1].strip().split()[0].lower()
            elif keyword == b'output':
                self.output = keylist[1]
            elif keyword == b'flags':
                self.flags = [t.strip().lower() for t in keylist[1].split()]
                for flag in self.flags: # more flags to come
                    if flag == b'real': #for most sims
                        self.real = True
                    elif flag == b'complex': #for ac analysis
                        self.real = False
                    elif flag == b'forward':
                        self.forward = True
                    elif flag == b'reverse': #sweep is from high-to-low values - use for stepped
                        self.forward = False
                    elif flag == b'log': #log sweep
                        self.linear = False
                    elif flag == b'stepped': #stepped sweep (multi-sweep)
                        self.stepped = True
                        self.nosteps = 0
                        self.steppoints = [0]
                    else:
                        print('unknown flag',flag)
            elif keyword == b'no. variables':
                self.novariables = int(keylist[1]) #if this is wrong it will stuff up reading
            elif keyword == b'no. points':
                self.nopoints = int(keylist[1]) #if this is wrong it will stuff up reading
            elif keyword == b'offset':
                self.offset = float(keylist[1])
            elif keyword == b'command':
                self.command = keylist[1]
                if self.command.find(b'XVII') >=0: self.ltsvxvii = True
            elif keyword == b'variables': # the saved variables...
                for vno in range(self.novariables): #entry independent var?
                    line = simfile.readline()
                    varentry = line.replace(b'\0',b'').strip().split()
                    if len(self.variables) != int(varentry[0]) or vno != int(varentry[0]):
                        print('unsuspected variable entry',line)
                    self.variables.append(varentry[1])
                    self.variabletypes.append(varentry[2])
                    if self.real:
                        self.values.append(np.zeros(self.nopoints))
                    else:
                        self.values.append(np.zeros(self.nopoints,dtype=complex))
            elif keyword == b'values': # ascii data
                self.binary = False
                for pno in range(self.nopoints):
                    line = simfile.readline()
                    valentry = line.replace(b'\0',b'').strip().split()
                    if int(valentry[0])!=pno:
                        print('unsuspected value entry',line)
                    self.values[0][pno] = self.getrcvalue(valentry[1],self.real)
                    if self.stepped:
                        if pno > 0:
                            if self.isnewstep(self.values[0][pno],self.values[0][pno-1],self.forward,self.real):
                                self.steppoints.append(pno)
                                self.nosteps += 1
                    for vno in range(1,self.novariables):
                        line = simfile.readline()
                        self.values[vno][pno] = self.getrcvalue(line.replace(b'\0',b'').strip(),self.real)
            elif keyword == b'binary': # binary data
                self.binary = True
                if self.ltsvxvii: rubbish = simfile.read(1) # read \0 char after newline
                if not self.real:
                    alldata = np.fromfile(simfile,count=2*self.novariables*self.nopoints,dtype='float64')
                    for pno in range(self.nopoints):
                        for vno in range(self.novariables):
                            index = self.novariables*pno*2+vno*2
                            self.values[vno][pno]=complex(alldata[index],alldata[index+1])
                else:
                    for pno in range(self.nopoints):
                        self.values[0][pno]=np.fromfile(simfile,count=1,dtype='float64')
                        pointdata = np.fromfile(simfile,count=self.novariables-1,dtype='float32')
                        for vno in range(1,self.novariables):
                            self.values[vno][pno]=pointdata[vno-1]
                if self.analysis == b'transient' and tranfix:
                    self.values[0]=abs(self.values[0])
                if self.stepped:
                    for pno in range(1,self.nopoints):
                        if self.isnewstep(self.values[0][pno],self.values[0][pno-1],self.forward,self.real):
                            self.steppoints.append(pno)
                            self.nosteps += 1
            elif keyword == b'backannotation':#just ignore
                self.backannotation = keylist[1]
            else:
                print('unknown keyword',keylist[0])
            line = simfile.readline()
        if self.nosteps != None and self.nosteps != 0:#'and self.nosteps!=0 - fix for stepped .op
            self.nosteps += 1
            self.steppoints.append(self.nopoints)
            self.steplen = np.array(self.steppoints[1:self.nosteps+1])-np.array(self.steppoints[0:self.nosteps])
            if self.nosteps == 1: # not really stepped after all as no repeat steps... step primary sweep.
                self.steplen=self.steplen[0]
            else:
                alldata=self.values[:]
                for vno in range(self.novariables):
                    self.values[vno]=[[]]*self.nosteps
                    for sno in range(self.nosteps):
                        self.values[vno][sno]=alldata[vno][self.steppoints[sno]:self.steppoints[sno+1]]
            if not os.path.isfile(logfilename):
                print('no logfile for step info')
            else:
                logfile=open(logfilename,'rb') #TL removed 'U' from mode
                line = logfile.readline()
                while line != b'':
                    keylist = line.replace(b'\0',b'').split()
                    if keylist != [] and keylist[0] == b'.step':
                        if self.stepvariables == None:
                            self.stepvariables = []
                            self.stepvalues = []
                            for key in keylist[1:]:
                                stepvar,stepval = key.split(b'=')
                                self.stepvariables.append(stepvar)
                                self.stepvalues.append([])
                        stv = 0
                        for key in keylist[1:]: #.step v1=7.2 run=6
                            stepvar,stepval = key.split(b'=')
                            self.stepvalues[stv].append(float(stepval))
                            stv += 1
                    line = logfile.readline()
                for stv in range(len(self.stepvariables)):
                    self.stepvalues[stv] = np.array(self.stepvalues[stv])

    def getrcvalue(self,string,real):
        '''Support function to read "real" or "real,imaginary"
        number from string.
        '''
        if real:
            return float(string)
        else:
            ss = string.split(b',')
            return float(ss[0])+complex(ss[1]+b'j')

    def isnewstep(self,value,oldvalue,forward,real):
        '''Support function to see if independent variable has wrapped
        around.
        '''
        if forward:
            fwdfac=1
        else:
            fwdfac=-1
        if not real:
            value=abs(value)
            oldvalue=abs(oldvalue)
        return value*fwdfac < oldvalue*fwdfac

    def getfilenames(seld,filename):
        filebase,extension = os.path.splitext(filename)
        if extension == '':
            extension = '.raw'
        return (filebase+extension,filebase+'.log')

    def getfilenames_old(self,filename):
        x=filename.split('.')
        basename=x[0]
        if len(x)>1:
            extension=x[-1]
            for i in range(1,len(x)-1):
                basename+='.'+x[i]
        else:
            extension='raw'
        return (basename+'.'+extension,basename+'.log')

if __name__ == '__main__':
    print('LTSPy version 1.041-3 )c( 2019 by Torsten Lehmann')
    if len(sys.argv) != 2:
        print('''Reads LTSpice .raw output files into python.
        Import in your python program for data analysis and use:
        mydata = ltspy.SimData('mydatafilename.raw')

        Commandline use prints .raw file information; use:
        python ltspy.py mydatafile.raw
        ''')
    else:
        data = SimData(sys.argv[1])
        print('File:', sys.argv[1])
        print('Title:', data.title)
        print('Date:', data.date)
        print('Plotname:', data.plotname)
        print('No. variables:', data.novariables)
        print('No. points:', data.nopoints)
        print('Offset:', data.offset)
        print('Output:', data.output)
        print('Command:', data.command)
        print('Binary:', data.binary)
        print('Analysis:', data.analysis)
        print('Flags:', data.flags)
        if data.stepped:
            print('Steplengths:', data.steplen)
            print('No. steps', data.nosteps)

