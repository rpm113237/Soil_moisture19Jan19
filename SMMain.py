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
# from pandas import DataFrame, read_csv
import numpy as np
import pandas as pd
# import fileinput
import dropbox
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
# from matplotlib import ticker as ticker
# from csv import reader
# from csv import DictReader
# from dateutil import parser
# from dateutil import relativedelta
# import calendar

import contextlib
from decimal import Decimal
# import fileinput
import csv
from shutil import copyfile
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
# HeadingsDict = {"Time": 1, "Vbat": 7, "Temp": 8}
# current, change when format changes.

UNIT_RESP_HDGS = ['StaID', 'Sns0', 'Sns1', 'Sns2', 'Sns3',
                  'SnsRef', 'Vbat', 'Temp']

# to make dict out of Station Response

DATA_FILE_HDGS = ['Station', 'DateTime', 'Ohms0', 'Ohms1', 'Ohms2',
                  'Ohms3', 'OhmsRef', 'Vbat', 'Temp']
NO_PLOT_LIST = ['', ' ', 'None', '0', 'No', 'NO']
PLOT_OHMS = False
PLOT_OHMS_ADJ = True

AlmMin = 2  # alrm delay in minutes
# TODO alarm Delay in hours--later read from DB File
dflt_alarm_delay = round(Decimal(AlmMin / 60), 3)
PrintTimes = False
PrintVerbose = False

TFACT = .064     # temperature offset factor
TOFF = 23

def to_do_s():

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
    #if PrintTimes:
    # print_time(f'Time to upload {lcl_f}', at0)
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
    #if PrintTimes:
    print_time(f'Time to download {db_f}', at0)
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


def mx_b(rx, rl, rh, bar_l, bar_h):
    # //note r0, r1 in ohms, bar1, bar0 in actual Bar *10
    # //also used for the Delm calc--which has neg slope
    if rx > rh:
        retval = 0
    else:
        denom = rh - rl
    if denom == 0:
        denom = 1  # //shouldn't happen
    if bar_h >= bar_l:
        retval = ((bar_h - bar_l) * (rx - rl)) / denom + bar_l
    num = bar_h - bar_l
    if bar_h < bar_l:
        retval = bar_l - (((bar_l - bar_h) * (rx - rl)) / denom)
    #    num = (bar_l-bar_h)

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


def trimfile(f, xdays, dictline):
    """
    finds the last time stamp in file f (the master file)
    returns a file ftrim that starts xdays before the last time stamp, ends
    with last time stamp.
    if there is no timestamp xdays back, returns the entire file f
    trimfile is a working file.  Not archived.  The master file (f)
    is the only one archived
    :param dictline:

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
    last_temp = df.at[df_len, 'Temp']
    xdays_act = xdt_act.days + math.ceil(xdt_act.seconds / (3600 * 24))

    file_nm_base = df.at[df_len,'Station']
    titleTmStamp = f'{last_time}  {last_temp}(C) {last_vbat}V'
    titleID = f'{file_nm_base} (last {xdays} days)'

    # from matplotlib import rcParams
    # rcParams.update({'figure.autolayout': True})

    fig, ax1 = plt.subplots()
    ax1.set_xlabel(titleTmStamp, color="red", fontsize=12, weight="bold")
    # ax1.set_ylabel(YaxisDict[Param], color="black")

    # TODO--this only works for ohms; need to have an ohms adjust?
    # TODO--make an Ohms adjust routine.  Keep raw and adjusted?
    plt.title(titleID, fontsize=12, weight="bold", color="red")

    # gca stands for 'get current axis'
    plt.style.use('fivethirtyeight')
    ax1 = plt.gca()
    # ax1.set_xlabel(titleTmStamp, color="orange")
    ltp = [dictline['Snsr0_Nm'], dictline['Snsr1_Nm'], dictline['Snsr2_Nm'],  # ltp = labels to plot
           dictline['Snsr3_Nm'], dictline['Temp_Nm']]   # easier typing
    if PLOT_OHMS_ADJ:
        pst = time.time()
        df['adj_0'] = df.apply(lambda x: ohms_adj(x.Ohms0, x.Temp, TFACT, TOFF), axis=1)
        df['adj_1'] = df.apply(lambda x: ohms_adj(x.Ohms1, x.Temp, TFACT, TOFF), axis=1)
        df['adj_2'] = df.apply(lambda x: ohms_adj(x.Ohms2, x.Temp, TFACT, TOFF), axis=1)
        df['adj_3'] = df.apply(lambda x: ohms_adj(x.Ohms3, x.Temp, TFACT, TOFF), axis=1)
        df.rename({'adj_0': ltp[0], 'adj_1': ltp[1], 'adj_2': ltp[2], 'adj_3': ltp[3], 'Temp': ltp[4]},
                  axis=1, inplace=True)
        ax1.set_ylabel('Ohms(C)', color="Red", weight='bold')
        num_entries = len(df.index)
        # print_time(f"time to calc temp adjustments for {num_entries} entries (X4)", pst)
    else:
        df.rename({'Ohms0': ltp[0], 'Ohms1': ltp[1], 'Ohms2': ltp[2], 'Ohms3': ltp[3], 'Temp': ltp[4]},
                  axis=1, inplace=True)
        ax1.set_ylabel('Ohms', color="black", weight='bold')



    for ltag in ltp[0:4]:   # doesn't include end pt
        if ltag not in NO_PLOT_LIST:
            # print(f'column to be plotted {ltag}')
            df.plot(kind='line', x='dt_tm', y=ltag, ax=ax1)

    ax1.set_xlabel(titleTmStamp)

    ax2 = ax1.twinx()
    ax2.set_ylabel('Temp(C)', color="magenta", weight='bold')

    plt.yticks(fontsize=12, color="magenta")
    df.plot(kind='line', x='dt_tm', y=ltp[4], color='magenta', ax=ax2)
    ax1.set_yticks(calculate_ticks(ax1, 10))
    ax2.set_yticks(calculate_ticks(ax2, 10))
    ax1.legend(loc=2, prop={'size': 8})
    ax2.legend(loc=1, prop={"size": 8})

    # plt.show()
    # time.sleep(10)

    lcl_pdf_file = file_nm_base + "_" + str(xdays) + ".pdf"
    db_pdf_file = "/" + lcl_pdf_file

    plt.savefig(lcl_pdf_file, facecolor="b", transparent=False,
                bbox_inches="tight")

    upload_file(lcl_pdf_file, db_pdf_file)

    # plt.close('all')

    # TODO--use trim days or actual for file name?
    # TODO If trimfile sees it already exists, don't make it
    # TODO don't plot it.  plot has to remove the file after plot
    # trimfile is local--if uploaded, for visibility only. db trim file is
    # don't upload trim fle.

    return "ftrim.csv"

def calculate_ticks(ax, ticks, round_to=0.1, center=False):
    upperbound = np.ceil(ax.get_ybound()[1]/round_to)
    lowerbound = np.floor(ax.get_ybound()[0]/round_to)
    dy = upperbound - lowerbound
    fit = np.floor(dy/(ticks - 1)) + 1
    dy_new = (ticks - 1)*fit
    if center:
        offset = np.floor((dy_new - dy)/2)
        lowerbound = lowerbound - offset
    # TODO diddle this so it becomes a multiple of 1,2,5
    values = np.linspace(lowerbound, lowerbound + dy_new, ticks)
    return values*round_to

def ser_wrt(Com, wrtstr):
    '''
    write wrtstr to Com"
    has character by character delay--poor way to avoid overrun on FM
    transmitters.

    '''
    # TODO-- figure out transmitter delay issue.
    at0 = time.time()
    try:
        ser = serial.Serial(Com, baudrate=9600, timeout=None)
    except serial.SerialException as e:
        print(f"could not open serial port '{Com}': {e}")
        return False
    # if PrintVerbose:
    print(f'Sent to Unit; {wrtstr}')
    wrtlist = list(wrtstr)
    for num, char in enumerate(wrtlist):
        ser.write(char.encode())

        # time.sleep(.015)    # TODO 15ms delay??

    ser.close()
    # print_time('time for write to unit:', at0)
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

    at0 = time.time()
    line = []
    first_rd_tm = 0  # Global for tracking unit awake time.
    eol_f = False
    comment = False     # assume not a comment (starts w '//')
    while not comment:
        while not eol_f:
            for c in ser.read():
                if first_rd_tm == 0:
                    first_rd_tm = time.time()
                # x = chr(c)
                # print (f'c= {c}; chr c = {x}')
                if c in range(20,127):    #drop out unprintables
                    line.append(chr(c))
                if c in ['\n', 0X0A, 0X0D]:
                    eol_f = True
        # have an eol.  Is it a comment??
        if line[0]=='/':
            eol_f = False   # start over
            print(f'comment line = {"".join(line)}\n')
            first_rd_tm = 0
            line = []
        else:
            comment = True  # break out
    ser.close()
    last_rd_tm = time.time()
    num_chars = len(line)
    line = ''.join(line)
    tot_tm = last_rd_tm-first_rd_tm
    # if PrintTimes:
    # print_time(f'read {len(line)} characters in ', first_rd_tm)
    print(f'Unit sent: {line}')
    return {'first_char_tm': first_rd_tm, 'total_rd_tm': tot_tm, 'rd_line': line}
    # TODO--have to work out how we stick BCC in
    # probably with ESC


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
    max_newbie = 15   # only allows 15 named "Newbie_N"
    foundentry = True
    while(i <= max_newbie) and foundentry:
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
    arpt = float(dictentry['Report H.h']) * 60
    arpt = int(round(arpt))  # should go to nearest
    strnow = now.strftime("%b %d %Y %H:%M")
    alarm = now + timedelta(minutes=arpt)
    stralarm = alarm.strftime("%b %d %Y %H:%M")
    outstr = f'{CurAdr},{NewAdr},{strnow},{stralarm},0\r'  # make a byte str
    ser_wrt(COM, outstr)
    # if Station responds AOK, update
    sr_dict = get_unit_response(COM, 50)    # sb "AOK"; "AWOL" if no response
    StaResp = sr_dict['rd_line']
# return {'first_char_tm': first_rd_tm, 'total_rd_tm': tot_tm, 'rd_line': line}
    if PrintVerbose:
        print(f"Unit TellStation RAW Response is {StaResp}")
    StaResp = StaResp.split(';')[0]
    unit_end_tm = time.time()
    if StaResp == "AOK":
        unit_end_tm = time.time()
        # if = AOK, cupdate old name to new name, even if no change.
        df = pd.read_csv(StaDict_lcl)
        tst = df.Station_Name_Old == CurAdr     # find index of CurAdr
        tl = df.index[tst].tolist()
        # tl is list with all indices matching CurAdr. s.b len = 1 (exactly)
        if not (len(tl) == 1):  # has to be exactly one
            print(f'Missing or duplicate station name {CurAdr}.  Should not happen ')
            print(f'total {len(tl)} entires, should be exactly one')

        # print(f'{CurAdr} index is {tl[0]}')
        if CurAdr != NewAdr:
            dfdict = df.to_dict()   # dictionary of dictionaries
            dfdict['Station_Name_Old'][tl[0]] = dfdict['Station_Name_New'][tl[0]]
            df = df.from_dict(dfdict)
            df.to_csv(StaDict_lcl, encoding='utf-8', index=False)
            upload_file(StaDict_lcl, StaDict_db)
            # not a problem here--Unit went to sleep with "AOK"
        ret_aok = True
    
    if PrintTimes:
        print(f'tell_station elapsed time = {time.time() - t0}')

    return unit_end_tm, ret_aok

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
    # pandas
    # my_dict = {row[0]: row[1] for row in df.values}

    linelist = unit_report.split(',')   # now a list split by ','
    UnitAdr = linelist[UNIT_RESP_HDGS.index('StaID')]   # sb[0]
    entryfound = False
    df = pd.read_csv(StaDict_lcl)
    # dfdict = df.to_dict()
    tst = (df.Station_Name_Old == UnitAdr)  # find index of CurAdr
    tlst = df.index[tst].tolist()
    # tlst has list of entries--if 0, no entry, if one, entry exists

    if len(tlst) == 1:  # Already here, get the dict for return
        dictline = dict(zip(UNIT_DIRECTORY_HDGS,df.loc[tlst[0]]))
        # no change necessary

    if len(tlst) == 0:  # New (to us)
        if UnitAdr == "Newbie":
            UnitAdr = GetNewbie()
        directorystr = (f'{UnitAdr},{UnitAdr},One ft,Two_ft,Three_ft,'
                        f'48 inches,SnsrRef_Nm,Temp_Nm,{dflt_alarm_delay},3,7,30,360')
        dictline = dict(zip(UNIT_DIRECTORY_HDGS, directorystr.split(',')))
        df.loc[len(df)] = dictline
        df.to_csv(StaDict_lcl, index=False)
        upload_file(StaDict_lcl, StaDict_db)
        # don't upload here--tell station does that.  requires AOK from unit
        # TODO ??????--if created new entry, must upload?????

    return dictline   #dictionary line out of UnitDirectory



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

def ohms_adj(ohms, temp, tfact, toff):
    """

    """
    ohms_adj = int(float(ohms)/(1 + float(tfact*(toff -temp))))

    return ohms_adj

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
    global first_rd_tm  # to keep track of station awake time.
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

        while not unit_aok:     #waiting for data
            while not good_response:
                resp_dict = get_unit_response(COM, None)
                unit_resp = resp_dict['rd_line']
                start_unit_timer = resp_dict['first_char_tm']
            # return {'first_char_tm': first_rd_tm, 'total_rd_tm': tot_tm, 'rd_line': line}
                if len(unit_resp.split(',')) == hdglen:
                    good_response = check_response(resp_dict['rd_line'])   # various checks
                elif PrintVerbose:
                    print(f'discarded comment/out of order = {unit_resp} ')

            # as of here, we have a good unit data stream
            # download_file(StaDict_lcl, StaDict_db)
            # TODO--make this asynch. Station is hung up dring download TODO
    
            dictline = get_directory_line(unit_resp)
            # print_time('awake after get directory_line',start_unit_timer)
            # dict line = dictionary line UnitDir
            unit_dn_tm, unit_aok = tellStation(COM, dictline, dflt_alarm_delay)
            print(f'Unit was awake {unit_dn_tm - start_unit_timer} ')
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
        linelist.insert(DATA_FILE_HDGS.index('DateTime'), get_time())
        line = ",".join(linelist) + '\n'  # print (line)
        with open(lcl_dat_f_nm, "a+") as fo:
            # line = ",".join(linelist) + '\n'    # print (line)
            fo.write(line)
        with open(lcl_dat_f_nm) as f:   # no clever way to count lines
            for d_f_l, l in enumerate(f):
                pass
        fsize = os.stat(lcl_dat_f_nm)
        bsize = fsize.st_size.__str__()
        print(f'data file entry: {lcl_dat_f_nm} ({bsize} bytes/{d_f_l + 1}lines) : {line}', end='')

        upload_file(lcl_dat_f_nm, ("/" + lcl_dat_f_nm))  # store raw data?
        # TODO make a folder on dropbox for data.  Never downloaded
        rpts = ['Rpt%s' % str(i) for i in range(1, 10)]   # 10 possible report times.
        for rindex in UNIT_DIRECTORY_HDGS:
            if rindex in rpts:
                rpt_tm = dictline[rindex]
                if rpt_tm not in NO_PLOT_LIST:
                    trimfile(lcl_dat_f_nm, int(rpt_tm), dictline)  # creates trimfile.csv

        plt.close('all')
        download_file(StaDict_lcl, StaDict_db)  # not while station awake. Consequence:
        # most of time, change won't take place until NEXT response
        print_time(f'Total time for whole McGillicuddy = ', start_unit_timer)
        print(f'\n')
# TODO  rework or new function to adjust raw ohms, change trimfile header
# so that plot just plots the headers???

        # plotSM("Ohms", dictline, lcl_dat_f_nm,
        #        lcl_dat_f_nm.split('.')[0], 3)    # stores in locally
        # TODO dictline and localfile have everything necessary except Title ("Ohms") for plot
    return   # proforma return.  Never executes


if __name__ == '__main__':
    # see http://ibiblio.org/g2swap/byteofpython/read/module-name.html

    main()
