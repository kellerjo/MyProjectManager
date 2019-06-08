#!/usr/bin/env python
import sys
import os
import stat
import yaml
import time
import datetime
from subprocess import call


commands=["new","show","showall","info","quick","setold", "add", "leave", "quit", "open", "t", "edit"]
#templateFP=projDir + "./Templates/"


infoFileName="projInfo.yaml"
projDir=os.environ["MPM_PROJ_DIR"] + "/"
mpm_data_path = os.environ["MPM_DATA_DIR"] + "/mpm_data.yaml"


allProjPathList={}
oldProjPathList={}
activeProjPathList={}
aliasMap={}

tpath=""

def makeConfFile(projN, projD):
    df = open(infoFileName,"w")
    df.write("---\n")
    yaml.dump({"ProjectName" : projN, "ShortProjectDescription" : projD, "CreationDate" : datetime.datetime.now().strftime("%y-%m-%d"), "alias" : [ projN.lower()], "Language" : "Undefined", "ProjectDescription" : "_", "Status" : "Active" },df, default_flow_style=False)
    df.close()

#TODO copy template
def makeQuickstartFile(projN, projPath):
    df = open("quickstart","w")
    df.write("#!/bin/bash\n")
    df.write("tmux attach -t " + projN + " || tmux new-session -s " + projN + " -c " + projPath + projN +  "/\n")
    os.chmod("quickstart",stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
    df.close()

def defaultProjPathList():
    res = []
    for d in os.listdir(projDir):
        if d[0] != '.':
            path= projDir + '/' + d
            if os.path.isfile(path + '/' + infoFileName):
                res.append(path)

def projList():
    res = []
    for d in os.listdir(projDir):
        if d[0] != '.':
            path= projDir + '/' + d + '/' + infoFileName
            if os.path.isfile(path):
                res.append(yaml.load(open(path))['ProjectName'])


    return(res)


def filestr(path):
    df = open(path,"r")
    tmp = df.read()
    df.close()
    return(tmp)

def loadMPMData():
    y = yaml.load(open(mpm_data_path))
    global projDir, projPathList, allProjPathList, activeProjPathList, oldProjPathList, tpath, aliasMap

    #projDir=y['ProjectsFolder']
    tpath=y['t']

    #TODO
    for p in projList():
       projP = projDir + p
       allProjPathList[p] = projP
       if getYAML(p)['Status'] == "Active":
           activeProjPathList[p] = projP
       else:
           oldProjPathList[p] = projP
    if y['Other'] is not None:
        for k,v in y['Other'].items():
           allProjPathList[k] = v
           if getYAML(k)['Status'] == "Active":
               activeProjPathList[k] = v
           else:
               oldProjPathList[k] = v

    for p in allProjPathList:
        y = getYAML(p)
        aliasMap[p] = p
        for a in y['alias']:
            aliasMap[a] = p

def printCommands():
    for t in commands:
        print(t)

def wrongCommand():
    print("Unknown Command, Possible are:")
    printCommands()

def getYAML(pr):
    return(yaml.load(open(allProjPathList[pr] + "/" + infoFileName)))

def allYAMLs(includeOld):
    l=[]
    for pr in allProjPathList:
        l.append(getYAML(pr))
    return(l)

def getProjectName(pAlias):
    if aliasMap.has_key(pAlias):
        return aliasMap[pAlias]
    else:
        print "Project Name '" + pAlias + "' unknown"
        sys.exit(1)


if __name__ == "__main__":

    loadMPMData()

    args = sys.argv
    arg = []
    params = []
    for a in args:
        if a[0] == "-":
            params.append(a[1:].lower())
        arg.append(a)


    if len(arg) == 1:
        wrongCommand()
        exit()

    if arg[1] == "show":
        for y in activeProjPathList:
            print y

    elif arg[1] == "showall":
        for y in allProjPathList:
            print y

    elif arg[1] == "quick" or arg[1] == "j" or arg[1] == "open":
        if len(arg) > 2:
            p=allProjPathList[getProjectName(arg[2])]

            if (os.path.exists(p)):
                os.chdir(p)
                call(["./quickstart"])
            else:
                print("Project does not exist")
        else:
            print "Please give a project name"

    elif arg[1] == "info":
        print("")
        def showProj(d):
            print("")
            print("Name: " + d['ProjectName'])
            print("Desc: " + d['ShortProjectDescription'])
            if 'CreationDate' in d:
                print("Date: " + d['CreationDate'])
            print("")

        if len(arg) > 2:
            projName=getProjectName(arg[2])
            projPath=allProjPathList[getProjectName(arg[2])]
            if not(os.path.exists(projPath)):
                print("Project does not exist")
                sys.exit()

            d = getYAML(projName)
            showProj(d)

        else:
            for d in allYAMLs(False):
                showProj(d)

    elif arg[1] == "setold":
        if len(arg) == 1:
            print("Projectname must be specified")
            sys.exit()
        print "TODO"

    elif arg[1] == "new":
        if len(arg) > 2:
            projName=arg[2]
        else:
            projName=raw_input("Enter project name: ")

        if os.path.exists(projName):
            print("Project already exists")
            sys.exit()

        projDesc=raw_input("Enter short project description: ")

        os.chdir(projDir)
        os.mkdir(projName)
        os.chdir(projName)
        #os.mkdir(projFolderName)
        makeConfFile(projName, projDesc)
        makeQuickstartFile(projName, projDir)

        if params.count("no-git") == 0:
            call(["git", "init"])
            call(["git", "add" , infoFileName])
            call(["git", "commit" , "-m" , "'Initial Commit'"])

    elif arg[1] == "add":

        projName = raw_input("Enter project name: ")
        projDesc=raw_input("Enter short project description: ")

        makeConfFile(projName, projDesc)
        makeQuickstartFile(projName, os.curdir + "/")

        with open(mpm_data_path) as f:
            d = yaml.safe_load(f)

        d['Other'][projName] = os.getcwd() + "/"

        with open(mpm_data_path, 'w') as f:
            yaml.safe_dump(d,f,default_flow_style=False)
            f.close()

    elif arg[1] == "t":
        path = os.getcwd()
        inProj=False
        for p in allProjPathList:
            v = allProjPathList[p]
            if len(v) <= len(path) and v == path[0:len(v)]:
                inProj=True
                tcall = ["python", tpath, "--task-dir", v, "--list", "tasks"]
                for i in range(2,len(arg)):
                    tcall.append(arg[i])
                call(tcall)
                break

        if not inProj:
            print "mpm was not called inside a valid mpm project"

    elif arg[1] == "edit":
        if len(arg) > 2:
            projName=arg[2]
        else:
            print "Please provide a project name"
            sys.exit()

        call(["vim", allProjPathList[getProjectName(projName)] + "/" + infoFileName])

    elif arg[1] == "leave" or arg[1] == "quit" or arg[1] == "q":
        call(["tmux", "detach"])
    else:
        wrongCommand();
