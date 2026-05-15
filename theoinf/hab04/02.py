# Gefordert: kommentiertes Python-Programm
# Sie können weitere Hilfsfunktionen verwenden!
# Namen:
#
#
#

########## HILFSFUNKTIONEN ##########

def divtwo(dividend: int) -> int:
    # Gibt das abgerundete Ergebnis von dividend / 2 zurück
    divisor = 0
    if (dividend >= 0):
        while ((divisor + divisor) < (dividend - 1)):
            divisor = (divisor + 1)
        # Der gesuchte Divisor wird so lange um eins erhöht bis
        # seine Verdopplung größer gleich (Divident - 1) ist
    
    return divisor

def DyadicRepresentation(x: int) -> list:
    # liefert eine Liste mit den dyadischen Ziffern von x
    # z.B. DyadicRepresentation(20) = [1, 2, 1, 2]
    res: list[int] = []
    while (x > 0):
        div: int = divtwo(x)
        if (x % 2 == 0):
            # n ist gerade
            # Rest = 0 in dyadischer Darstellung nicht zulässig, deswegen muss
            # mit div - 1 weitergerechnet werden und Rest 2 aufgeschrieben werden
            x = div - 1
            res += [2]
        else:
            # n ist ungerade, also wird mit div weitergerechnet und Rest 1 aufgeschrieben
            x = div
            res += [1]
    
    return res

def Number(l: list) -> int: # Parameterformat: list[int]
    i: int = len(l) - 1
    res: int = 0

    while(i >= 0):
        if (l[i] != 1 and l[i] != 2):
            return 0
        res += l[i] * 2**i
        i -= 1

    return res
	
########## HAUPTFUNKTION ########## (Namen und Signatur nicht ändern!)

# Hinweis:
# Zur verbesserten Lesbarkeit wurde das Schlüsselwort nonlocal und der Datentyp str verwendet, um die Funktionen
# b1Walk(dir: str) + b2Walk(dir: str) zu integrieren.
# Um die (erweiterten) WHILE-Bedingungen einzuhalten müsste b1Walk('R'), b1Walk('L'), ... lediglich durch den
# Inhalt der jeweiligen IF-Bedingung ersetzt werden.

def main(x: int) -> int:
    z = 0
    b1 = DyadicRepresentation(x) + [0]

    b2 = [0]
    h1 = h2 = 0

    def b1Walk(dir: str):
        nonlocal h1
        nonlocal b1
        if dir == 'R':
            h1 += 1 # 1 Schritt nach rechts laufen
            if (h1 > len(b1) - 1):
                b1 = b1 + [0] # Falls ein nach rechts laufen den Austritt aus dem Band bedeutet: Band vergrößern
        if dir == 'L':
            if (h1 == 0):
                b1 = [0] + b1 # Falls h2 == 0, Band links um eins erweitern und Index beibehalten
                return
            h1 -= 1 # 1 Schritt nach links laufen

    def b2Walk(dir: str):
        nonlocal h2
        nonlocal b2
        if dir == 'R':
            h2 += 1
            if (h2 > len(b2) - 1):
                b2 = b2 + [0]
        if dir == 'L':
            if (h2 == 0):
                b2 = [0] + b2
                return
            h2 -= 1
    
    while(z != 1):
        # ZUSTAND Z0

        # (z0,1,_) -> (z0,1,1,R,L)
        if (z == 0 and b1[h1] == 1 and b2[h2] == 0):
            b2[h2] = 1
            
            b1Walk('R')
            b2Walk('L')
                
        # (z0,2,_) -> (z0,2,2,R,L)
        elif (z == 0 and b1[h1] == 2 and b2[h2] == 0):
            b2[h2] = 2

            b1Walk('R')
            b2Walk('L')
                
        # (z0,_,_) -> (z2,_,_,O,R)
        elif (z == 0 and b1[h1] == 0 and b2[h2] == 0):
            h1 = h1 # wir stoppen auf Band 1
            b2Walk('R')
            
            z = 2 # In Zustand 2 wechseln

        # ZUSTAND Z2
    
        # (z2,_,1) -> (z2,1,_,R,R)
        elif (z == 2 and b1[h1] == 0 and b2[h2] == 1):
            b1[h1] = 1
            b2[h2] = 0

            b1Walk('R')
            b2Walk('R')

        # (z2,_,2) -> (z3,2,_,R,R)
        elif (z == 2 and b1[h1] == 0 and b2[h2] == 2):
            b1[h1] = 2
            b2[h2] = 0

            b1Walk('R')
            b2Walk('R')
            
            z = 3

        # ZUSTAND Z3

        # (z3,_,1) -> (z3,1,_,R,R)
        elif (z == 3 and b1[h1] == 0 and b2[h2] == 1):
            b1[h1] = 1
            b2[h2] = 0

            b1Walk('R')
            b2Walk('R')

        # (z3,_,2) -> (z3,_,_,R,R)
        elif (z == 3 and b1[h1] == 0 and b2[h2] == 2):
            b1[h1] = 2
            b2[h2] = 0

            b1Walk('R')
            b2Walk('R')
        
        else:
            z = 1
    
    res = []
    wordCount = 0
    
    for i in range(0,len(b1) - 1):
        if (b1[i] != 0):
            # Sobald wir die erste Ziffer != 0 gefunden haben, haben wir den Anfang des ersten Worts gefunden
            if (wordCount == 0): wordCount = 1
            res = res + [b1[i]]
        elif (b1[i] == 0 and wordCount == 1):
            # Wenn bereits ein Wort (Ziffernfolge != 0) gefunden wurde und die aktuelle Ziffer == 0
            # müssen alle folgenden Ziffern = 0 sein, ansonsten haben wir mehrere Wörter als Ausgabe
            # -> Ungültige Eingabe -> Schleife wird abgebrochen (break)
            for i in range(i, len(b1) - 1):
                if (b1[i] != 0):
                    res = [0]
                    break

    y = Number(res)

    return y
