#
#Fuzzer specific config stuff...
#
#for ftp 
LOCAL_PORT=21
LOCAL_IP="192.168.1.73"
MAX_COUNT=5000
#for pydbg script
IMAGE="C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
ARGS="test.html"
LOG_DIR="crashes"
#for taskill
IMAGE_NAME="firefox.exe"
#specific fuzz file gotten from queue
MUTATION_FILE="samples\\U-HellSoft.in"
#specific mutation type gotten from queue
#0=random
#1=string
MUTATION_TYPE=0