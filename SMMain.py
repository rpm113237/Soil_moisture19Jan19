#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Thu Mar 29 07:55:41 2018

@author: Rich
"""

import sys
import glob
import serial
import time
import os
import math
from pandas import DataFrame, read_csv
import pandas as pd
# import fileinput
import dropbox
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from matplotlib import ticker as ticker
from csv import reader
from csv import DictReader
from dateutil import parser
# from dateutil import relativedelta
# import calendar

import contextlib
from decimal import Decimal
# import fileinput
import csv
# from shutil import copyfile
# from sys import exit

access_token = "aelnjlQMStkAAAAAAACfyW27v2oV8u5PkHnMELuOUyGbZyOhhQPsBFWt2vffTrO4"
# for db instantation

UNIT_DIRECTORY_HDGS = ["Station_Name_Old", "Station_Name_New", "Snsr0_Nm",
                       "Snsr1_Nm", "Snsr2_Nm", "Snsr3_Nm", "SnsrRef_Nm",
                       "Temp_Nm", "Report H.h", "Rpt1", "Rpt2", "Rpt3",
                       "Rpt4"]

StaDict_lcl = 'StationID_lcl.csv'
StaDict_db = '/StationID_db.csv'

# Note the Station name/extension makes the controller (this program) unique
# right now, you cannot have two.

lcl_pdf = 'lclfile.pdf'  # local file path
db_pdf = '/dbpdf.pdf'  # dropbox path

# There are two files, stored locally and on Dropbox:
# One with the data in it, one with the station ID's in it
# lcltxt:lclfile.txt, lclpdf: lclfile.pdf;
# dbtxt: dbfile.txt and dbpdf:dbfile.pdf

YaxisDict = {"Delm": "Delmhorst Units", "Ohms": "Ohms", "Mbars": "Millibars"}
# LegendDict = {"Delm": "DUnits", "Ohms": "Ohms", "Mbars": "Mbar"}
StartColDict = {"Delm": 2, "Ohms": 2, "Mbars": 12, "Temp": 8}
HeadingsDict = {"Time": 1, "Vbat": 7, "Temp": 8}
# current, change when format changes.

UNIT_RESP_HDGS = ['StaID', 'Sns0', 'Sns1', 'Sns2', 'Sns3',
                  'SnsRef', 'Vbat', 'Temp']

# to make dict out of Station Response

DATA_FILE_HDGS = ['Station', 'DateTime', 'Ohms0', 'Ohms1', 'Ohms2',
                  'Ohms3', 'OhmsRef', 'Vbat', 'Temp']
NO_PLOT_LIST = ['',' ', 'None', '0']
PLOT_OHMS = False
PLOT_OHMS_ADJ = True


AlmMin = 2  # alrm delay in minutes
# TODO alarm Delay in hours--later read from DB File
AlarmDelay = round(Decimal(AlmMin / 60), 3)
PrintTimes = False
PrintVerbose = False

TFACT = .064     # temperature offset factor
TOFF = 23

def TODOs():

    """
This is a generalized comment file
Used for list of TODO's # TODO
Need some renaming of things like StaDict
The Master Dictionary file is called UnitDirectory.  It is stored locally (on the RPi)
as UnitDirectory_lcl and on Dropbox as UnitDirectory.  The Dropbox file is the master.
It is downloaded and the local file updated.  If it cannot be downloaded, the local
file is used.  There is currently no mechanism to change the name of this file.
Meaning currently there is no possibility of having two RPi's on the same Dropbox App
The first row is a header (UNIT_DIRECTORY_HDGS), each row below has corresponding values, by Unit
Each Field Unit has a .txt file (.csv for easier opening??) labelled (UnitName)_Data.
This file is since beginning of time.  It is updated with each data report from the Unit.
When a FieldUnit is renamed, its Data file is renamed.
The .pdf plot, at the moment, is stored only on Dropbox.  If the Unit is renamed, new pdf's
are created, there is currently no mechanism to rename or remove the old ones.  The DropBox
API apparently has a mechanism, but I haven't figured it out.  The user can delete the old
pdf's.  They will not be updated.

    """

def make_unitdirectory(lcl_path, db_path):
    """
    This checks existence of dictionary (named UnitDirectory),
    makes one if it doesn't exist; writes out headings.
    Only does anything in first time after initialization.
    Stored both locally and on Dropbox
    formal parameters unused  # TODO


    """
    if os.path.exists(StaDict_lcl):

        filelen = len(open(StaDict_lcl).readlines())
        if PrintVerbose:
            print(StaDict_lcl + " exists, length(lines) = " +
            str(filelen))  # should be a db dict
        download_file(StaDict_lcl, StaDict_db)  # necessary TODO  ???
        filelen = len(open(StaDict_lcl).readlines())
        if PrintVerbose:
            print(StaDict_lcl + " DropBox D/L, length(lines) = " +
            str(filelen))  # should be a db dict
#        pass
    else:
        fo = open(StaDict_lcl, "w")
        # opens if not already, resets pointer to beginning
        fo.write(','.join(UNIT_DIRECTORY_HDGS) + '\n')
#        fo.write("Station_Name_Old,Station_Name_New,Snsr0_Nm,Snsr1_Nm,"
#                 + "Snsr2_Nm,Snsr3_Nm,SnsrRef_Nm,Temp_Nm\n")

        # TODO figure out what to do if fails to upload.  Or init
        fo.close()
        filelen = len(open(StaDict_lcl).readlines())  # TODO--why
        upload_file(StaDict_lcl, StaDict_db)
        print(StaDict_lcl + " Dictionary created, initialized,  & uploaded")
        print("Station ID Dict len = " + str(filelen))  # TODO--why
    return
# TODO: Change upload/download to db_sdk_example error tolerant versions

def upload_file(lcl_f, db_f):

    """
    uploads lcl_f to db_f
    # TODO add in error checking in case db not home
    # If db doesn't respond, just proceed with local file.
    """
    at0 = time.time()
    dbx = dropbox.Dropbox(access_token)
    with open(lcl_f, 'rb') as f:
    # TODO rewrite for failed write--returning NONE? Not hanging up.
        dbx.files_upload(f.read(), db_f, mode=dropbox.files.WriteMode.overwrite,
                         mute=True)
        # f.read uploads all characters in file
    if PrintTimes:
        print_time(f'Time to upload {lcl_f}', at0)
    #f.close()
    return


def download_file(lcl_f, db_f):
    """
    downloads db_f to lcl_f
    # TODO add in error checking in case db not home
    # If db doesn't respond, just proceed with local file.
    """
    at0 = time.time()
    dbx = dropbox.Dropbox(access_token)
    with open(lcl_f, 'w') as f:    # overwrites local file
        dbx.files_download_to_file(lcl_f, db_f)
    if PrintTimes:
        print_time(f'Time to download {lcl_f}', at0)
#    f.close()
    return

def print_time(message, t0):
    eltime = time.time()-t0
    if eltime >= 1:
        print(f'{message} : {round(eltime,2)} s')
    else:
        print(f'{message} : {round(eltime*1000,1)} ms')
    return


def get_time():
    # t = time.localtime(time.time)
    now = datetime.now()
    strnow = now.strftime("%m/%d/%y %H:%M")
    # format to make sheets, whatever work
    # print (strnow)
    return strnow


def Mx_B(Rx, RL, RH, BarL, BarH):
    # //note r0, r1 in ohms, bar1, bar0 in actual Bar *10
    # //also used for the Delm calc--which has neg slope
    if Rx > RH:
        retval = 0
    else:
        denom = RH-RL
    if denom == 0:
        denom = 1  # //shouldn't happen
    if BarH >= BarL:
        retval = ((BarH-BarL) * (Rx-RL)) / denom + BarL
    num = BarH - BarL
    if BarH < BarL:
        retval = BarL - (((BarL - BarH) * (Rx - RL)) / denom)
    #    num = (BarL-BarH)

    return retval


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
        : left in (rpm) for portability to RPi

        : see https://www.dropbox.com/developers-v1/core/start/python
    """

    if sys.platform.startswith('win'):
        ports = ['COM%s' % str(i) for i in range(2, 256)]
        # (2,256) to bump past COM1--which is a windows artifact
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass

    return result


def trimfile(f, xdays):
    """
    finds the last time stamp in file f (the master file)
    returns a file ftrim that starts xdays before the last time stamp, ends
    with last time stamp.
    if there is no timestamp xdays back, returns the entire file f
    trimfile is a working file.  Not archived.  The master file (f)
    is the only one archived

    """
# try pandas
    # for test --force xdays
    # xdays = 10
    df = pd.read_csv(f)
    df['dt_tm'] = df.apply(lambda row: datetime.strptime(row['DateTime'], "%m/%d/%y %H:%M"), axis=1)
    first_time_to_plot = df['dt_tm'].max() - timedelta(days=xdays)
    df = df[df.dt_tm > first_time_to_plot]
    df.reset_index(inplace=True)
    df_len = len(df)-1  # index starts at zero
    xdt_act = df['dt_tm'].max()-df['dt_tm'].min()
    last_time = df.at[df_len, 'dt_tm']
    last_vbat = df.at[df_len, 'Vbat']
    last_temp = df.at[df_len,'Temp']
    xdays_act = xdt_act.days + math.ceil(xdt_act.seconds / (3600 * 24))

    file_nm_base = df.at[df_len,'Station']
    titleTmStamp = f'{last_time}  {last_temp}(C) {last_vbat}V'
    titleID = f'{file_nm_base} (last {xdays} days)'

    # from matplotlib import rcParams
    # rcParams.update({'figure.autolayout': True})

    fig, ax1 = plt.subplots()
    ax1.set_xlabel(titleTmStamp, color="red", fontsize=12, weight="bold")
    # ax1.set_ylabel(YaxisDict[Param], color="black")
    ax1.set_ylabel('Ohms', color="black")
    # TODO--this only works for ohms; need to have an ohms adjust?
    # TODO--make an Ohms adjust routine.  Keep raw and adjusted?
    plt.title(titleID, fontsize=12, weight="bold", color="red")

    # gca stands for 'get current axis'
    plt.style.use('fivethirtyeight')
    ax1 = plt.gca()
    # ax1.set_xlabel(titleTmStamp, color="orange")
    df.plot(kind='line', x='dt_tm', y='Ohms1', ax=ax1)
    df.plot(kind='line', x='dt_tm', y='Ohms2', ax=ax1)
    df.plot(kind='line', x='dt_tm', y='Ohms3', ax=ax1)
    # df.plot(kind='line', x='dt_tm', y='Ohms0', ax=ax1)
    ax1.set_xlabel(titleTmStamp)

    ax2 = ax1.twinx()
    ax2.set_ylabel('Temp(C)', color="magenta")
    l = ax1.get_ylim()
    l2 = ax2.get_ylim()
    f = lambda x: l2[0] + (x - l[0]) / (l[1] - l[0]) * (l2[1] - l2[0])
    ticks = f(ax1.get_yticks())
    ax2.yaxis.set_major_locator(ticker.FixedLocator(ticks))
    # ax2.set_ylim(15, 30)
    plt.yticks(fontsize=12, color="magenta")
    df.plot(kind='line', x='dt_tm', y='Temp', label='Temp(C)', color='magenta', ax=ax2)

    # plt.show()
    # time.sleep(10)

    lcl_pdf_file = file_nm_base + "_" + str(xdays) + ".pdf"
    db_pdf_file = "/" + lcl_pdf_file

    plt.savefig(lcl_pdf_file, facecolor="b", transparent=False,
                bbox_inches="tight")

    upload_file(lcl_pdf_file, db_pdf_file)

    # plt.close('all')


    # TODO :figure out how to name and store file.
    # create a named trim file & plot for  report time (in unit directory)
    # Name file (Station) +_xdays
    # TODO--use trim days or actual for file name?
    # If trimfile sees it already exists, don't make it
    # don't plot it.  plot has to remove the file after plot
    # trimfile is local--if uploaded, for visibility only. db trim file is
    # don't upload trim fle.

    # TODO why by bother with the .csv?  why not pass the df?

    # if PLOT_OHMS_ADJ:
    #     L = ohms_adj(L,TFACT,TOFF)
    # fw.write(','.join(L)+'\n')


    return "ftrim.csv"

def plotSM(Param, unit_id, data_file_name, xdays):

    # TODO label plot = Station Name == filename w/o extension
    # TODO change the plot labels to the StaDict headings
    """
    def plotSM(Param, trimfile, xdays)
    rework 24Jan19.  Needs Param (Y axis title); .csv trimfile to be 
    plotted, number of days looking back (xdays) (could be derived)
    Unit Name comes from last entry in trim file. pdf will be named using 
    file name of trimfile
    
    Produces a plot starting at end of file time stamp (most recent entry)
    (time stamp format 04/19/18 13:41
     back for xdays. The (pdf) plot is named:
     "SM_Param_ndays.pdf" and stored locally and on dropbox.

    Param = String such as Delm, Ohms, Mbars (currently not used)
    Param is only used to label the plot
    unit_id is a list == StaID entry for this file
    data_file_name = name of local .txt file with Data in it.
    (csv): Station Name, TimeStamp,Data0, Data1, Data2, Data3, Vbat, Temp

   Example: plotSM("Ohms", "localdat.txt", "Marsanne", 3)
   would go to localdat.txt file  (which is actually a csv)
   go back three days, create a pdf plot of labeled "Ohms"
   create or overwrite file labeled Marsanne_3_days.pdf;
   stored locally and pushed to DB
    TODO--put in error handling in case lclfile is corrupted.

    """

# get last time, temp, Vbat    
    with open (data_file_name, 'r') as f:
        for line in f:
            x = line
    ls = x.split(',')
    last_time = ls[data_file_hdg_index['DateTime']]
    last_Vbat = ls[data_file_hdg_index['Vbat']]
    last_temp = ls[data_file_hdg_index['Temp']]        

    FileBase = ls[data_file_hdg_index['Station']]
    titleTmStamp = f'{last_time}  {last_temp}(C) {last_Vbat}V'
    titleID = f'{FileBase} (last {xdays} days)'
    
    with open(trimfile(data_file_name, xdays), 'r') as ftrim:
        data = list(reader(ftrim))
        
# set up plot
    fig, ax1 = plt.subplots()
    ax1.set_xlabel(titleTmStamp, color="orange")
    ax1.set_ylabel(YaxisDict[Param], color="black")
# TODO--this only works for ohms; need to have an ohms adjust?
# TODO--make an Ohms adjust routine.  Keep raw and adjusted?
    tfact = .064     # temperature offset factor
    toff = 23
    plt.title(titleID, fontsize=12, weight="bold", color="red")
    # pyplot.axis('auto')
    # plt.grid(True)
    # plt.xticks(rotation=45)

    col = StartColDict[Param]
# TODO--fix this.  Get rid of StartColDict, use headings unit_dir_hdg_index
#    print ("col = ", col)
    tcol = StartColDict["Temp"]
#    print ("temp col = ",tcol)
    #tfact = .06
    #t0 = 27--original equation used 23C might want to fiddle.
    #but t0=27 and tfact = .04 seems to work pretty well.

    Line0 = [float(i[col])/(1+tfact*(toff-float(i[tcol])))
             for i in data[1::]]
#    print ("line0= ", Line0)
    Line1 = [float(i[col+1])/(1+tfact*(toff-float(i[tcol])))
             for i in data[1::]]
#    print ("line1= ", Line1)
    Line2 = [float(i[col+2])/(1+tfact*(toff-float(i[tcol]))) for i in data[1::]]
#    print ("line2= ", Line2)
    Line3 = [float(i[col+3])/(1+tfact*(toff-float(i[tcol]))) for i in data[1::]]
#    Line1 = [float(i[col+1]) for i in data[1::]]
#    Line2 = [float(i[col+2]) for i in data[1::]]
#    Line3 = [float(i[col+3]) for i in data[1::]]
    Temp = [float(i[StartColDict["Temp"]]) for i in data[1::]]
    # print ('temp = ' + Temp)
    time = [parser.parse(i[1]) for i in data[1::]]
    mx = 2      # markersize
    plt.xticks(fontsize=8, rotation=45)
    plt.yticks(fontsize=8, color="red")

    ax1.grid(linestyle='-', linewidth='0.5', color='red')
    ax1.grid(True)
    
# TODO here: check ID against a list of "no plots" ['',' ', 'None', '0']
    if  not (unit_id['Snsr0_Nm'] in NO_PLOT_LIST):
        ax1.plot(time, Line0, "ro-", label=unit_id['Snsr0_Nm'], markersize=mx)
    if unit_id['Snsr1_Nm'] != " ":
        ax1.plot(time, Line1, 'gx-', label=unit_id['Snsr1_Nm'], markersize=mx)
    if unit_id['Snsr2_Nm'] != " ":
        ax1.plot(time, Line2, 'b^-', label=unit_id['Snsr2_Nm'], markersize=mx)
    if unit_id['Snsr3_Nm'] != " ":
        ax1.plot(time, Line3, 'ms-', label=unit_id['Snsr3_Nm'], markersize=mx)

    ax2 = ax1.twinx()
    ax2.set_ylabel('Temp(c)', color="yellow")
    #ax2.set_ylim(15, 30)
    plt.yticks(fontsize=8, color="yellow")
    plt.plot(time, Temp, 'yx--', label=unit_id['Temp_Nm'], markersize=mx)
    # plots, but need twinx() assigned

    ax1.legend(loc=2, prop={'size': 8})
    ax2.legend(loc=1, prop={"size": 8})

    lcl_pdf_file = FileNmBase + "_" + str(xdays) + ".pdf"
    db_pdf_file = "/" + lcl_pdf_file

    plt.savefig(lcl_pdf_file, facecolor="b", transparent=False,
                bbox_inches="tight")

    upload_file(lcl_pdf_file, db_pdf_file)
    plt.close('all')
    # fig.close   ???? getting wornings about too many figs open

    return





def ser_wrt(Com, wrtstr):
    '''
    write wrtstr to Com"
    has character by character delay--poor way to avoid overrun on FM
    transmitters.

    '''
    # TODO-- figure out transmitter delay issue.

    try:
        ser = serial.Serial(Com, baudrate=9600, timeout=None)
    except serial.SerialException as e:
        print(f"could not open serial port '{Com}': {e}")
        return False
    wrtlist = list(wrtstr)
    for num, char in enumerate(wrtlist):
        ser.write(char.encode())

        time.sleep(.015)    # TODO 15ms delay??

    ser.close()
    return True
# ???? there may be more error checking on write??

def get_unit_response(COM, howlong):
    """
    Opens port COM
    waits until howlong has elapsed
    min string len should be 3--"AOK"
    if <3, had to be timeout, returns "AWOL"
 # TODO --make str len a parameter ?????
    strips comments (comments start with //)

    """

    at0 = time.time()
    if howlong is 0:
        howlong = None
    try:
        ser = serial.Serial(COM, baudrate=9600, timeout=howlong)
    except serial.SerialException as e:
        print(f"could not open serial port '{COM}': {e}")
        return "None"
    if PrintVerbose:
        print(f'reached get_unit_response, Print Times = {PrintTimes}')

    at0 = time.time()
    lineraw = (ser.readline().decode(encoding='UTF-8',
                                     errors='ignore'))
    # Note--if timeout min len is 1--\n
    # errors= 'ignore'--means ignore undecodeable characters
    line = lineraw.replace('\x00', '')  # strip nulls (shouldn't be)
    line = line.rstrip('\n')            # strip EOL

    if PrintTimes:
        print_time('Elapsed time for readline: ',at0)
    return line

def check_response(resp):
    """
    This does a BCC check--not implemented
    here for form--returns True
    
    """
    
    # check+ret = False
    # # TODO add error checking
    # if len(line) < 1:     # timeout --len = 1
    #     print(f"short/timeout; line = {line}, length = {len(line)}")
    #     return "AWOL"
    # if len(line) > 1:   # why 1 vs 2 --- throw out excess \n
    #     goodline = (len(line) > 2) and (line[0] != '/')
    # > 2 because AOK + \n is expected from Station
    return True


def GetNewbie():
    #    print ("Start GetNewbie")
    if len(open(StaDict_lcl).readlines()) == 1:
        # "first dict entry--no search")
        return "Newbie_1"   # only called if "newbie", this is first entry

    i = 1
    max = 5   # only allows 5 named "Newbie_N"
    # TODO figure out why "max"
    foundentry = True
    while(i <= max) and (foundentry):
        StaAdrX = "Newbie_" + str(i)

        with open(StaDict_lcl) as csvfile:
            reader = csv.DictReader(csvfile)
            foundentry = False
            # print ("got here in newbie")
            # print ("searching for " + StaAdrX)
            for row in reader:
                if row['Station_Name_Old'] == StaAdrX:  # already used
                    foundentry = True
            i += 1
    return StaAdrX


def ReplaceInFile(FilePath, Old, New):
    """
    Goes through file at FilePath, line by line, and replaces any occurencs of
    string Old with string New.  It creates new file temp--copies
    over with changes.  Then removes (os.remove) FilePath and renames temp
    to FilePath
    """
    fin = open(FilePath)
    fout = open("temp.txt", "wt")
    for line in fin:
        fout.write(line.replace(Old, New))
    fin.close()
    fout.close()
    os.remove(FilePath)
    os.rename("temp.txt", FilePath)
#    os.remove("temp.txt")


def tellStation(COM, dictentry, alrmmin):
    """
    Unit thinks its address is curAdr; this function tells the Unit
    its new address is NewAdr.  It also gives the Unit current time and
    time to send next report

    Example:
    "Newbie, Newbie_1, Oct 25 2017 18:35:33,Oct 25 2017 18:35:43, BCC"
    Station Responds with normal report, but uses NewAdr = Newbie_1
    This function waits for response before updating local version of
    UnitDirectory.  DB UnitDirectory updated after response
    Returns True if successful (Station responds with correct address)
    False if not.  If

    UNIT_DIRECTORY_HDGS = ["Station_Name_Old", "Station_Name_New", "Snsr0_Nm",
                   "Snsr1_Nm", "Snsr2_Nm", "Snsr3_Nm", "SnsrRef_Nm", "Temp_Nm"]
    """
    t0 = time.time()  # for timing (move this inside
    ret_aok = False
    CurAdr = dictentry['Station_Name_Old']
    NewAdr = dictentry['Station_Name_New']
    now = datetime.now()
    arpt = (Decimal(dictentry['Report H.h']) * 60)
    arpt = int(round(arpt))  # should go to nearest
    strnow = now.strftime("%b %d %Y %H:%M")
    alarm = now + timedelta(minutes=arpt)
    stralarm = alarm.strftime("%b %d %Y %H:%M")
    outstr = f'{CurAdr},{NewAdr},{strnow},{stralarm},0\r'  # make a byte str
    if PrintVerbose:
        print(f"Tell the Field Unit: {outstr}")

    ser_wrt(COM, outstr)  
    # if Station responds AOK, update
    
    StaResp = get_unit_response(COM, 50)    # sb "AOK"; "AWOL" if no response
    if PrintVerbose:
        print(f"Unit TellStation RAW Response is {StaResp}")
    StaResp = StaResp.split(';')[0]
    if StaResp == "AOK":
        if CurAdr != NewAdr:
# TODO !!!!. This isn't going to update file.  Need to write new file
# TODO !!!! line by line.
            dictentry['Station_Name_Old'] = dictentry['Station_Name_New']
            print(f" Station Name changed from {CurAdr} to {NewAdr}")
        if PrintVerbose:
            with open(StaDict_lcl) as fo:
                for line in fo:
                    print(f'current unit directory: {line}')
        upload_file(StaDict_lcl, StaDict_db)
        ret_aok = True
    
    if PrintTimes:
        print(f'tell_station elapsed time = {time.time() - t0}')

    return ret_aok

def get_directory_line(unit_report):

    """
    unit_report is data from Unit, massaged for comments, nulls, etc.
        --return from get_unit_response(...)
    checks UnitDirectory_lcl for reporting unit ID
    if not there and OldUnitID != "Newbie" creates an entry
        (note this is kind of weird--an already configured Unit is being added)
    if Unit_ID = "Newbie", calls getnewbie #TODO--rename for a "Newbie_N"
        --adds entry for Newbie_N
    all this is to UnitDirectory_lcl; Dropbox is updated asychronously.

    """
    # At program init, this StaDict was formed.
    # what we want is the address of the unit reporting
    linelist = unit_report.split(',')   # now a list split by ','
    UnitAdr = linelist[UNIT_RESP_HDGS.index('StaID')]   # sb[0]
    entryfound = False
    # if PrintVerbose:
    #     print(f'get_directory_line: unit adr = {UnitAdr} ')

    with open(StaDict_lcl) as fr:   #job is to find if StaAdr has an entry
        unitdictreader = DictReader(fr)
        for line in unitdictreader:
            if line['Station_Name_Old'] == UnitAdr:
                entryfound = True
                unitdictline = line
                # if PrintVerbose:
                #     print(f'get_directory_line:dir entry for {UnitAdr} = {line}')
            # found the
# There is never a "Newbie" in the Dict.  Need to find the next Newbie_N
    if not entryfound:  # ???? not in dict,make new entry (file also?)
        if UnitAdr == "Newbie":
            UnitAdr = GetNewbie()
        with open(StaDict_lcl, "a+") as fo:
            directorystr = (f'{UnitAdr},{UnitAdr},Snsr0_Nm,Snsr1_Nm,Snsr2_Nm,'
                            f'Snsr3_Nm,SnsrRef_Nm,Temp_Nm,{AlarmDelay},3,7,30,360')
            fo.write(directorystr)  #append
# have dictionary entry, new or created
# cannot update files until Station has been told and responded.
            unitdictline = dict(zip(UNIT_DIRECTORY_HDGS, directorystr.split(',')))
            upload_file(StaDict_lcl, StaDict_db)     # upload it to DB
            
    return unitdictline   #dictionary line out of UnitDirectory



def make_data_file(dictline):
    """ make_data_file(dictline) checks for/creates local/db files named for entry
    # first, checks for local file named for Station Old--s.b. same as Station
    New.  If doesn't exist, make a local and db file of that name +.txt
    returns a list with 'old', 'new' names

    StaDict has been updated already all to do is make datafile
    if dict[0] != dict[1], rename file to dict[0] name
    UNIT_DIRECTORY_HDGS = ["Station_Name_Old", "Station_Name_New", "Snsr0_Nm", "Snsr1_Nm",
               "Snsr2_Nm", "Snsr3_Nm", "SnsrRef_Nm", "Temp_Nm"]
    The Master Dictionay file is called FieldUnitList.  It is stored locally as
    FieldUnitList_lcl and on Dropbox as FieldUnitList_DB.
    """
    filenm = dictline['Station_Name_Old'] + '.txt'

    if os.path.exists(filenm):
        # if this is first time, filenm doesn't exist
        if PrintVerbose:
            print(f'filename {filenm} exists')
        if dictline['Station_Name_Old'] != dictline['Station_Name_New']:
            # have had a name station change
            oldnm = dictline['Station_Name_Old'] + '.txt'
            newnm = dictline['Station_Name_New'] + '.txt'
            print(f'copy from {oldnm} to {newnm}')
        # adding exception handling
            try:
                copyfile(oldnm, newnm)
                # TODO copy entire entry--preserve names
                dictline['Station_Name_Old'] = dictline['Station_Name_New']
                print('copied....')
                return newnm
            except IOError as e:
                print("Unable to copy file. %s" % e)
                return "Error"
#                exit(1)
        else:   #they are equal
            return filenm

    else:   # no data file exists.

        with open(filenm, "w") as fo:     # creates and opens
            fo.write(','.join(DATA_FILE_HDGS) + '\n')
#        fo.write("Station, DateTime, Ohms0, Ohms1, Ohms2, Ohms3," +
#                 " OhmsRef, Vbat, Temp\n")
        # fo.close()
            print(f"file {filenm}  created & header written")
        return filenm  # done--created new data file



@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))
        return


def make_resp_dict(line):
    """ takes string line splits into list on ','
        zips with StaHdsDict
        UNIT_RESP_HDGS = ['StaID', 'Sns0', 'Sns1', 'Sns2', 'Sns3',
        'SnsRef', 'Vbat', 'Temp']
        to make dict with values
    """
    linelist = line.split(',')
    return dict(zip(UNIT_RESP_HDGS, linelist))

def ohms_adj(slist, tfact, toff):
    """
    slist is station response split on ','
    uses Ohms0, Ohms1... to create OhmsAdj0, OhmsAdj1...
    uses data_f_hdg_index
    returns expanded list
     Line0 = [float(i[col])/(1+tfact*(toff-float(i[tcol])))
             for i in data[1::]]
    """
    temp = slist[data_file_hdg_index['Temp']]

    for oi in range (data_file_hdg_index['Ohms0'], (data_file_hdg_index['Ohms3']+1)):
        slist[oi] = str(int(float(slist[oi])/(1+tfact*(toff-float(temp)))))
    return slist
        

def make_data_file_entry(unit_resp, unitdict,unit_aok):
    """
    unit_resp is the response from the unit--a string
    unitdict is the line from the directory--need it for station name
    unit_aok--if the unit responded AOK to the name change request,
    change name in data file.
    this function creates the data file entry.  With ohms adj
    (future millibars???)
    """
# data_f_hdg_index = {'Station': 0, 'DateTime': 1, 'Ohms0': 2, 'Ohms1': 3,
# 'Ohms2': 4, 'Ohms3': 5, 'OhmsRef': 6, 'OhmsAdj0': 7, 'OhmsAdj1': 8,
# 'OhmsAdj2': 9, 'OhmsAdj3': 10, 'Vbat': 11, 'Temp': 12}
    tfact = .064     # temperature offset factor
    toff = 23
    newlist = []
    for i, ent in enumerate(DATA_FILE_HDGS):
        newlist.append(0)    #make a dummy entry
    linelist = unit_resp.split(',')
    if unit_aok == 'AOK':
        linelist[data_file_hdg_index['Station']] = \
        unitdict['Station_Name_Old']
        # only if unit reported 'AOK'
    linelist.insert(data_file_hdg_index['DateTime'], get_time())
    for i, x in enumerate(linelist):
        newlist[i] = x  # copy in up to Temp.
    oiadj = data_file_hdg_index['OhmsAdj0']
    for oi in range(data_file_hdg_index['Ohms0'], (data_file_hdg_index['Ohms3'] +1)):
        adjohms = float(linelist[oi])/ \
        (1+tfact*(toff-float(linelist[data_file_hdg_index['Temp']])))
        newlist[oiadj] = str(int(adjohms))
        oiadj = oiadj+1

    return newlist


# ==========================
    return  # return something?


def make_hdgs_dict(hdgs_list):
    """
    hdgs_list is of the form ['abc','def','ghi',....]
    returns the dictionary of the form
    rdict = {[abc:0],[def:1], ....}
    enabling the access of the def element as rdict['def']
    DID WE JUST START A REINVENT OF THE .csv MODULE?

    """""
    rdict = {}
    for i, ent in enumerate(hdgs_list):
        rdict[ent] = i

    return rdict

def main():
    comlist = serial_ports()
    global COM    # make it available outside
    with serial.Serial(comlist[0], 9600) as ser:
        COM = ser.port   # this is a readback of comlist[0]
    print(f'Hello, World! ; System Platform = {sys.platform}')
    print(f'Connected to {COM} @ {get_time()}\n')  # COM was global defined at init

    global data_file_hdg_index
    data_file_hdg_index = make_hdgs_dict(DATA_FILE_HDGS)
    #print (f' data file headings dictionary = {data_file_hdg_index}')
    global unit_dir_hdg_index     # TODO used???
    unit_dir_hdg_index = make_hdgs_dict(UNIT_DIRECTORY_HDGS)
    #print (f' unit directory index = {unit_dir_hdg_index}')
    
    hdglen =len(UNIT_RESP_HDGS)

    make_unitdirectory(StaDict_lcl, StaDict_db)
    # in case there is none
    # only time called.

    while 1:

        # only good line here is one with len = len Hdgs--s.b above
        unit_aok = False
        good_response = False
        while not unit_aok:
            while not good_response:
                unit_resp = get_unit_response(COM, None)  
                if (len(unit_resp.split(',')) == hdglen):
                    good_response = check_response(unit_resp)   # various checks
                elif(PrintVerbose):
                    print(f'discarded comment/out of order = {unit_resp} ')

            # as of here, we have a good unit data stream
            download_file(StaDict_lcl, StaDict_db)  
            # TODO--make this asynch. Station is hung up dring download TODO
    
            dictline = get_directory_line(unit_resp) 
            # dict line = dictionary line UnitDir
            unit_aok = tellStation(COM, dictline, AlarmDelay)
            # tellStation updates StaDict_lcl ONLY if Station says AOK
            # chks for/creates local/db files entry
            # returns True if good response        
        # as of here, we got a good Unit transmission, Unit acknowledged
        # time update, alarm time, etc. Name change, if any
        # unit should be back asleep
        
        lcl_dat_f_nm = make_data_file(dictline) 
        # returns file name for data--makes if new, copies if changed
        # TODO -check out deleting old files locally.
        
        # new_data_list = make_data_file_entry(unit_resp, dictline, unit_aok)
               
        linelist = unit_resp.split(',')        
        linelist.insert(data_file_hdg_index['DateTime'], get_time())
        with open(lcl_dat_f_nm, "a+") as fo:
            line = ",".join(linelist) + '\n'    # print (line)
            print(f'data entered in file {lcl_dat_f_nm} : {line}', end='')
            fo.write(line)
    # have to reset line ptr to zero to count lines??
        if PrintVerbose:
            with open(lcl_dat_f_nm, 'r') as fo:
                data_file_len = len(fo.readlines())
                print(f'            ****break for readability--not in file;'
                      f'file length = {data_file_len}  *********\n')



        upload_file(lcl_dat_f_nm, ("/" + lcl_dat_f_nm))  # store raw data?
# plotSM('Ohms'.dictline,lcl_dat_f_nm)
# 'Ohms' can be "Ohms', 'Ohms_adj',
        rpts = ['Rpt%s' % str(i) for i in range(1, 10)]   # 10 possible report times.
        for rindex in UNIT_DIRECTORY_HDGS:
            # print(f'Unit Heading ={rindex}')
            if rindex in rpts:
                rpt_tm = dictline[rindex]
                # print(f'found {rindex} , value = {rpt_tm}')
                if rpt_tm not in NO_PLOT_LIST:
                 #   with open (lcl_dat_f_nm, 'r') as fr:

                    trimfile(lcl_dat_f_nm,int(rpt_tm))  # creates trimfile.csv
                    # print(f'ftrim created for {rpt_tm} days')
        plt.close('all')
# TODO  rework or new function to adjust raw ohms, change trimfile header
# so that plot just plots the headers???

        # plotSM("Ohms", dictline, lcl_dat_f_nm,
        #        lcl_dat_f_nm.split('.')[0], 3)    # stores in locally
        # TODO dictline and localfile have everything necessary except Title ("Ohms") for plot
    return   # proforma return.  Never executes


if __name__ == '__main__':
    # see http://ibiblio.org/g2swap/byteofpython/read/module-name.html

    main()
