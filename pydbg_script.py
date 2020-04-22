from pydbg import *
from pydbg.defines import *
import sys
import os
import thread
from threading import Timer
import time
import msvcrt
try:
	import config
	program = config.IMAGE
	prog_args = config.ARGS
	log_dir = config.LOG_DIR
except:
	print "using command line..."
	if (len(sys.argv) < 4):
		print("PYDBG: USAGE: " + sys.argv[0] + " <prog> <args> <ldir>")
		sys.exit()
	program = sys.argv[1]
	prog_args = sys.argv[2]
	# timeout = float(sys.argv[3])
	log_dir = sys.argv[3]
	pass

def log_crash(pydbg, eip_str, disass, context):
	if not os.path.exists(log_dir):
		os.makedirs(log_dir)
	eip_log = "%s\\%s" % (log_dir, "eip_" + eip_str + ".log")
	f = open(eip_log, 'w')
	f.write("-----------------------------\n")
	f.write("        CRASH MODULE\n")
	f.write("-----------------------------\n")
	exec_module = pydbg.addr_to_module(int(eip_str, 16))
	if exec_module:
		f.write("PATH='"+exec_module.szExePath+"'\n")
		f.write("BASE='"+hex(exec_module.modBaseAddr)+"'\n")
		f.write("OFFSET='"+hex(int(eip_str, 16) - exec_module.modBaseAddr)+"'\n")
	else:
		f.write("UNKNOWN!!\n")
	f.write("-----------------------------\n")
	f.write("        CRASH CONTEXT\n")
	f.write("-----------------------------\n")
	f.write(context + "\n\n")
	f.write("-----------------------------\n")
	f.write("          DIASSEMBLY\n")
	f.write("-----------------------------\n")
	for tuple in disass:
		address, instr = tuple
		f.write(hex(int(address, 16)) + "    " + instr + "\n")
	f.close()

def av_handler(pydbg):
	#if dbg.dbg.u.Exception.dwFirstChance:
		#return DBG_EXCEPTION_NOT_HANDLED
	disass = pydbg.disasm_around(pydbg.context.Eip, 5)
	context = pydbg.dump_context()
	eip_str = hex(pydbg.context.Eip)
	eip_str = eip_str.replace("L", "").replace("0x", "").lower()
	print("PYDBG: [+] access violation! (crash!) eip: %s" % (eip_str))
	log_crash(pydbg, eip_str, disass, context)
	pydbg.terminate_process(1)
	return DBG_EXCEPTION_NOT_HANDLED

def process_terminated_handler(pydbg):
	print("PYDBG: [+] process was terminated")
	return DBG_CONTINUE

def program_started_handler(pydbg):
	#if pydbg.first_breakpoint:
	# print("[+] adding breakpoints")
	# pydbg.set_callback(EXCEPTION_ACCESS_VIOLATION, av_handler)
	# pydbg.set_callback(EXIT_PROCESS_DEBUG_EVENT, process_terminated_handler)
	return DBG_CONTINUE

def check_for_remote_kill():
	global already_terminated
	global dbg
	global want_to_die

	total_input = ""
	while not want_to_die and not sys.__stdin__.closed:
		try:
			total_input += sys.__stdin__.readline()
		except EOFError:
			total_input += ""

		if total_input.find("KILL") != -1 and not already_terminated:
			print("PYDBG: [+] Received piped KILL command, terminating process")
			dbg.terminate_process(1)
			already_terminated = True

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

dbg = pydbg()
#dbg.set_callback(EXCEPTION_BREAKPOINT, program_started_handler)
print("PYDBG: [+] loading: " + program + " with " + prog_args)
# dbg.load(program)
# os.system("\"" + program + "\" \"" + prog_args + "\"")
#dbg.set_callback(EXCEPTION_ACCESS_VIOLATION, av_handler)
#dbg.set_callback(EXIT_PROCESS_DEBUG_EVENT, process_terminated_handler)
#dbg.load("soffice", "test.ods")

dbg.load(program, prog_args)
dbg.set_callback(EXCEPTION_ACCESS_VIOLATION, av_handler)
dbg.set_callback(EXIT_PROCESS_DEBUG_EVENT, process_terminated_handler)

already_terminated = False
want_to_die = False
thread.start_new_thread(check_for_remote_kill, ())

print("PYDBG: [+] starting program " + os.path.basename(program))
dbg.run()
want_to_die = True

print("PYDBG: [+] DONE! running program")
