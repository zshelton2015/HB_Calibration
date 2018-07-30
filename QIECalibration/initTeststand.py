import sendCommands
import sys
import os
from textwrap import dedent

def initLinks(uHTRslot = 3,readDelay=192):

    initCommands = dedent("""\
                   clock
                   setup                  
                   3
                   quit
                   link
                   init
                   %i
                   1
                   0
                   quit
                   exit"""% (readDelay))

    with open("uHTRcommands.txt","w") as f:
        f.write(initCommands)

    os.popen("uHTRtool.exe 192.168.41.%d < uHTRcommands.txt" % (uHTRslot*4)).read()


def resetBackplane(rbx = "HB2",port = 64000, host = "cmsnghcal01.fnal.gov"):
    cmds = ["put %s-bkp_pwr_enable 1"%rbx,
            "put %s-bkp_reset 1"%rbx,
            "put %s-bkp_reset 0"%rbx]

    outputs = sendCommands.send_commands(cmds = cmds, script=False, port=port, control_hub=host)

    badOutput = False
    for value in outputs:
        if not "OK" in value["result"]:
            print "Problem with backplane reset"
            badOutput = True

    if badOutput:
        sys.exit(999)



if __name__ == "__main__":
    resetBackplane(rbx = "HB2", port=64000, host="cmsnghcal01.fnal.gov")
    initLinks(uHTRslot=3,readDelay=192)
