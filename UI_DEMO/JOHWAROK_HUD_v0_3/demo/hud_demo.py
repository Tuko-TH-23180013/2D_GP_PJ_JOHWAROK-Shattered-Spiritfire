"""JOHWAROK transparent PNG HUD demo. Run: pip install pico2d; python demo/hud_demo.py
From package root, uses assets with fixed 1280 x 720 canvas. Controls: 1 HP down, 2 HP up,
Z dash consume, R recharge, SPACE weapon swap, B boss toggle, G stagger fill, ESC quit.
"""
from pico2d import open_canvas, close_canvas, clear_canvas, update_canvas, load_image, load_font, get_events, delay
from pico2d import SDL_QUIT, SDL_KEYDOWN, SDLK_ESCAPE, SDLK_1, SDLK_2, SDLK_z, SDLK_r, SDLK_SPACE, SDLK_b, SDLK_g
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WIDTH,HEIGHT=1280,720

class HUD:
    def __init__(self):
        self.assets={p.stem:load_image(str(p)) for p in (ROOT/'assets').glob('*.png')}
        self.font=load_font('ENCR10B.TTF',17)
        self.health=87;self.max_health=110;self.dash=2;self.weapon=0
        self.boss=False;self.boss_hp=.72;self.stagger=.44

    def draw_asset(self,name,x,y,w=None,h=None):
        im=self.assets[name]
        im.draw(x,y, w or im.w, h or im.h)

    def bar_fill(self,name,x,y,ratio,full_w,inner_left=8,inner_right=8,src_w=None):
        """Crop a 1-pixel-wide colored strip on a reusable transparent canvas.
        Using pico2d draw_rectangle is simpler; draw it BEFORE bar frame.
        """
        from pico2d import draw_rectangle
        # Intentionally outline-only placeholder, actual fill uses draw_rectangle differently.
        # Fill dynamically with solid 1x1 texture scaled via draw() below.
        pass

    def draw_meter(self,x,y,width,height,ratio,color):
        # Create colored 1x1 PNG on first use; pixel scale efficiently.
        name='meter_'+color
        if name not in self.assets:
            from pico2d import load_image
            self.assets[name]=load_image(str(ROOT/'assets'/('meter_'+color+'.png')))
        fill_w=max(0,int(width*max(0.,min(1.,ratio))))
        if fill_w:self.assets[name].draw(x+fill_w/2,y,fill_w,height)

    def draw(self):
        self.draw_asset('player_panel',257,72)
        self.draw_asset('portrait_dokkaebi',75,75)
        for idx,x in enumerate((166,241)):
            active=self.weapon==idx
            self.draw_asset('slot_active' if active else 'slot_inactive',x,87)
            self.draw_asset('weapon_basic' if idx==0 else 'weapon_heavy',x,87)
        self.draw_meter(139,36,307,12,self.health/self.max_health,'hp')
        self.draw_asset('health_frame',292,35)
        self.font.draw(362,29,f'{self.health} / {self.max_health}',(255,248,242))
        for i,x in enumerate((164,202)):
            self.draw_asset('dash_ready' if i<self.dash else 'dash_empty',x,18)
        self.draw_asset('ability_panel',631,69)
        for key,x,skill in [('A',587,'slash'),('S',667,'locked')]:
            self.draw_asset('slot_active' if key=='A' else 'slot_inactive',x,70,63,63)
            self.draw_asset('skill_'+skill,x,70,57,57)
            self.font.draw(x-6,111,key,(255,246,234))
        self.draw_asset('currency_panel',1162,67)
        self.draw_asset('currency_spirit',1102,89,34,34)
        self.draw_asset('currency_shard',1102,43,34,34)
        self.font.draw(1135,84,'105',(247,246,237))
        self.font.draw(1135,38,'7',(247,246,237))
        if self.boss:
            self.draw_asset('boss_panel',640,658)
            self.draw_meter(346,663,586,10,self.boss_hp,'boss')
            self.draw_asset('boss_health_frame',639,661)
            self.draw_meter(397,632,484,5,self.stagger,'stagger')
            self.draw_asset('boss_stagger_frame',639,632)
            self.font.draw(567,690,'CHEONGYEOM WONGWI',(255,226,198))


def main():
    open_canvas(WIDTH,HEIGHT)
    hud=HUD()
    running=True
    while running:
        for e in get_events():
            if e.type==SDL_QUIT:running=False
            if e.type==SDL_KEYDOWN:
                if e.key==SDLK_ESCAPE:running=False
                elif e.key==SDLK_1:hud.health=max(0,hud.health-10)
                elif e.key==SDLK_2:hud.health=min(hud.max_health,hud.health+10)
                elif e.key==SDLK_z:hud.dash=max(0,hud.dash-1)
                elif e.key==SDLK_r:hud.dash=min(2,hud.dash+1)
                elif e.key==SDLK_SPACE:hud.weapon=1-hud.weapon
                elif e.key==SDLK_b:hud.boss=not hud.boss
                elif e.key==SDLK_g:hud.stagger=min(1.,hud.stagger+.12)
        clear_canvas()
        hud.draw()
        update_canvas()
        delay(1/60)
    close_canvas()

if __name__=='__main__':main()
