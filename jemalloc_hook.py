#!/usr/bin/env python
"""
Hook on mozglue.malloc/free
"""

DESC = """Hook on mozglue.malloc/mozglue.free and display information """
import immlib
from immlib import LogBpHook
import getopt
import struct

# mozglue.malloc Hook class
ALLOCLABEL = "mozglue.malloc + 0x41"
class RtlAllocateHeapHook(LogBpHook):
    def __init__(self):
        LogBpHook.__init__(self)
        
    def run(self,regs):
        """This will be executed when hooktype happens"""
        imm = immlib.Debugger()
        readaddr=""
        size=""
        
        res=imm.readMemory( regs['ESP'] , 0x8)
        if len(res) != 0x8:
            imm.log("mozglue.malloc: ESP seems to broken, unable to get args")
            return 0x0
        (loc, size) = struct.unpack("LL", res)
        ptr = imm.getRegs()['EAX']
        if ptr < 0x1000:
            imm.pause()
            return 0x00
        imm.log("mozglue.malloc(from=0x%08x, size=0x%08x, ptr=0x%08x)" % (loc, size, ptr))        

# mozglue.free Hook class
FREELABEL = "mozglue.free"
class RtlFreeHeapHook(LogBpHook):
    def __init__(self):
        LogBpHook.__init__(self)
        
    def run(self,regs):
        """This will be executed when hooktype happens"""
        imm = immlib.Debugger()
        readaddr=""
        size=""
        
        res=imm.readMemory( regs['ESP'] , 0x8)
        if len(res) != 0x8:
            imm.log("mozglue.free: ESP seems to broken, unable to get args")
            return 0x0
        (loc, block) = struct.unpack("LL", res)
        imm.log("mozglue.free(from=0x%08x, ptr=0x%08x)" % (loc, block))        
            
            
def usage(imm):
    imm.log("!jemalloc_hook     Hook on mozglue.malloc/free and display information")
    imm.log("-a             Hook on mozglue.malloc")
    imm.log("-f             Hook on mozglue.free")
    imm.log("-u             Disable Hooks")
    
def HookOn(imm, LABEL,  HeapHook, bp_address, Disable):
    hookalloc = imm.getKnowledge( LABEL )
    if Disable:
       if not hookalloc:
           imm.log("Error %s: No hook to disable" % (LABEL))
           return "No %s to disable for heap " % (LABEL)
       else:
           hookalloc.UnHook()
           imm.log("UnHooked %s" % LABEL)
           imm.forgetKnowledge( LABEL )
           imm.deleteBreakpoint(imm.getAddress(LABEL))
           return "%s  heap unhooked" % (LABEL) 
    else:
        if not hookalloc:
            hookalloc= HeapHook()
            hookalloc.add( LABEL , bp_address)
            imm.log("Placed %s" % LABEL)
            imm.addKnowledge( LABEL, hookalloc )
        else:
            imm.log("HookAlloc is already running")
        return "Hooking on mozglue.malloc"
#!/usr/bin/env python
    
def main(args):
    if not args:
        return "No arguments given"

    Disable = False
    AllocFlag = False
    FreeFlag = False
    imm = immlib.Debugger()
    
    try:
        opts, argo = getopt.getopt(args, "h:uaf")
    except getopt.GetoptError:
        imm.setStatusBar("Bad argument %s" % str(args))
        usage(imm)
        return 0
    
    for o,a in opts:
        if o == "-h" :
            try:
                heap = int(a, 16)
            except ValueError, msg:
                return "Invalid heap address: %s" % a
        elif o == "-u" :
            Disable = True
        elif o == "-a":
            AllocFlag = True
        elif o == "-f":
            FreeFlag = True
    
    ret = ""
    if AllocFlag:
        allocaddr = imm.getAddress("mozglue.malloc  + 0x41" )
        ret = "Alloc Hook <%s>" % HookOn(imm, ALLOCLABEL, RtlAllocateHeapHook, allocaddr, Disable)
    if FreeFlag:
        freeaddr = imm.getAddress("mozglue.free" ) 
        if ret:
            ret+= " - "
        ret +="Free Hook <%s>" %  HookOn(imm, FREELABEL, RtlFreeHeapHook, freeaddr, Disable)
    return ret
                            
        
    
    


        
   
    
    
    
    


    
    
