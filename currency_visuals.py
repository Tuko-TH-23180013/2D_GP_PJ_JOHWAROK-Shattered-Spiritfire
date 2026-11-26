"""골드 동전과 옥석의 교체 가능한 임시 픽셀 아이콘."""
def draw_icon(kind, x, y, size=20):
    from pico2d import pico2d as p2d
    scale = size/20
    if kind == 'gold':
        for l,b,r,t,color in ((-6,-10,6,10,(160,100,24)),(-10,-6,10,6,(160,100,24)),
                              (-6,-8,6,8,(255,205,62)),(-8,-5,8,5,(255,205,62)),
                              (-2,-5,2,5,(255,244,170))):
            p2d.draw_rectangle(x+l*scale,y+b*scale,x+r*scale,y+t*scale,*color,filled=True)
    else:
        for row in range(-9,10):
            width = max(1,9-abs(row))
            color = (95,240,205) if row >= 0 else (32,145,148)
            p2d.draw_rectangle(x-width*scale,y+row*scale,x+width*scale,y+(row+1)*scale,*color,filled=True)
        p2d.draw_rectangle(x-2*scale,y,x+scale,y+6*scale,210,255,245,filled=True)
