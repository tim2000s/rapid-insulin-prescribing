"""Print context around regex matches in a capture: ctx.py FILE PATTERN [WIDTH] [MAX]"""
import re,sys
t=open(sys.argv[1],errors='ignore').read(); w=int(sys.argv[3]) if len(sys.argv)>3 else 150; n=int(sys.argv[4]) if len(sys.argv)>4 else 20
for i,m in enumerate(re.finditer(sys.argv[2],t,re.I)):
    if i>=n: break
    print('>>',t[max(0,m.start()-w):m.end()+w].replace('\n',' | '))
