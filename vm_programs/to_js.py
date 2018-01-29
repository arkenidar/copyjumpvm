fp=open('integer_sum.cj')
i=0
for line in fp:
    line=list(map(int, line.split(' ')[:4]))
    line[2]+=i
    line[3]+=i
    line=list(map(str, line))
    print('['+line[1]+', '+line[0]+', '+line[3]+', '+line[2]+'],')
    i+=1
