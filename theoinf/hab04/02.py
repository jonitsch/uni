def divtwo(dividend: int):
    divisor = 0
    if (dividend >= 0):
        while ((divisor + divisor) < (dividend - 1)):
            divisor = (divisor + 1)
        # Der gesuchte Divisor wird so lange um eins erhöht bis
        # seine Verdopplung größer gleich (Divident - 1) ist
    
    return divisor

def dya(n: int) -> list[int]:
    res: list[int] = []
    while (n > 0):
        div: int = divtwo(n)
        if (n - (div * 2) == 0):
            # n ist gerade
            n = div - 1
            res += [2]
        else:
            # n ist ungerade
            n = div
            res += [1]
    
    return res

    

def turing(n : int):
    # E (Alphabet) = {_,1,2,*}
    # Z = {z0, z1, z2, z3}
    z: int = 0
    
    b1: list[int] = dya(n) + [0]
    
    print(b1)
    b2: list[int] = [0]
    
    h1: int = 0
    h2: int = 0
    
    def walk(dir: str, array: list[int], index: int) -> int:
        if dir == 'R':
            index += 1
            if (index > len(array) - 1):
                array.append(0)
                
        if dir == 'L':
            index -= 0
            if (index < 0):
                index = 0
                array.insert(0, 0)
                
        return index
    
    while(z != 1):
        print('step')
        
        # (z0,1,_)->(z0,1,1,R,L)
        if (z == 0 and b1[h1] == 1 and b2[h2] == 0):
            b2[h2] = 1
            
            if (h1 + 1 > len(b1) - 1):
                b1 = b1 + [0] # Falls ein nach rechts laufen den Austritt aus dem Band bedeutet: Band vergrößern
            h1 += 1 # 1 Schritt nach rechts laufen
            
            if (h2 == 0):
                b2 = [0] + b2 # Falls h2 == 0, Band links um eins erweitern und Index beibehalten
            else:
                h2 -= 1 # 1 Schritt nach links laufen
                
        # (z0,2,_)->(z0,2,2,R,L)
        elif (z == 0 and b1[h1] == 2 and b2[h2] == 0):
            b2[h2] = 2
            
            h1 = walk('R', b1, h1)
            h2 = walk('L', b2, h2)
                
        # (z0,_,_) -> (z2,_,_,O,R)
        elif (z == 0 and b1[h1] == 0 and b2[h2] == 0):
            b1[h1] = 0
            b2[h2] = 0
            
            h1 = h1 # wir stoppen auf Band 1 
            h2 = walk('R', b2, h2)
            
            z = 2 # In Zustand 2 wechseln
            
        # (z2,_,1) -> (z2,1,_,R,R)
        elif (z == 2 and b1[h1] == 0 and b2[h2] == 1):
            b1[h1] = 1
            b2[h2] = 0
            
            h1 = walk('R', b1, h1)
            h2 = walk('R', b2, h2)

        # (z2,_,2)->(z3,2,_,R,R)
        elif (z == 2 and b1[h1] == 0 and b2[h2] == 2):
            b1[h1] = 2
            b2[h2] = 0
            
            h1 = walk('R', b1, h1)
            h2 = walk('R', b2, h2)
            
            z = 3
            
        # (z3,_,1)->(z3,1,_,R,R)
        elif (z == 3 and b1[h1] == 1 and b2[h2] == 0):
            b1[h1] = 1
            b2[h2] = 0
            
            h1 = walk('R', b1, h1)
            h2 = walk('R', b2, h2)
            
        else:
            z = 1
        
    res: list[int] = []
    i: int = 0
    
    while (i < len(b1) - 1):
        if (b1[i] != 0): 
            res.append(b1[i])
    
    w = 0
    
    print(res)
    
    return w

turing(121)